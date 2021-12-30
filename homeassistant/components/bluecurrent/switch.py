"""Support for Blue Current switches."""
from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_ICON, CONF_NAME
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import BlueCurrentEntity, Connector
from .const import DOMAIN, FUNCTION, KEY, LOGGER, SWITCHES


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Blue Current switches."""
    connector: Connector = hass.data[DOMAIN][entry.entry_id]

    switch_list = []
    for evse_id in connector.charge_points.keys():
        for switch in SWITCHES:
            switch_list.append(
                ChargePointSwitch(
                    connector,
                    evse_id,
                    switch,
                )
            )

    async_add_entities(switch_list)


class ChargePointSwitch(BlueCurrentEntity, SwitchEntity):
    """Base charge point switch."""

    _attr_should_poll = False

    def __init__(
        self, connector: Connector, evse_id: str, switch: dict[str, Any]
    ) -> None:
        """Initialize the switch."""
        super().__init__(connector, "switch", switch[CONF_NAME], evse_id)

        self._attr_icon = switch[CONF_ICON]
        self._function = switch[FUNCTION]
        self._key = switch[KEY]
        self._attr_unique_id = f"{switch[KEY]}_{evse_id}"
        self.entity_id = f"switch.{switch[KEY]}_{evse_id}"

    async def call_function(self, value: bool) -> None:
        """Call the function to set setting."""
        try:
            await self._function(self._connector.client, self._evse_id, value)
        except ConnectionError:
            LOGGER.error("No connection")

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the entity on."""
        await self.call_function(True)
        self._attr_is_on = True

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the entity on."""
        await self.call_function(False)
        self._attr_is_on = False

    @callback
    def update_from_latest_data(self) -> None:
        """Fetch new state data for the switch."""
        new_value = self._connector.charge_points[self._evse_id].get(self._key)
        if new_value is not None:
            self._attr_available = True
            self._attr_is_on = new_value
        else:
            self._attr_available = False
