"""Constants for the Blue Current integration."""

import logging

from homeassistant.const import Platform

DOMAIN = "blue_current"

LOGGER = logging.getLogger(__package__)

PLATFORMS = [Platform.SENSOR]

EVSE_ID = "evse_id"
CARD = "card"
