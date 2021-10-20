"""Support for BlueCurrent sensors."""
from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_DEVICE_CLASS, CONF_NAME, CONF_UNIT_OF_MEASUREMENT
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import ChargePointEntity, Connector
from .const import DOMAIN, SENSOR_TYPES


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Blue Current sensors."""
    connector = hass.data[DOMAIN][entry.entry_id]

    sensor_list = []
    for evse_id in connector.charge_points.keys():
        for sensor in SENSOR_TYPES.items():
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
        self, connector: Connector, evse_id: str, sensor: tuple[str, dict[str, str]]
    ) -> None:
        """Initialize the sensor."""
        super().__init__(connector, sensor[1][CONF_NAME], evse_id)

        self._data_id = sensor[0]
        self._attr_native_unit_of_measurement = sensor[1][CONF_UNIT_OF_MEASUREMENT]
        self._attr_device_class = sensor[1][CONF_DEVICE_CLASS]
        self._attr_native_value = 0
        self._attr_device_info = {
            "identifiers": {(DOMAIN, self._evse_id)},
            "name": "NanoCharge",
            "manufacturer": "BlueCurrent",
            "model": "v2",
            "sw_version": "1",
            "via_device": (DOMAIN, "test"),
        }

    @callback
    def update_from_latest_data(self) -> None:
        """Update the sensor from the latest data."""
        self._attr_native_value = self._connector.charge_points[self._evse_id][
            self._data_id
        ]
