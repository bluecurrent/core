"""Constants for the BlueCurrent integration."""
import logging

from bluecurrent_api import Client

from homeassistant.components.button import ButtonEntityDescription
from homeassistant.components.sensor import SensorEntityDescription
from homeassistant.const import CONF_ICON, CONF_NAME

DOMAIN = "bluecurrent"

LOGGER = logging.getLogger(__package__)

PLATFORMS = ["sensor", "switch", "button"]

ACTIVITY = "activity"
AVAILABLE = "available"
CARD = "card"
CHARGE_POINTS = "CHARGE_POINTS"
DATA = "data"
DELAY_1 = 1
DELAY_2 = 20
EVSE_ID = "evse_id"
ERROR = "error"
FUNCTION = "function"
GRID_STATUS = "GRID_STATUS"
KEY = "key"
MODEL_TYPE = "model_type"
OBJECT = "object"
REBOOT = "reboot"
RESET = "reset"
RESULT = "result"
SERVICES = ("SOFT_RESET", "REBOOT", "START_SESSION", "STOP_SESSION")
SETTINGS = ("PUBLIC_CHARGING", "PLUG_AND_CHARGE")
START_SESSION = "start_session"
STOP_SESSION = "stop_session"
TIMESTAMP_KEYS = ("start_datetime", "stop_datetime", "offline_since")
SUCCESS = "success"
UNAVAILABLE = "unavailable"
VALUE_TYPES = ("CH_STATUS", "CH_SETTINGS")

SENSORS = (
    SensorEntityDescription(
        key="actual_v1",
        native_unit_of_measurement="V",
        device_class="voltage",
        name="Voltage Phase 1",
        entity_registry_enabled_default=False,
    ),
    SensorEntityDescription(
        key="actual_v2",
        native_unit_of_measurement="V",
        device_class="voltage",
        name="Voltage Phase 2",
        entity_registry_enabled_default=False,
    ),
    SensorEntityDescription(
        key="actual_v3",
        native_unit_of_measurement="V",
        device_class="voltage",
        name="Voltage Phase 3",
        entity_registry_enabled_default=False,
    ),
    SensorEntityDescription(
        key="avg_voltage",
        native_unit_of_measurement="V",
        device_class="voltage",
        name="Average Voltage",
    ),
    SensorEntityDescription(
        key="actual_p1",
        native_unit_of_measurement="A",
        device_class="current",
        name="Current Phase 1",
        entity_registry_enabled_default=False,
    ),
    SensorEntityDescription(
        key="actual_p2",
        native_unit_of_measurement="A",
        device_class="current",
        name="Current Phase 2",
        entity_registry_enabled_default=False,
    ),
    SensorEntityDescription(
        key="actual_p3",
        native_unit_of_measurement="A",
        device_class="current",
        name="Current Phase 3",
        entity_registry_enabled_default=False,
    ),
    SensorEntityDescription(
        key="avg_current",
        native_unit_of_measurement="A",
        device_class="current",
        name="Average Current",
    ),
    SensorEntityDescription(
        key="total_kw",
        native_unit_of_measurement="kW",
        device_class="power",
        name="Total kW",
    ),
    SensorEntityDescription(
        key="actual_kwh",
        native_unit_of_measurement="kWh",
        device_class="energy",
        name="Energy Usage",
        state_class="total_increasing",
    ),
    SensorEntityDescription(
        key="start_datetime",
        native_unit_of_measurement="Timestamp",
        device_class="timestamp",
        name="Started On",
    ),
    SensorEntityDescription(
        key="stop_datetime",
        native_unit_of_measurement="Timestamp",
        device_class="timestamp",
        name="Stopped On",
    ),
    SensorEntityDescription(
        key="offline_since",
        native_unit_of_measurement="Timestamp",
        device_class="timestamp",
        name="Offline Since",
    ),
    SensorEntityDescription(
        key="total_cost",
        native_unit_of_measurement="EUR",
        device_class="monetary",
        name="Total Cost",
    ),
    SensorEntityDescription(
        key="vehicle_status",
        name="Vehicle Status",
        icon="mdi:car",
        device_class="bluecurrent__vehicle_status",
    ),
    SensorEntityDescription(
        key="activity",
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
        entity_registry_enabled_default=False,
    ),
    SensorEntityDescription(
        key="grid_actual_p2",
        native_unit_of_measurement="A",
        device_class="current",
        name="Grid Current Phase 2",
        entity_registry_enabled_default=False,
    ),
    SensorEntityDescription(
        key="grid_actual_p3",
        native_unit_of_measurement="A",
        device_class="current",
        name="Grid Current Phase 3",
        entity_registry_enabled_default=False,
    ),
    SensorEntityDescription(
        key="grid_avg_current",
        native_unit_of_measurement="A",
        device_class="current",
        name="Average Grid Current",
    ),
    SensorEntityDescription(
        key="grid_max_current",
        native_unit_of_measurement="A",
        device_class="current",
        name="Max Grid Current",
    ),
)

BUTTONS = (
    ButtonEntityDescription(key=RESET, name="Reset", icon="mdi:restart"),
    ButtonEntityDescription(key=REBOOT, name="Reboot", icon="mdi:restart-alert"),
    ButtonEntityDescription(key=START_SESSION, name="Start session", icon="mdi:play"),
    ButtonEntityDescription(key=STOP_SESSION, name="Stop session", icon="mdi:stop"),
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
        FUNCTION: Client.set_operative,
        CONF_NAME: "Availability",
        CONF_ICON: "mdi:power",
    },
)
