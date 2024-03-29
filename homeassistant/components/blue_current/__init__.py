"""The Blue Current integration."""

from __future__ import annotations

import asyncio
from contextlib import suppress

from bluecurrent_api import Client
from bluecurrent_api.exceptions import (
    BlueCurrentException,
    InvalidApiToken,
    RequestLimitReached,
    WebsocketError,
)

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_NAME, CONF_API_TOKEN, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady

from .const import DOMAIN, EVSE_ID, LOGGER, MODEL_TYPE
from .coordinator import ChargePointCoordinator, GridCoordinator

PLATFORMS = [Platform.BUTTON, Platform.SENSOR]
CHARGE_POINTS = "CHARGE_POINTS"
DATA = "data"
DELAY = 5

GRID = "GRID"
OBJECT = "object"
VALUE_TYPES = ["CH_STATUS"]


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Set up Blue Current as a config entry."""
    hass.data.setdefault(DOMAIN, {})
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
    hass.data[DOMAIN][config_entry.entry_id] = connector
    await hass.config_entries.async_forward_entry_setups(config_entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Unload the Blue Current config entry."""

    unload_ok = await hass.config_entries.async_unload_platforms(
        config_entry, PLATFORMS
    )
    if unload_ok:
        hass.data[DOMAIN].pop(config_entry.entry_id)

    return unload_ok


class Connector:
    """Define a class that connects to the Blue Current websocket API."""

    def __init__(
        self, hass: HomeAssistant, config: ConfigEntry, client: Client
    ) -> None:
        """Initialize."""
        self.config = config
        self.hass = hass
        self.client = client
        self.charge_point_coordinators: dict[str, ChargePointCoordinator] = {}
        self.grid_coordinator = GridCoordinator(hass, client)

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
            self.grid_coordinator.async_set_updated_data(data)

    async def handle_charge_point_data(self, charge_points_data: list) -> None:
        """Handle incoming chargepoint data."""
        await asyncio.gather(
            *(
                self.handle_charge_point(
                    entry[EVSE_ID], entry[MODEL_TYPE], entry[ATTR_NAME]
                )
                for entry in charge_points_data
            ),
            self.client.get_grid_status(charge_points_data[0][EVSE_ID]),
        )

    async def handle_charge_point(self, evse_id: str, model: str, name: str) -> None:
        """Add the chargepoint and request their data."""
        self.add_charge_point(evse_id, model, name)
        await self.client.get_status(evse_id)

    def add_charge_point(self, evse_id: str, model: str, name: str) -> None:
        """Add a charge point to charge_points."""
        if evse_id not in self.charge_point_coordinators:
            self.charge_point_coordinators[evse_id] = ChargePointCoordinator(
                self.hass, self.client, evse_id, name, model
            )

    def update_charge_point(self, evse_id: str, data: dict) -> None:
        """Update the charge point data."""
        self.charge_point_coordinators[evse_id].async_set_updated_data(data)

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
        for coordinator in self.charge_point_coordinators.values():
            coordinator.async_update_listeners()
        self.grid_coordinator.async_update_listeners()

    async def _disconnect(self) -> None:
        """Disconnect from the websocket."""
        with suppress(WebsocketError):
            await self.client.disconnect()
            self._on_disconnect()
