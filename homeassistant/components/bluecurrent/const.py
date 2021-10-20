"""Constants for the BlueCurrent integration."""
import logging

from homeassistant.const import CONF_DEVICE_CLASS, CONF_NAME, CONF_UNIT_OF_MEASUREMENT

DOMAIN = "bluecurrent"

LOGGER = logging.getLogger(__package__)

PLATFORMS = ["sensor"]

# temp
URL = "ws://172.19.64.172:8765"

SENSOR_TYPES = {
    "voltage 1": {
        CONF_NAME: "Voltage 1",
        CONF_UNIT_OF_MEASUREMENT: "V",
        CONF_DEVICE_CLASS: "voltage",
    },
    "voltage 2": {
        CONF_NAME: "Voltage 2",
        CONF_UNIT_OF_MEASUREMENT: "V",
        CONF_DEVICE_CLASS: "voltage",
    },
    "voltage 3": {
        CONF_NAME: "Voltage 3",
        CONF_UNIT_OF_MEASUREMENT: "V",
        CONF_DEVICE_CLASS: "voltage",
    },
    "current 1": {
        CONF_NAME: "Current 1",
        CONF_UNIT_OF_MEASUREMENT: "A",
        CONF_DEVICE_CLASS: "current",
    },
    "current 2": {
        CONF_NAME: "Current 2",
        CONF_UNIT_OF_MEASUREMENT: "A",
        CONF_DEVICE_CLASS: "current",
    },
    "current 3": {
        CONF_NAME: "Current 3",
        CONF_UNIT_OF_MEASUREMENT: "A",
        CONF_DEVICE_CLASS: "current",
    },
    # "session start": {
    #     CONF_NAME: "start time",
    #     CONF_UNIT_OF_MEASUREMENT: "Timestamp",
    #     CONF_DEVICE_CLASS: "timestamp",
    # },
    # grid
    # total cost
    # session duration
    # total V / A ?
    #     "activity": {CONF_NAME: "activity", CONF_ICON: "mdi:ev-station"},
    # "vehicle status": {CONF_NAME: "vehicle status", CONF_ICON: "mdi:car"},
}
