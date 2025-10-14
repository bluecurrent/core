"""The Blue Current integration."""

from __future__ import annotations

import asyncio
from contextlib import suppress
from typing import Any

from bluecurrent_api import Client
from bluecurrent_api.exceptions import (
    BlueCurrentException,
    InvalidApiToken,
    RequestLimitReached,
    WebsocketError,
)
import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_API_TOKEN, Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.dispatcher import async_dispatcher_send

from .actions import (
    clear_user_override,
    set_delayed_charging,
    set_price_based_charging,
    set_user_override,
)
from .const import (
    CURRENT,
    DEVICE_IDS,
    DOMAIN,
    EVSE_ID,
    LOGGER,
    OVERRIDE_END_DAYS,
    OVERRIDE_END_TIME,
    OVERRIDE_START_DAYS,
    OVERRIDE_START_TIME,
)

type BlueCurrentConfigEntry = ConfigEntry[Connector]

PLATFORMS = [Platform.BUTTON, Platform.SENSOR]
CHARGE_POINTS = "CHARGE_POINTS"
DATA = "data"
DELAY = 5

GRID = "GRID"
OBJECT = "object"
VALUE_TYPES = ["CH_STATUS"]

DAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]

SERVICE_SET_USER_OVERRIDE_SCHEMA = vol.Schema(
    {
        vol.Required(DEVICE_IDS): vol.All(cv.ensure_list, [cv.string]),
        vol.Required(CURRENT): cv.positive_int,
        vol.Required(OVERRIDE_START_TIME): cv.time_period,
        vol.Required(OVERRIDE_START_DAYS): cv.multi_select(DAYS),
        vol.Required(OVERRIDE_END_TIME): cv.time_period,
        vol.Required(OVERRIDE_END_DAYS): cv.multi_select(DAYS),
    }
)

SERVICE_CLEAR_USER_OVERRIDE_SCHEMA = vol.Schema(
    {
        vol.Required(DEVICE_IDS): vol.All(cv.ensure_list, [cv.string]),
    }
)

SERVICE_SET_PRICE_BASED_CHARGING_SCHEMA = vol.Schema(
    {
        vol.Required("device_id"): cv.string,
        vol.Required("expected_departure_time"): cv.time_period,
        vol.Required("expected_charging_session_size"): vol.Range(1, 80),
        vol.Required("immediately_charge"): vol.Range(1, 80),
    }
)

SERVICE_DELAYED_CHARGING_SCHEMA = vol.Schema(
    {
        vol.Required("device_id"): cv.string,
        vol.Required("days"): cv.multi_select(DAYS),
        vol.Required("end_time"): cv.time_period,
        vol.Required("start_time"): cv.time_period,
    }
)


async def async_setup_entry(
    hass: HomeAssistant, config_entry: BlueCurrentConfigEntry
) -> bool:
    """Set up Blue Current as a config entry."""
    client = Client()
    api_token = config_entry.data[CONF_API_TOKEN]
    connector = Connector(hass, config_entry, client)

    try:
        await client.validate_api_token(api_token)
    except InvalidApiToken as err:
        raise ConfigEntryAuthFailed("Invalid API token.") from err
    except BlueCurrentException as err:
        raise ConfigEntryNotReady from err
    config_entry.async_create_background_task(
        hass, connector.run_task(), "blue_current-websocket"
    )

    await client.wait_for_charge_points()
    await client.get_user_override_currents_list()

    config_entry.runtime_data = connector
    await hass.config_entries.async_forward_entry_setups(config_entry, PLATFORMS)

    async def set_price_based_charging_call(service_call: ServiceCall) -> None:
        """Set smart charging profile."""
        await set_price_based_charging(
            hass, client, connector.charge_points, service_call
        )

    async def set_delayed_charging_call(service_call: ServiceCall) -> None:
        """Set price based charging."""
        await set_delayed_charging(hass, client, connector.charge_points, service_call)

    async def set_user_override_call(service_call: ServiceCall) -> None:
        """Set user override."""
        await set_user_override(hass, client, connector.schedules, service_call)

    async def clear_user_override_call(service_call: ServiceCall) -> None:
        """Clear user override."""
        await clear_user_override(hass, client, connector.schedules, service_call)

    hass.services.async_register(
        DOMAIN,
        "set_delayed_charging",
        set_delayed_charging_call,
        SERVICE_DELAYED_CHARGING_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        "set_price_based_charging",
        set_price_based_charging_call,
        SERVICE_SET_PRICE_BASED_CHARGING_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        "set_user_override",
        set_user_override_call,
        SERVICE_SET_USER_OVERRIDE_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        "clear_user_override",
        clear_user_override_call,
        SERVICE_CLEAR_USER_OVERRIDE_SCHEMA,
    )

    return True


