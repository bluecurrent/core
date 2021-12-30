"""Support for BlueCurrent buttons."""
from __future__ import annotations

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import BlueCurrentEntity, Connector
from .const import BUTTONS, DOMAIN, EVSE_ID


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Blue Current buttons."""
    connector: Connector = hass.data[DOMAIN][entry.entry_id]
    button_list = []
    for evse_id in connector.charge_points.keys():
        for button in BUTTONS:
            button_list.append(
                ChargePointButton(
                    connector,
                    evse_id,
                    button,
                )
            )

    async_add_entities(button_list)


class ChargePointButton(BlueCurrentEntity, ButtonEntity):
    """Base Blue Current button."""

    _attr_should_poll = False

    def __init__(
        self, connector: Connector, evse_id: str, button: ButtonEntityDescription
    ) -> None:
        """Initialize the button."""
        assert button.name is not None
        super().__init__(connector, "button", button.name, evse_id)

        self._attr_icon = button.icon
        self._service = button.key
        self._attr_unique_id = f"{button.key}_{evse_id}"
        self.entity_id = f"button.{button.key}_{evse_id}"

    async def async_press(self) -> None:
        """Handle the button press."""
        await self.hass.services.async_call(
            DOMAIN, self._service, {EVSE_ID: self._evse_id}
        )

    @callback
    def update_from_latest_data(self) -> None:
        """Fetch new state data for the button."""
