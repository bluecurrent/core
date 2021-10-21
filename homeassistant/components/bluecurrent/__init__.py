"""The BlueCurrent integration."""
from __future__ import annotations

import asyncio

from bluecurrent_api import Client
from bluecurrent_api.errors import WebsocketError

from homeassistant.components import persistent_notification
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EVENT_HOMEASSISTANT_STOP
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.dispatcher import (
    async_dispatcher_connect,
    async_dispatcher_send,
)
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.event import async_call_later

from .const import DELAY, DOMAIN, LOGGER, PLATFORMS, URL


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
    hass.config_entries.async_setup_platforms(config_entry, PLATFORMS)

    async def _async_disconnect_websocket(_: Event) -> None:
        await client.disconnect()

    config_entry.async_on_unload(
        hass.bus.async_listen_once(
            EVENT_HOMEASSISTANT_STOP, _async_disconnect_websocket
        )
    )

    return True


async def async_unload_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Unload an BlueCurrent config entry."""
    connector = hass.data[DOMAIN].pop(config_entry.entry_id)
    hass.async_create_task(connector.disconnect())

    return await hass.config_entries.async_unload_platforms(config_entry, PLATFORMS)


def set_entities_unavalible(hass: HomeAssistant, config_id):
    """Set all Blue Current entities to unavailable."""
    entity_registry = er.async_get(hass)
    entries = er.async_entries_for_config_entry(entity_registry, config_id)

    for entry in entries:
        entry.write_unavailable_state(hass)


class Connector:
    """Define a class that connects to the Blue Current websocket API."""

    def __init__(
        self, hass: HomeAssistant, config: ConfigEntry, client: Client
    ) -> None:
        """Initialize."""
        self._config = config
        self._hass = hass
        self.client = client
        self.charge_points: dict[str, dict] = {}

    async def connect(self, token: str) -> None:
        """Register on_data and connect to the websocket."""

        def on_data(data: dict) -> None:
            """Define a handler to handle received data."""
            command = data["object"]
            data = data["data"]

            if command == "CHARGE_POINTS":
                for evse_id in data.keys():
                    self.charge_points[evse_id] = data[evse_id]
                    async_dispatcher_send(
                        self._hass, f"bluecurrent_data_update_{evse_id}"
                    )

            elif command == "STATUS":
                evse_id = data["evse_id"]
                if data != self.charge_points[evse_id]:
                    LOGGER.debug("New data received: %s", data)
                    self.charge_points[evse_id] = data
                    async_dispatcher_send(
                        self._hass, f"bluecurrent_data_update_{evse_id}"
                    )

        self.client.set_on_data(on_data)
        await self.client.websocket.connect(token, URL)
        await self.client.get_charge_points()

    async def start_loop(self) -> None:
        """Start the receive loop."""
        try:
            await self.client.start_loop()
        except WebsocketError:
            LOGGER.warning(
                "Disconnected from the Blue Current websocket. Trying to connect in 30 seconds"
            )

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
            await self.connect("123")
            LOGGER.info("Reconnected to the Blue Current websocket")
            await self.start_loop()
        except WebsocketError:
            LOGGER.warning("Reconnect to the Blue Current websocket failed")
            async_call_later(self._hass, DELAY * 10, self.reconnect)

    async def disconnect(self) -> None:
        """Disconnect from the websocket."""
        await self.client.disconnect()


class ChargePointEntity(Entity):
    """Define a base charge point entity."""

    def __init__(
        self,
        connector: Connector,
        name: str,
        evse_id: str,
    ) -> None:
        """Initialize the sensor."""
        self._evse_id = evse_id
        self._connector = connector
        self._attr_unique_id = f"{evse_id}_{name}"
        self._attr_name = name

    async def async_added_to_hass(self) -> None:
        """Register callbacks."""

        @callback
        def update() -> None:
            """Update the state."""

            if not self._attr_available:
                self._attr_available = True

            self.update_from_latest_data()
            self.async_write_ha_state()

        # no idea how the dispatcher gets called but many other integrations use it like this
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass, f"bluecurrent_data_update_{self._evse_id}", update
            )
        )

        self.update_from_latest_data()

    @callback
    def update_from_latest_data(self) -> None:
        """Update the entity from the latest data."""
        raise NotImplementedError
