"""Entity representing a Blue Current charge point."""

from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .coordinator import BlueCurrentCoordinator, ChargePointCoordinator, GridCoordinator


class BaseEntity(CoordinatorEntity[BlueCurrentCoordinator]):
    """Define a base entity."""

    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(
        self, coordinator: BlueCurrentCoordinator, is_stateless: bool = False
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)

        self.is_stateless = is_stateless
        self.has_value = False

    async def async_added_to_hass(self) -> None:
        """Update when added to hass."""
        await super().async_added_to_hass()
        self._handle_coordinator_update()

    @property
    def available(self) -> bool:
        """Return entity availability."""
        return self.coordinator.client.is_connected() and (
            self.has_value or self.is_stateless
        )


class ChargepointEntity(BaseEntity):
    """Define a charge point entity."""

    def __init__(
        self, coordinator: ChargePointCoordinator, is_stateless: bool = False
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator, is_stateless)

        self._attr_device_info = coordinator._attr_device_info


class GridEntity(BaseEntity):
    """Define a grid entity."""

    def __init__(
        self, coordinator: GridCoordinator, is_stateless: bool = False
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator, is_stateless)
