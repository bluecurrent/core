"""The BlueCurrent integration."""
from __future__ import annotations

import asyncio
from typing import Any

from bluecurrent_api import Client
from bluecurrent_api.errors import InvalidToken, WebsocketError
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_API_TOKEN, EVENT_HOMEASSISTANT_STOP
from homeassistant.core import Event, HomeAssistant, ServiceCall, callback
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import entity_registry
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.dispatcher import (
    async_dispatcher_connect,
    async_dispatcher_send,
)
from homeassistant.helpers.entity import DeviceInfo, Entity
from homeassistant.helpers.event import async_call_later
from homeassistant.helpers.typing import ConfigType

from .const import (
    ACTIVITY,
    AVAILABLE,
    CARD,
    CHARGE_POINTS,
    DATA,
    DELAY,
    DOMAIN,
    ERROR,
    EVSE_ID,
    GRID_STATUS,
    LOGGER,
    MODEL_TYPE,
    OBJECT,
    PLATFORMS,
    RESULT,
    SERVICES,
    SETTINGS,
    SUCCESS,
    UNAVAILABLE,
    VALUE_TYPES,
)

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_API_TOKEN): cv.string,
                vol.Required(CARD): cv.string,
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the BlueCurrent component."""
    conf = config.get(DOMAIN)
    if conf is not None:
        hass.async_create_task(
            hass.config_entries.flow.async_init(
                DOMAIN, context={"source": config_entries.SOURCE_IMPORT}, data=conf
            )
        )

    return True


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Set up Blue Current as a config entry."""
    hass.data.setdefault(DOMAIN, {})
    client = Client()
    api_token = config_entry.data[CONF_API_TOKEN]
    connector = Connector(hass, config_entry, client)
    try:
        await connector.connect(api_token)
    except (WebsocketError, InvalidToken) as err:
        LOGGER.error("Config entry failed: %s", err)
        raise ConfigEntryNotReady from err

    hass.loop.create_task(connector.start_loop())
    hass.data[DOMAIN][config_entry.entry_id] = connector

    await asyncio.sleep(1)
    hass.config_entries.async_setup_platforms(config_entry, PLATFORMS)

    async def _async_disconnect_websocket(_: Event) -> None:
        try:
            await client.disconnect()
        except WebsocketError:
            pass

    config_entry.async_on_unload(
        hass.bus.async_listen_once(
            EVENT_HOMEASSISTANT_STOP, _async_disconnect_websocket
        )
    )

    async def handle_get_status(call: ServiceCall) -> None:
        evse_id = call.data.get(EVSE_ID)
        await client.get_status(evse_id)

    async def handle_reset(call: ServiceCall) -> None:
        evse_id = call.data.get(EVSE_ID)
        await client.reset(evse_id)

    async def handle_reboot(call: ServiceCall) -> None:
        evse_id = call.data.get(EVSE_ID)
        await client.reboot(evse_id)

    async def handle_start_session(call: ServiceCall) -> None:
        evse_id = call.data.get(EVSE_ID)
        await client.start_session(evse_id, config_entry.data[CARD])

    async def handle_stop_session(call: ServiceCall) -> None:
        evse_id = call.data.get(EVSE_ID)
        await client.stop_session(evse_id)

    hass.services.async_register(DOMAIN, "get_status", handle_get_status)
    hass.services.async_register(DOMAIN, "reset", handle_reset)
    hass.services.async_register(DOMAIN, "reboot", handle_reboot)
    hass.services.async_register(DOMAIN, "start_session", handle_start_session)
    hass.services.async_register(DOMAIN, "stop_session", handle_stop_session)

    return True


