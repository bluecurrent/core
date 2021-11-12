"""Constants for the BlueCurrent integration."""
import logging

from homeassistant.components.sensor import SensorEntityDescription

DOMAIN = "bluecurrent"

LOGGER = logging.getLogger(__package__)

PLATFORMS = ["sensor"]

EVSE_ID = "evse_id"

DATA = "data"

# temp
URL = "ws://172.21.185.83:8765"

DELAY = 10


SENSORS = (
    SensorEntityDescription(
        key="actual_v1",
        native_unit_of_measurement="V",
        device_class="voltage",
        name="Voltage Phase 1",
    ),
    SensorEntityDescription(
        key="actual_v2",
        native_unit_of_measurement="V",
        device_class="voltage",
        name="Voltage Phase 2",
    ),
    SensorEntityDescription(
        key="actual_v3",
        native_unit_of_measurement="V",
        device_class="voltage",
        name="Voltage Phase 3",
    ),
    SensorEntityDescription(
        key="total voltage",
        native_unit_of_measurement="V",
        device_class="voltage",
        name="Total Voltage",
    ),
    SensorEntityDescription(
        key="actual_p1",
        native_unit_of_measurement="A",
        device_class="current",
        name="Current Phase 1",
    ),
    SensorEntityDescription(
        key="actual_p2",
        native_unit_of_measurement="A",
        device_class="current",
        name="Current Phase 2",
    ),
    SensorEntityDescription(
        key="actual_p3",
        native_unit_of_measurement="A",
        device_class="current",
        name="Current Phase 3",
    ),
    SensorEntityDescription(
        key="total current",
        native_unit_of_measurement="A",
        device_class="current",
        name="Total Current",
    ),
    SensorEntityDescription(
        key="actual_kwh",
        native_unit_of_measurement="kWh",
        device_class="energy",
        name="Energy Usage",
    ),
    # SensorEntityDescription(
    #     key="start_datetime",
    #     native_unit_of_measurement="Timestamp",
    #     device_class="timestamp",
    #     name="Session Start Date",
    # ),
    # SensorEntityDescription(
    #     key="stop_datetime",
    #     native_unit_of_measurement="Timestamp",
    #     device_class="timestamp",
    #     name="Session Stop Date",
    # ),
    # SensorEntityDescription(
    #     key="ch_offline_since",
    #     native_unit_of_measurement="Timestamp",
    #     device_class="timestamp",
    #     name="Offline Since",
    # ),
    SensorEntityDescription(
        key="total_cost",
        native_unit_of_measurement="EUR",
        device_class="monetary",
        name="Total cost",
    ),
    SensorEntityDescription(
        key="vehicle_status",
        name="Vehicle Status",
        icon="mdi:car",
    ),
    SensorEntityDescription(
        key="activity",
        name="Activity",
        icon="mdi:ev-station",
    ),
)
# duration?

GRID_SENSORS = (
    SensorEntityDescription(
        key="actual_p1",
        native_unit_of_measurement="A",
        device_class="current",
        name="Grid current Phase 1",
    ),
    SensorEntityDescription(
        key="actual_p2",
        native_unit_of_measurement="A",
        device_class="current",
        name="Grid current Phase 2",
    ),
    SensorEntityDescription(
        key="actual_p3",
        native_unit_of_measurement="A",
        device_class="current",
        name="Grid current Phase 3",
    ),
)
