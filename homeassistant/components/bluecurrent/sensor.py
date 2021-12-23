"""Support for BlueCurrent sensors."""
from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback
import homeassistant.util.dt as dt_util

from . import BlueCurrentEntity, Connector
from .const import DOMAIN, GRID_SENSORS, SENSORS, TIMESTAMP_KEYS


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Blue Current sensors."""
    connector: Connector = hass.data[DOMAIN][entry.entry_id]
    sensor_list: list[Any] = []
    for evse_id in connector.charge_points.keys():
        for sensor in SENSORS:
            sensor_list.append(
                ChargePointSensor(
                    connector,
                    evse_id,
                    sensor,
                )
            )
    for grid_sesor in GRID_SENSORS:
        sensor_list.append(
            GridSensor(
                connector,
                grid_sesor,
            )
        )

    async_add_entities(sensor_list)


class ChargePointSensor(BlueCurrentEntity, SensorEntity):
    """Base charge point sensor."""

    _attr_should_poll = False

    def __init__(
        self, connector: Connector, evse_id: str, sensor: SensorEntityDescription
    ) -> None:
        """Initialize the sensor."""
        assert sensor.name is not None
        super().__init__(connector, "sensor", sensor.name, evse_id)

        self._key = sensor.key
        self._attr_native_unit_of_measurement = sensor.native_unit_of_measurement
        # self._attr_state_class = sensor.state_class
        self._attr_device_class = sensor.device_class
        self._attr_icon = sensor.icon
        self._attr_unique_id = f"{sensor.key}_{evse_id}"
        self.entity_id = f"sensor.{sensor.key}_{evse_id}"

    @callback
    def update_from_latest_data(self) -> None:
        """Update the sensor from the latest data."""

        new_value = self._connector.charge_points[self._evse_id].get(self._key)
        if new_value is not None:
            if self._key in TIMESTAMP_KEYS:
                new_value = dt_util.as_local(new_value)
            self._attr_available = True
            self._attr_native_value = new_value
        else:
            self._attr_available = False


class GridSensor(SensorEntity):
    """Base grid sensor."""

    _attr_should_poll = False

    def __init__(self, connector: Connector, sensor: SensorEntityDescription) -> None:
        """Initialize the sensor."""
        self._key = sensor.key
        self._attr_native_unit_of_measurement = sensor.native_unit_of_measurement
        self._attr_device_class = sensor.device_class
        self._attr_icon = sensor.icon
        self._attr_unique_id = sensor.key
        self._attr_native_value = 0
        self.entity_id = f"sensor.{sensor.key}"
        self._connector = connector

    async def async_added_to_hass(self) -> None:
        """Register callbacks."""

        @callback
        def update() -> None:
            """Update the state."""
            self.update_from_latest_data()
            self.async_write_ha_state()

        self.async_on_remove(
            async_dispatcher_connect(self.hass, "bluecurrent_grid_update", update)
        )

        self.update_from_latest_data()

    @callback
    def update_from_latest_data(self) -> None:
        """Update the sensor from the latest data."""

        new_value = self._connector.grid.get(self._key)
        if new_value is not None:
            self._attr_available = True
            self._attr_native_value = new_value
        else:
            self._attr_available = False
