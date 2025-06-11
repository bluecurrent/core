"""Provide the device conditions for Blue Current."""

from __future__ import annotations

import voluptuous as vol

from homeassistant.components.device_automation import InvalidDeviceAutomationConfig
from homeassistant.const import (
    ATTR_ENTITY_ID,
    CONF_CONDITION,
    CONF_DEVICE_ID,
    CONF_DOMAIN,
    CONF_ENTITY_ID,
    CONF_TYPE,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import (
    condition,
    config_validation as cv,
    device_registry as dr,
)
from homeassistant.helpers.typing import ConfigType, TemplateVarsType

from . import DOMAIN

ACTIVITY_TYPES = {"available", "charging", "unavailable", "error", "offline"}

VEHICLE_STATUS_TYPES = {
    "standby",
    "vehicle_detected",
    "ready",
    "no_power",
    "vehicle_error",
}

CONDITION_SCHEMA = cv.DEVICE_CONDITION_BASE_SCHEMA.extend(
    {
        vol.Required(CONF_ENTITY_ID): cv.entity_id,
        vol.Required(CONF_TYPE): vol.In(ACTIVITY_TYPES.union(VEHICLE_STATUS_TYPES)),
    }
)


async def async_get_conditions(
    hass: HomeAssistant, device_id: str
) -> list[dict[str, str]]:
    """List device conditions for Blue Current devices."""
    registry = dr.async_get(hass)
    conditions = []

    if (device := registry.async_get(device_id)) is None:
        raise InvalidDeviceAutomationConfig(f"Device ID {device_id} is not valid")

    evse_id = list(device.identifiers)[0][1].lower()

    base_condition = {
        CONF_CONDITION: "device",
        CONF_DEVICE_ID: device_id,
        CONF_DOMAIN: DOMAIN,
    }

    conditions += [
        {
            **base_condition,
            CONF_TYPE: t,
            CONF_ENTITY_ID: f"sensor.{evse_id}_activity",
        }
        for t in ACTIVITY_TYPES
    ]

    conditions += [
        {
            **base_condition,
            CONF_TYPE: t,
            CONF_ENTITY_ID: f"sensor.{evse_id}_vehicle_status",
        }
        for t in VEHICLE_STATUS_TYPES
    ]

    return conditions


@callback
def async_condition_from_config(
    hass: HomeAssistant, config: ConfigType
) -> condition.ConditionCheckerType:
    """Create a function to test a device condition."""
    state = config[CONF_TYPE]

    @callback
    def test_is_state(hass: HomeAssistant, variables: TemplateVarsType) -> bool:
        """Test if an entity is a certain state."""
        return condition.state(hass, config[ATTR_ENTITY_ID], state)

    return test_is_state