async def async_unload_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Unload the BlueCurrent config entry."""
    connector: Connector = hass.data[DOMAIN].pop(config_entry.entry_id)
    hass.async_create_task(connector.disconnect())

    return await hass.config_entries.async_unload_platforms(config_entry, PLATFORMS)


def set_entities_unavalible(hass: HomeAssistant, config_id: str) -> None:
    """Set all Blue Current entities to unavailable."""
    registry = entity_registry.async_get(hass)
    entries = entity_registry.async_entries_for_config_entry(registry, config_id)

    for entry in entries:
        entry.write_unavailable_state(hass)


class Connector:
    """Define a class that connects to the Blue Current websocket API."""

    charge_points: dict[str, dict] = {}
    grid: dict[str, Any] = {}

    def __init__(
        self, hass: HomeAssistant, config: ConfigEntry, client: Client
    ) -> None:
        """Initialize."""
        self._config: ConfigEntry = config
        self._hass: HomeAssistant = hass
        self.client: Client = client

    async def connect(self, api_token: str) -> None:
        """Register on_data and connect to the websocket."""
        self.client.set_receiver(self.on_data)
        await self.client.connect(api_token)
        await self.client.get_charge_points()

    async def on_data(self, message: dict) -> None:
        """Define a handler to handle received data."""

        async def handle_charge_points(data: list) -> None:
            """Loop over the charge points and get their data."""
            for entry in data:
                evse_id = entry[EVSE_ID]
                model = entry[MODEL_TYPE]
                self.add_charge_point(evse_id, model)
                await self.get_charge_point_data(evse_id)
            await self.client.get_grid_status(data[0][EVSE_ID])

        object_name: str = message[OBJECT]

        print(object_name)

        if ERROR in message:
            LOGGER.debug("Received an error: %s for %s", message[ERROR], object_name)
            return

        if DATA in message:
            data: dict | list = message[DATA]

        # gets charge point ids
        if object_name == CHARGE_POINTS:
            assert isinstance(data, list)
            await handle_charge_points(data)

        # gets charge point key / values
        elif object_name in VALUE_TYPES:
            assert isinstance(data, dict)
            evse_id = data.pop(EVSE_ID)
            self.update_charge_point(evse_id, data)

        # gets grid key / values
        elif object_name == GRID_STATUS:
            assert isinstance(data, dict)
            self.grid = data
            self.dispatch_signal()

        # setting change responses
        elif object_name in SETTINGS:
            evse_id = message.pop(EVSE_ID)
            key = object_name.lower()
            result = message[RESULT]
            new_data = {key: result}
            self.update_charge_point(evse_id, new_data)

        # service responses
        elif object_name in SERVICES:
            success: bool = message[SUCCESS]
            self.handle_success(success, object_name)

    async def get_charge_point_data(self, evse_id: str) -> None:
        """Get all the data of the charge point."""
        await self.client.get_status(evse_id)
        await self.client.get_settings(evse_id)

    def add_charge_point(self, evse_id: str, model: str) -> None:
        """Add a charge point to the dictionary."""
        self.charge_points[evse_id] = {MODEL_TYPE: model}

    def update_charge_point(self, evse_id: str, data: dict) -> None:
        """Update the charge point data."""

        def handle_activity(data: dict) -> None:
            activity = data.get(ACTIVITY)
            if activity == AVAILABLE:
                data[AVAILABLE] = True
            else:
                data[AVAILABLE] = False

        def handle_available(data: dict) -> None:
            available = data.get(AVAILABLE)
            if available:
                data[ACTIVITY] = AVAILABLE

            else:
                data[ACTIVITY] = UNAVAILABLE

        if AVAILABLE in data:
            handle_available(data)
        elif ACTIVITY in data:
            handle_activity(data)
        for key in data:
            self.charge_points[evse_id][key] = data[key]
        self.dispatch_signal(evse_id)

    def handle_success(self, success: bool, object_name: str) -> None:
        """Log a message based on success."""
        if success:
            LOGGER.debug(object_name, "success")
        else:
            LOGGER.warning(object_name, "unsuccessful")

    def dispatch_signal(self, evse_id: str | None = None) -> None:
        """Dispatch a signal."""
        if evse_id is not None:
            async_dispatcher_send(self._hass, f"bluecurrent_value_update_{evse_id}")
        else:
            async_dispatcher_send(self._hass, "bluecurrent_grid_update")

    async def start_loop(self) -> None:
        """Start the receive loop."""
        try:
            await self.client.start_loop()
        except WebsocketError:
            LOGGER.warning(
                "Disconnected from the Blue Current websocket. Retrying to connect in background"
            )

            set_entities_unavalible(self._hass, self._config.entry_id)

            async_call_later(self._hass, DELAY, self.reconnect)

    async def reconnect(self, timestamp: int | None = None) -> None:
        """Keep trying to reconnect to the websocket."""
        try:
            await self.connect(self._config.data[CONF_API_TOKEN])
            LOGGER.warning("Reconnected to the Blue Current websocket")
            await self.start_loop()
            await self.client.get_charge_points()
        except WebsocketError:
            async_call_later(self._hass, DELAY * 10, self.reconnect)

    async def disconnect(self) -> None:
        """Disconnect from the websocket."""
        try:
            await self.client.disconnect()
        except WebsocketError:
            pass


class BlueCurrentEntity(Entity):
    """Define a base charge point entity."""

    def __init__(
        self,
        connector: Connector,
        entity_type: str,
        name: str,
        evse_id: str,
    ) -> None:
        """Initialize the entity."""
        self.entity_type = entity_type
        self._evse_id: str = evse_id
        self._connector: Connector = connector
        self._attr_name: str = name

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, evse_id)},
            name=f"{connector.charge_points[evse_id][MODEL_TYPE]} {evse_id}",
            manufacturer="BlueCurrent",
            model=connector.charge_points[evse_id][MODEL_TYPE],
        )

    async def async_added_to_hass(self) -> None:
        """Register callbacks."""

        @callback
        def update() -> None:
            """Update the state."""
            self.update_from_latest_data()
            self.async_write_ha_state()

        self.async_on_remove(
            async_dispatcher_connect(
                self.hass, f"bluecurrent_value_update_{self._evse_id}", update
            )
        )

        self.update_from_latest_data()

    @callback
    def update_from_latest_data(self) -> None:
        """Update the entity from the latest data."""
        raise NotImplementedError
