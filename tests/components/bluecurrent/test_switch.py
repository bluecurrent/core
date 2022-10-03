"""The tests for Octoptint binary sensor module."""

from unittest.mock import patch

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
    for key, value in charge_point.items():
        state = hass.states.get(f"switch.{key}_101")
        assert state

        if value:
            str_value = "on"
        else:
            str_value = "off"
        assert state.state == str_value
        entry = entity_registry.async_get(f"switch.{key}_101")
        assert entry
        assert entry.unique_id == f"{key}_101"

    # availabile
    switches = er.async_entries_for_config_entry(entity_registry, "uuid")
    assert len(charge_point.keys()) == len(switches) - 1

    state = hass.states.get("switch.available_101")
    assert state
    assert state.state == "unavailable"
    entry = entity_registry.async_get("switch.available_101")
    assert entry
    assert entry.unique_id == "available_101"


async def test_switch_on(hass: HomeAssistant) -> None:
    """Test the switch can be turned on."""
    await init_integration(hass, "switch", data, charge_point)

    with patch(
        "homeassistant.components.bluecurrent.switch.ChargePointSwitch.call_function"
    ) as mock_call_function:
        await hass.services.async_call(
            "switch",
            "turn_on",
            {"entity_id": "switch.public_charging_101"},
            blocking=True,
        )
        await hass.async_block_till_done()

        mock_call_function.assert_called_once_with(True)


async def test_switch_off(hass: HomeAssistant) -> None:
    """Test the switch can be turned off."""
    await init_integration(hass, "switch", data, charge_point)

    with patch(
        "homeassistant.components.bluecurrent.switch.ChargePointSwitch.call_function"
    ) as mock_call_function:
        await hass.services.async_call(
            "switch",
            "turn_off",
            {"entity_id": "switch.public_charging_101"},
            blocking=True,
        )
        await hass.async_block_till_done()

        mock_call_function.assert_called_once_with(False)


async def test_switch_update(hass: HomeAssistant):
    """Test the on / off methods and if the switch gets updated."""

    await init_integration(hass, "switch", data, charge_point)

    state = hass.states.get("switch.public_charging_101")
    assert state
    assert state.state == "off"

    connector: Connector = hass.data["bluecurrent"]["uuid"]
    connector.charge_points = {"101": {"public_charging": True}}
    async_dispatcher_send(hass, "bluecurrent_value_update_101")

    state = hass.states.get("switch.public_charging_101")
    assert state
    assert state.state == "on"

    connector.charge_points = {"101": {"public_charging": False}}
    async_dispatcher_send(hass, "bluecurrent_value_update_101")

    state = hass.states.get("switch.public_charging_101")
    assert state
    assert state.state == "off"