async def async_unload_entry(
    hass: HomeAssistant, config_entry: BlueCurrentConfigEntry
) -> bool:
    """Unload the Blue Current config entry."""

    return await hass.config_entries.async_unload_platforms(config_entry, PLATFORMS)


class Connector:
    """Define a class that connects to the Blue Current websocket API."""

    def __init__(
        self, hass: HomeAssistant, config: BlueCurrentConfigEntry, client: Client
    ) -> None:
        """Initialize."""
        self.config = config
        self.hass = hass
        self.client = client
        self.schedules: dict[str, dict] = {}
        self.charge_points: dict[str, dict] = {}
        self.grid: dict[str, Any] = {}

    async def on_data(self, message: dict) -> None:
        """Handle received data."""

        object_name: str = message[OBJECT]

        # gets charge point ids
        if object_name == CHARGE_POINTS:
            charge_points_data: list = message[DATA]
            await self.handle_charge_point_data(charge_points_data)

        # gets charge point key / values
        elif object_name in VALUE_TYPES:
            value_data: dict = message[DATA]
            evse_id = value_data.pop(EVSE_ID)
            self.update_charge_point(evse_id, value_data)

        # gets grid key / values
        elif GRID in object_name:
            data: dict = message[DATA]
            self.grid = data
            self.dispatch_grid_update_signal()

        elif "LIST_OVERRIDE_CURRENT" in object_name:
            self.update_override_schedules(message[DATA])

        elif object_name in ("POST_EDIT_OVERRIDE_CURRENT", "POST_SET_OVERRIDE_CURRENT"):
            self.update_schedule(message[DATA])

    async def handle_charge_point_data(self, charge_points_data: list) -> None:
        """Handle incoming chargepoint data."""
        await asyncio.gather(
            *(
                self.handle_charge_point(entry[EVSE_ID], entry)
                for entry in charge_points_data
            ),
            self.client.get_grid_status(charge_points_data[0][EVSE_ID]),
        )

    async def handle_charge_point(
        self, evse_id: str, charge_point: dict[str, Any]
    ) -> None:
        """Add the chargepoint and request their data."""
        self.add_charge_point(evse_id, charge_point)
        await self.client.get_status(evse_id)

    def add_charge_point(self, evse_id: str, charge_point: dict[str, Any]) -> None:
        """Add a charge point to charge_points."""
        self.charge_points[evse_id] = charge_point

    def update_charge_point(self, evse_id: str, data: dict) -> None:
        """Update the charge point data."""
        self.charge_points[evse_id].update(data)
        self.dispatch_charge_point_update_signal(evse_id)

    def update_override_schedules(self, schedules: list[dict]) -> None:
        """Update the registered override schedules."""
        for schedule in schedules:
            self.update_schedule(schedule)

    def update_schedule(self, schedule: dict) -> None:
        """Add or register an existing schedule."""
        self.schedules[schedule["schedule_id"]] = schedule

    def dispatch_charge_point_update_signal(self, evse_id: str) -> None:
        """Dispatch a charge point update signal."""
        async_dispatcher_send(self.hass, f"{DOMAIN}_charge_point_update_{evse_id}")

    def dispatch_grid_update_signal(self) -> None:
        """Dispatch a grid update signal."""
        async_dispatcher_send(self.hass, f"{DOMAIN}_grid_update")

    async def on_open(self) -> None:
        """Fetch data when connection is established."""
        await self.client.get_charge_points()

    async def run_task(self) -> None:
        """Start the receive loop."""
        try:
            while True:
                try:
                    await self.client.connect(self.on_data, self.on_open)
                except RequestLimitReached:
                    LOGGER.warning(
                        "Request limit reached. reconnecting at 00:00 (Europe/Amsterdam)"
                    )
                    delay = self.client.get_next_reset_delta().seconds
                except WebsocketError:
                    LOGGER.debug("Disconnected, retrying in background")
                    delay = DELAY

                self._on_disconnect()
                await asyncio.sleep(delay)
        finally:
            await self._disconnect()

    def _on_disconnect(self) -> None:
        """Dispatch signals to update entity states."""
        for evse_id in self.charge_points:
            self.dispatch_charge_point_update_signal(evse_id)
        self.dispatch_grid_update_signal()

    async def _disconnect(self) -> None:
        """Disconnect from the websocket."""
        with suppress(WebsocketError):
            await self.client.disconnect()
            self._on_disconnect()

    @property
    def connected(self) -> bool:
        """Returns the connection status."""
        return self.client.is_connected()
