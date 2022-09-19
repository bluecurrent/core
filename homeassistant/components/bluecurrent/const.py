"""Constants for the BlueCurrent integration."""
import logging

from bluecurrent_api import Client

from homeassistant.components.sensor import SensorEntityDescription
from homeassistant.const import CONF_ICON, CONF_NAME

DOMAIN = "bluecurrent"

LOGGER = logging.getLogger(__package__)

PLATFORMS = ["sensor", "switch"]

ACTIVITY = "activity"
AVAILABLE = "available"
CHARGE_POINTS = "CHARGE_POINTS"
DATA = "data"
DELAY = 10
EVSE_ID = "evse_id"
ERROR = "error"
GRID_STATUS = "GRID_STATUS"
FUNCTION = "function"
KEY = "key"
MODEL_TYPE = "model_type"
OBJECT = "object"
RESULT = "result"
SETTINGS = ("AVAILABLE", "PUBLIC_CHARGING", "PLUG_AND_CHARGE")
SUCCESS = "success"
TIMESTAMP_KEYS = ("start_session", "stop_session", "offline_since")
UNAVAILABLE = "unavailable"
VALUE_TYPES = ("CH_STATUS", "CH_SETTINGS")

SENSORS = (
    SensorEntityDescription(
        key="ch_actual_v1",
        native_unit_of_measurement="V",
        device_class="voltage",
        name="Voltage Phase 1",
    ),
    SensorEntityDescription(
        key="ch_actual_v2",
        native_unit_of_measurement="V",
        device_class="voltage",
        name="Voltage Phase 2",
    ),
    SensorEntityDescription(
        key="ch_actual_v3",
        native_unit_of_measurement="V",
        device_class="voltage",
        name="Voltage Phase 3",
    ),
    SensorEntityDescription(
        key="ch_total_voltage",
        native_unit_of_measurement="V",
        device_class="voltage",
        name="Total Voltage",
    ),
    SensorEntityDescription(
        key="ch_actual_p1",
        native_unit_of_measurement="A",
        device_class="current",
        name="Current Phase 1",
    ),
    SensorEntityDescription(
        key="ch_actual_p2",
        native_unit_of_measurement="A",
        device_class="current",
        name="Current Phase 2",
    ),
    SensorEntityDescription(
        key="ch_actual_p3",
        native_unit_of_measurement="A",
        device_class="current",
        name="Current Phase 3",
    ),
    SensorEntityDescription(
        key="ch_total_current",
        native_unit_of_measurement="A",
        device_class="current",
        name="Total Current",
    ),
    SensorEntityDescription(
        key="ch_actual_kwh",
        native_unit_of_measurement="kWh",
        device_class="energy",
        name="Energy Usage",
    ),
    SensorEntityDescription(
        key="start_datetime",
        native_unit_of_measurement="Timestamp",
        device_class="timestamp",
        name="Session Start Date",
    ),
    SensorEntityDescription(
        key="stop_datetime",
        native_unit_of_measurement="Timestamp",
        device_class="timestamp",
        name="Session Stop Date",
    ),
    SensorEntityDescription(
        key="ch_offline_since",
        native_unit_of_measurement="Timestamp",
        device_class="timestamp",
        name="Offline Since",
    ),
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
        device_class="bluecurrent__vehicle_status",
    ),
    SensorEntityDescription(
        key="ch_activity",
        name="Activity",
        icon="mdi:ev-station",
        device_class="bluecurrent__activity",
    ),
)

GRID_SENSORS = (
    SensorEntityDescription(
        key="grid_actual_p1",
        native_unit_of_measurement="A",
        device_class="current",
        name="Grid Current Phase 1",
    ),
    SensorEntityDescription(
        key="grid_actual_p2",
        native_unit_of_measurement="A",
        device_class="current",
        name="Grid Current Phase 2",
    ),
    SensorEntityDescription(
        key="grid_actual_p3",
        native_unit_of_measurement="A",
        device_class="current",
        name="Grid Current Phase 3",
    ),
    SensorEntityDescription(
        key="grid_total_current",
        native_unit_of_measurement="A",
        device_class="current",
        name="Total Grid Current",
    ),
)

SWITCHES = (
    {
        KEY: "plug_and_charge",
        FUNCTION: Client.set_plug_and_charge,
        CONF_NAME: "Plug and charge",
        CONF_ICON: "mdi:ev-plug-type2",
    },
    {
        KEY: "public_charging",
        FUNCTION: Client.set_public_charging,
        CONF_NAME: "Public charging",
        CONF_ICON: "mdi:account-group",
    },
    {
        KEY: "available",
        FUNCTION: Client.set_available,
        CONF_NAME: "Available",
        CONF_ICON: "mdi:power",
    },
)
