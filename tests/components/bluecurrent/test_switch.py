"""The tests for Octoptint binary sensor module."""
import asyncio

from homeassistant.components.bluecurrent import Connector
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
    for key in charge_point:
        state = hass.states.get(f"switch.{key}_101")

        if charge_point[key]:
            value = "on"
        else:
            value = "off"
        assert state.state == value
        entry = entity_registry.async_get(f"switch.{key}_101")
        assert entry.unique_id == f"{key}_101"

    # availabile
    switches = er.async_entries_for_config_entry(entity_registry, "uuid")
    assert len(charge_point.keys()) == len(switches) - 1

    state = hass.states.get("switch.available_101")
    assert state.state == "unavailable"
    entry = entity_registry.async_get("switch.available_101")
    assert entry.unique_id == "available_101"


async def test_toggle(hass: HomeAssistant):
    """Test the on / off methods and if the switch gets updated."""

    await init_integration(hass, "switch", data, charge_point)

    state = hass.states.get("switch.public_charging_101")
    print("STATE:", state)

    assert state.state == "off"
    await hass.services.async_call(
        "switch",
        "turn_on",
        {"entity_id": "switch.public_charging_101"},
        blocking=True,
    )

    connector: Connector = hass.data["bluecurrent"]["uuid"]
    connector.charge_points = {"101": {"public_charging": True}}
    async_dispatcher_send(hass, "bluecurrent_value_update_101")

    # wait
    await asyncio.sleep(1)

    state = hass.states.get("switch.public_charging_101")
    assert state.state == "on"

    await hass.services.async_call(
        "switch",
        "turn_off",
        {"entity_id": "switch.public_charging_101"},
        blocking=True,
    )

    connector: Connector = hass.data["bluecurrent"]["uuid"]
    connector.charge_points = {"101": {"public_charging": False}}
    async_dispatcher_send(hass, "bluecurrent_value_update_101")

    # wait
    await asyncio.sleep(1)

    state = hass.states.get("switch.public_charging_101")
    assert state.state == "off"
