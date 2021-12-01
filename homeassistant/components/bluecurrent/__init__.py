"""The BlueCurrent integration."""
from __future__ import annotations

import asyncio
from typing import Any

from bluecurrent_api import Client
from bluecurrent_api.errors import WebsocketError
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.components import persistent_notification
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_TOKEN, EVENT_HOMEASSISTANT_STOP
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import entity_registry
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.dispatcher import (
    async_dispatcher_connect,
    async_dispatcher_send,
)
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.event import async_call_later
from homeassistant.helpers.typing import ConfigType

from .const import CARD, DATA, DELAY, DOMAIN, EVSE_ID, LOGGER, PLATFORMS, URL

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_TOKEN): cv.string,
                vol.Required(CARD): cv.string,
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the Netatmo component."""
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
    token = config_entry.data["token"]
    connector = Connector(hass, config_entry, client)

    try:
        await connector.connect(token)
    except WebsocketError as err:
        LOGGER.error("Config entry failed: %s", err)
        raise ConfigEntryNotReady from err

    hass.loop.create_task(connector.start_loop())
    hass.data[DOMAIN][config_entry.entry_id] = connector

    await asyncio.sleep(1)
    print("OK")
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

    return True


async def async_unload_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Unload an BlueCurrent config entry."""
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

    async def get_charge_point_data(self, evse_id: str) -> None:
        """Get all the data of the charge point."""
        await self.client.get_status(evse_id)

    async def connect(self, token: str) -> None:
        """Register on_data and connect to the websocket."""

        def update_charge_point(evse_id: str, data: dict) -> None:
            if evse_id not in self.charge_points:
                self.charge_points[evse_id] = data
            else:
                for key in data:
                    self.charge_points[evse_id][key] = data[key]

        async def on_data(message: dict) -> None:
            """Define a handler to handle received data."""
            command = message["object"]
            data = message[DATA]

            async def handle_charge_point(evse_id: str, entry: dict) -> None:
                data = {"model_type": entry["model_type"]}
                update_charge_point(evse_id, data)
                await self.get_charge_point_data(evse_id)

            def handle_status(evse_id: str, data: dict) -> None:
                update_charge_point(evse_id, data)
                async_dispatcher_send(
                    self._hass, f"bluecurrent_status_update_{evse_id}"
                )

            def handle_grid(evse_id: str, data: dict) -> None:
                update_charge_point(evse_id, data)
                async_dispatcher_send(self._hass, "bluecurrent_grid_update")

            if command == "CHARGE_POINTS":
                for entry in data:
                    evse_id = entry[EVSE_ID]
                    await handle_charge_point(evse_id, entry)
                await self.client.get_grid_status(data[1][EVSE_ID])

            elif command == "STATUS":
                evse_id = data[EVSE_ID]
                handle_status(evse_id, data)

            elif command == "GRID":
                print("grid")
                evse_id = data[EVSE_ID]
                handle_grid(evse_id, data)

            else:
                print(message)

        self.client.set_on_data(on_data)
        await self.client.connect(token, URL)
        await self.client.get_charge_points()

    async def start_loop(self) -> None:
        """Start the receive loop."""
        try:
            await self.client.start_loop()
        except WebsocketError:
            LOGGER.warning(
                "Disconnected from the Blue Current websocket. Trying to connect in 30 seconds"
            )

            # May have to be removed.
            persistent_notification.create(
                self._hass,
                "Connection to the Blue Current websocket has been lost. <br> trying to reconnect in 30 seconds",
                title=DOMAIN,
                notification_id="bluecurrent_notification",
            )

            set_entities_unavalible(self._hass, self._config.entry_id)

            async_call_later(self._hass, DELAY, self.reconnect)

    async def reconnect(self, timestamp: int | None = None) -> None:
        """Keep trying to reconnect to the websocket."""
        try:
            await self.connect(self._config.data["token"])
            LOGGER.info("Reconnected to the Blue Current websocket")
            await self.start_loop()
            await self.client.get_charge_points()
        except WebsocketError:
            LOGGER.warning(
                "Reconnect to the Blue Current websocket failed. Trying again in 5 minutes"
            )
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
        """Initialize the sensor."""
        self.entity_type = entity_type
        self._evse_id: str = evse_id
        self._connector: Connector = connector
        self._attr_name: str = name

        self._attr_device_info = {
            "identifiers": {(DOMAIN, evse_id)},
            "name": "NanoCharge " + evse_id,
            "manufacturer": "BlueCurrent",
            "model": connector.charge_points[evse_id]["model_type"],
        }

    async def async_added_to_hass(self) -> None:
        """Register callbacks."""

        @callback
        def update() -> None:
            """Update the state."""
            self.update_from_latest_data()
            self.async_write_ha_state()

        signal = f"bluecurrent_status_update_{self._evse_id}"
        self.async_on_remove(async_dispatcher_connect(self.hass, signal, update))

        self.update_from_latest_data()

    @callback
    def update_from_latest_data(self) -> None:
        """Update the entity from the latest data."""
        raise NotImplementedError
