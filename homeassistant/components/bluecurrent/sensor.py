"""Support for BlueCurrent sensors."""
from __future__ import annotations

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import ChargePointEntity, Connector
from .const import DOMAIN, SENSORS


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Blue Current sensors."""
    connector = hass.data[DOMAIN][entry.entry_id]

    sensor_list = []
    for evse_id in connector.charge_points.keys():
        for sensor in SENSORS:
            sensor_list.append(
                BlueCurrentSensor(
                    connector,
                    evse_id,
                    sensor,
                )
            )

    async_add_entities(sensor_list)


class BlueCurrentSensor(ChargePointEntity, SensorEntity):
    """Define an Blue Current sensor."""

    _attr_should_poll = False

    def __init__(
        self, connector: Connector, evse_id: str, sensor: SensorEntityDescription
    ) -> None:
        """Initialize the sensor."""
        assert sensor.name is not None
        super().__init__(connector, sensor.name, evse_id)

        self._key = sensor.key
        self._attr_native_unit_of_measurement = sensor.native_unit_of_measurement
        self._attr_device_class = sensor.device_class
        self._attr_icon = sensor.icon
        self._attr_native_value = 0
        self._attr_device_info = {
            "identifiers": {(DOMAIN, evse_id)},
            "name": "NanoCharge",
            "manufacturer": "BlueCurrent",
            "model": "v2",
            "sw_version": "1",
            "via_device": (DOMAIN, "test"),
        }

    @callback
    def update_from_latest_data(self) -> None:
        """Update the sensor from the latest data."""

        if self._key in self._connector.charge_points[self._evse_id]:
            self._attr_native_value = self._connector.charge_points[self._evse_id][
                self._key
            ]
