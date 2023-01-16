"""Support for Blue Current switches."""
from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

from bluecurrent_api import Client

from homeassistant.components.switch import (
    SwitchDeviceClass,
    SwitchEntity,
    SwitchEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import BlueCurrentEntity, Connector
from .const import DOMAIN, LOGGER


@dataclass
class BlueCurrentSwitchEntityDescriptionMixin:
    """Mixin for the called functions."""

    function: Callable[[Client, str, bool], Awaitable]


@dataclass
class BlueCurrentSwitchEntityDescription(
    SwitchEntityDescription, BlueCurrentSwitchEntityDescriptionMixin
):
    """Describes Blue Current switch entity."""


SWITCHES = (
    BlueCurrentSwitchEntityDescription(
        key="plug_and_charge",
        device_class=SwitchDeviceClass.SWITCH,
        name="Plug and charge",
        icon="mdi:ev-plug-type2",
        function=Client.set_plug_and_charge,
        has_entity_name=True,
    ),
    BlueCurrentSwitchEntityDescription(
        key="public_charging",
        device_class=SwitchDeviceClass.SWITCH,
        name="Public charging",
        icon="mdi:account-group",
        function=Client.set_public_charging,
        has_entity_name=True,
    ),
    BlueCurrentSwitchEntityDescription(
        key="available",
        device_class=SwitchDeviceClass.SWITCH,
        name="Available",
        icon="mdi:power",
        function=Client.set_operative,
        has_entity_name=True,
    ),
)


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

    entity_description: BlueCurrentSwitchEntityDescription

    def __init__(
        self,
        connector: Connector,
        evse_id: str,
        switch: BlueCurrentSwitchEntityDescription,
    ) -> None:
        """Initialize the switch."""
        super().__init__(connector, evse_id)

        self.key = switch.key
        self.entity_description = switch
        self._attr_unique_id = f"{switch.key}_{evse_id}"

    async def call_function(self, value: bool) -> None:
        """Call the function to set setting."""
        try:
            await self.entity_description.function(
                self.connector.client, self.evse_id, value
            )
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
        new_value = self.connector.charge_points[self.evse_id].get(self.key)
        if new_value is not None:
            self._attr_available = True
            self._attr_is_on = new_value
        else:
            self._attr_available = False
