"""Constants for the BlueCurrent integration."""
import logging

from bluecurrent_api import Client

from homeassistant.components.button import ButtonEntityDescription
from homeassistant.components.sensor import SensorEntityDescription
from homeassistant.const import CONF_ICON, CONF_NAME, CONF_SERVICE

DOMAIN = "bluecurrent"

LOGGER = logging.getLogger(__package__)

PLATFORMS = ["sensor", "switch", "button"]

KEY = "key"

CARD = "card"

EVSE_ID = "evse_id"

DATA = "data"
RESULT = "result"

MODEL_TYPE = "model_type"
OBJECT = "object"
SUCCESS = "success"
ERROR = "error"
FUNCTION = "function"

CHARGE_POINTS = "CHARGE_POINTS"
GRID_STATUS = "GRID_STATUS"
VALUE_TYPES = ("CH_STATUS", "CH_SETTINGS")
SERVICES = ("SOFT_RESET", "REBOOT")
SETTINGS = ("AVAILABLE", "PUBLIC_CHARGING", "PLUG_AND_CHARGE")

AVAILABLE = "available"
UNAVAILABLE = "unavailable"
ACTIVITY = "activity"
TIMESTAMP_KEYS = ("start_session", "stop_session", "offline_since")

# temp
URL = "ws://172.21.109.125:8765"

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
        key="total_voltage",
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
        key="total_current",
        native_unit_of_measurement="A",
        device_class="current",
        name="Total Current",
    ),
    SensorEntityDescription(
        key="actual_kwh",
        native_unit_of_measurement="kWh",
        device_class="energy",
        name="Energy Usage",
        # state_class="measurement",
    ),
    SensorEntityDescription(
        key="start_session",
        native_unit_of_measurement="Timestamp",
        device_class="timestamp",
        name="Session Start Date",
    ),
    SensorEntityDescription(
        key="stop_session",
        native_unit_of_measurement="Timestamp",
        device_class="timestamp",
        name="Session Stop Date",
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
        name="Total cost",
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

BUTTONS = (
    {
        CONF_SERVICE: "get_status",
        CONF_NAME: "Get status",
        CONF_ICON: "mdi:database-arrow-down",
    },
    {
        CONF_SERVICE: "reset",
        CONF_NAME: "Reset",
        CONF_ICON: "mdi:restart",
    },
    {
        CONF_SERVICE: "reboot",
        CONF_NAME: "Reboot",
        CONF_ICON: "mdi:restart-alert",
    },
    {
        CONF_SERVICE: "start_session",
        CONF_NAME: "Start session",
        CONF_ICON: "mdi:play",
    },
    {
        CONF_SERVICE: "stop_session",
        CONF_NAME: "Stop session",
        CONF_ICON: "mdi:stop",
    },
)
BUTTONS2 = (
    ButtonEntityDescription(
        key="get_status", name="Get status", icon="mdi:database-arrow-down"
    ),
    ButtonEntityDescription(key="reset", name="Get Reset", icon="mdi:restart"),
    ButtonEntityDescription(key="reboot", name="Reboot", icon="mdi:restart-alert"),
    ButtonEntityDescription(key="start_session", name="Start session", icon="mdi:play"),
    ButtonEntityDescription(key="stop_session", name="Stop session", icon="mdi:stop"),
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
