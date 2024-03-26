"""Entity representing a Blue Current charge point."""

from homeassistant.const import ATTR_NAME
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MODEL_TYPE
from .coordinator import BlueCurrentCoordinator


class BlueCurrentEntity(CoordinatorEntity[BlueCurrentCoordinator]):
    """Define a base Blue Current entity."""

    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(self, coordinator: BlueCurrentCoordinator) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        self.has_value = True

    async def async_added_to_hass(self) -> None:
        """Update when added to hass."""
        await super().async_added_to_hass()
        self._handle_coordinator_update()

    @property
    def available(self) -> bool:
        """Return entity availability."""
        return self.coordinator.connected and self.has_value


class ChargepointEntity(BlueCurrentEntity):
    """Define a base charge point entity."""

    def __init__(self, coordinator: BlueCurrentCoordinator, evse_id: str) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)

        chargepoint_name = coordinator.charge_points[evse_id][ATTR_NAME]

        self.evse_id = evse_id
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, evse_id)},
            name=chargepoint_name if chargepoint_name != "" else evse_id,
            manufacturer="Blue Current",
            model=coordinator.charge_points[evse_id][MODEL_TYPE],
        )
