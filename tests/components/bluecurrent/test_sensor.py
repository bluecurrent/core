"""The tests for Bluecurrent sensors."""
import asyncio
from datetime import datetime

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
    "actual_v1": 14,
    "actual_v2": 18,
    "actual_v3": 15,
    "actual_p1": 19,
    "actual_p2": 14,
    "actual_p3": 15,
    "activity": "available",
    "start_session": datetime.strptime("2021-11-18T14:12:23", "%Y-%m-%dT%H:%M:%S"),
    "stop_session": datetime.strptime("2021-11-18T14:32:23", "%Y-%m-%dT%H:%M:%S"),
    "offline_since": datetime.strptime("2021-11-18T14:32:23", "%Y-%m-%dT%H:%M:%S"),
    "total_cost": 13.32,
    "total_current": 54,
    "total_voltage": 34,
    "vehicle_status": "offline",
    "actual_kwh": 11,
}

grid = {
    "grid_actual_p1": 12,
    "grid_actual_p2": 14,
    "grid_actual_p3": 15,
    "grid_total_current": 13.7,
}


async def test_sensors(hass: HomeAssistant):
    """Test the underlying sensors."""
    await init_integration(hass, "sensor", data, charge_point, grid)

    entity_registry = er.async_get(hass)
    for key in charge_point:
        state = hass.states.get(f"sensor.{key}_101")
        assert state is not None
        assert state.state == str(charge_point[key])
        entry = entity_registry.async_get(f"sensor.{key}_101")
        assert entry.unique_id == f"{key}_101"

    for key in grid:
        state = hass.states.get(f"sensor.{key}")
        assert state is not None
        assert state.state == str(grid[key])
        entry = entity_registry.async_get(f"sensor.{key}")
        assert entry.unique_id == key

    sensors = er.async_entries_for_config_entry(entity_registry, "uuid")
    assert len(charge_point.keys()) + len(grid.keys()) == len(sensors)


async def test_sensor_update(hass: HomeAssistant):
    """Test if the sensors get updated when there is new data."""
    await init_integration(hass, "sensor", data, charge_point, grid)
    key = "actual_v1"
    grid_key = "grid_actual_p1"
    entity_registry = er.async_get(hass)

    connector: Connector = hass.data["bluecurrent"]["uuid"]

    # charge_points get reset but that doesn't matter for this test.
    connector.charge_points = {"101": {key: 20}}
    connector.grid = {grid_key: 20}
    async_dispatcher_send(hass, "bluecurrent_status_update_101")
    async_dispatcher_send(hass, "bluecurrent_grid_update")

    # wait
    await asyncio.sleep(1)

    # test data updated
    state = hass.states.get(f"sensor.{key}_101")
    assert state is not None
    assert state.state == str(20)
    entry = entity_registry.async_get(f"sensor.{key}_101")
    assert entry.unique_id == f"{key}_101"

    # grid
    state = hass.states.get(f"sensor.{grid_key}")
    assert state is not None
    assert state.state == str(20)
    entry = entity_registry.async_get(f"sensor.{grid_key}")
    assert entry.unique_id == f"{grid_key}"

    # test unavailable
    state = hass.states.get("sensor.actual_v2_101")
    assert state is not None
    assert state.state == "unavailable"
    entry = entity_registry.async_get("sensor.actual_v2_101")
    assert entry.unique_id == "actual_v2_101"

    # grid
    state = hass.states.get("sensor.grid_actual_p2")
    assert state is not None
    assert state.state == "unavailable"
    entry = entity_registry.async_get("sensor.grid_actual_p2")
    assert entry.unique_id == "grid_actual_p2"
