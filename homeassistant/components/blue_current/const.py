"""Constants for the Blue Current integration."""

import logging

DOMAIN = "blue_current"

LOGGER = logging.getLogger(__package__)

EVSE_ID = "evse_id"
MODEL_TYPE = "model_type"
VALUE = "value"

DELAYED_CHARGING = "delayed_charging"
PRICE_BASED_CHARGING = "price_based_charging"
SMART_CHARGING = "smart_charging"

DEVICE_IDS = "device_ids"
CURRENT = "current"
START_TIME = "start_time"
STOP_TIME = "stop_time"
OVERRIDE_START_DAYS = "override_start_days"
OVERRIDE_END_DAYS = "override_end_days"
OVERRIDE_CURRENT = "override_current"

MONDAY = "monday"
TUESDAY = "tuesday"
WEDNESDAY = "wednesday"
THURSDAY = "thursday"
FRIDAY = "friday"
SATURDAY = "saturday"
SUNDAY = "sunday"

CHARGE_POINTS = "charge_points"

OVERRIDE_START_TIME = "override_start_time"
OVERRIDE_END_TIME = "override_end_time"
