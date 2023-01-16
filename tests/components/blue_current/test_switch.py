"""The tests for Bluecurrent switches."""
import asyncio
from unittest.mock import patch

from homeassistant.components.blue_current import Connector
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.dispatcher import async_dispatcher_send

from . import init_integration

data = {
    "101": {
        "model_type": "hidden",
        "evse_id": "101",
    }
}

charge_point = {
    "plug_and_charge": True,
    "public_charging": False,
}


async def test_switches(hass: HomeAssistant):
    """Test the underlying switches."""

    await init_integration(hass, "switch", data, charge_point)

    entity_registry = er.async_get(hass)
    for key, value in charge_point.items():
        state = hass.states.get(f"switch.101_{key}")

        if value:
            value = "on"
        else:
            value = "off"
        assert state.state == value
        entry = entity_registry.async_get(f"switch.101_{key}")
        assert entry.unique_id == f"{key}_101"

    # available
    switches = er.async_entries_for_config_entry(entity_registry, "uuid")
    assert len(charge_point.keys()) == len(switches) - 1

    state = hass.states.get("switch.101_available")
    assert state.state == "unavailable"
    entry = entity_registry.async_get("switch.101_available")
    assert entry.unique_id == "available_101"


async def test_toggle(hass: HomeAssistant):
    """Test the on / off methods and if the switch gets updated."""

    with patch("bluecurrent_api.Client.set_public_charging"):

        await init_integration(hass, "switch", data, charge_point)

        state = hass.states.get("switch.101_public_charging")

        assert state.state == "off"
        await hass.services.async_call(
            "switch",
            "turn_on",
            {"entity_id": "switch.101_public_charging"},
            blocking=True,
        )

        connector: Connector = hass.data["blue_current"]["uuid"]
        connector.charge_points = {"101": {"public_charging": True}}
        async_dispatcher_send(hass, "blue_current_value_update_101")

        # wait
        await asyncio.sleep(1)

        state = hass.states.get("switch.101_public_charging")
        assert state.state == "on"

        await hass.services.async_call(
            "switch",
            "turn_off",
            {"entity_id": "switch.101_public_charging"},
            blocking=True,
        )

        connector: Connector = hass.data["blue_current"]["uuid"]
        connector.charge_points = {"101": {"public_charging": False}}
        async_dispatcher_send(hass, "blue_current_value_update_101")

        # wait
        await asyncio.sleep(1)

        state = hass.states.get("switch.101_public_charging")
        assert state.state == "off"
