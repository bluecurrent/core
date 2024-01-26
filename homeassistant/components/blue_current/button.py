"""Support for Blue Current buttons."""
from __future__ import annotations

from collections.abc import Callable, Coroutine
from dataclasses import dataclass
from typing import Any

from bluecurrent_api import Client

from homeassistant.components.button import (
    ButtonDeviceClass,
    ButtonEntity,
    ButtonEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import Connector
from .const import DOMAIN
from .entity import BaseEntity, ChargepointEntity


@dataclass(frozen=True)
class BlueCurrentButtonEntityDescriptionMixin:
    """Mixin for the called functions."""

    function: Callable[[Client, str], Coroutine[Any, Any, None]]


@dataclass(frozen=True)
class BlueCurrentButtonEntityDescription(
    ButtonEntityDescription, BlueCurrentButtonEntityDescriptionMixin
):
    """Describes a Blue Current button entity."""


CHARGE_POINT_BUTTONS = (
    BlueCurrentButtonEntityDescription(
        key="reset",
        translation_key="reset",
        icon="mdi:restart",
        function=lambda client, evse_id: client.reset(evse_id),
        device_class=ButtonDeviceClass.RESTART,
    ),
    BlueCurrentButtonEntityDescription(
        key="reboot",
        translation_key="reboot",
        icon="mdi:restart-alert",
        function=lambda client, evse_id: client.reboot(evse_id),
        device_class=ButtonDeviceClass.RESTART,
    ),
    BlueCurrentButtonEntityDescription(
        key="stop_charge_session",
        translation_key="stop_charge_session",
        icon="mdi:stop",
        function=lambda client, evse_id: client.start_session(evse_id),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Blue Current buttons."""
    connector: Connector = hass.data[DOMAIN][entry.entry_id]
    button_list: list[ButtonEntity] = [RefreshChargeCardsButton(connector)]
    for evse_id in connector.charge_points:
        for button in CHARGE_POINT_BUTTONS:
            button_list.append(
                ChargePointButton(
                    connector,
                    button,
                    evse_id,
                )
            )

    async_add_entities(button_list)


class ChargePointButton(ChargepointEntity, ButtonEntity):
    """Define a charge point button."""

    def __init__(
        self,
        connector: Connector,
        button: BlueCurrentButtonEntityDescription,
        evse_id: str,
    ) -> None:
        """Initialize the button."""
        super().__init__(connector, evse_id)

        self.function = button.function
        self.entity_description = button
        self._attr_unique_id = f"{button.key}_{evse_id}"

    async def async_press(self) -> None:
        """Handle the button press."""
        await self.function(self.connector.client, self.evse_id)


class RefreshChargeCardsButton(BaseEntity, ButtonEntity):
    """Defines the refresh charge cards button."""

    def __init__(self, connector: Connector) -> None:
        """Initialize the button."""
        super().__init__(connector)

        button = ButtonEntityDescription(
            key="refresh_charge_cards",
            translation_key="refresh_charge_cards",
            icon="mdi:card-account-details",
        )

        self.entity_description = button
        self._attr_unique_id = button.key

    async def async_press(self) -> None:
        """Handle the button press."""
        await self.connector.client.get_charge_cards()
