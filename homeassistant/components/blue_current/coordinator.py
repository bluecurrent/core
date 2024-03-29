"""Blue Current DataUpdateCoordinator."""

from bluecurrent_api import Client

from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import DOMAIN, LOGGER


class BlueCurrentCoordinator(DataUpdateCoordinator):
    """Base data update coordinator."""

    def __init__(self, hass: HomeAssistant, client: Client, name: str) -> None:
        """Initialize the coordinator."""
        super().__init__(hass, LOGGER, name=name)
        self.client = client


class ChargePointCoordinator(BlueCurrentCoordinator):
    """Chargepoint data update coordinator."""

    def __init__(
        self, hass: HomeAssistant, client: Client, evse_id: str, name: str, model: str
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(hass, client, f"Blue Current Charge Point {evse_id}")

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, evse_id)},
            name=name if name != "" else evse_id,
            manufacturer="Blue Current",
            model=model,
        )

        self.data = {}


class GridCoordinator(BlueCurrentCoordinator):
    """Grid data update coordinator."""

    def __init__(self, hass: HomeAssistant, client: Client) -> None:
        """Initialize the coordinator."""
        super().__init__(hass, client, "Blue Current Grid")
        self.data = {}
