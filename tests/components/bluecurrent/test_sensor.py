"""The tests for Bluecurrent sensors."""
import asyncio
from datetime import datetime

from homeassistant.components.bluecurrent import Connector
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.dispatcher import async_dispatcher_send
import homeassistant.util.dt as dt_util

from . import init_integration

data = {
    "101": {
        "model_type": "hidden",
        "evse_id": "101",
    }
}

charge_point = {
    "ch_actual_v1": 14,
    "ch_actual_v2": 18,
    "ch_actual_v3": 15,
    "ch_actual_p1": 19,
    "ch_actual_p2": 14,
    "ch_actual_p3": 15,
    "ch_activity": "available",
    "start_datetime": datetime.strptime("20211118 14:12:23+01:00", "%Y%m%d %H:%M:%S%z"),
    "stop_datetime": datetime.strptime("20211118 14:32:23+01:00", "%Y%m%d %H:%M:%S%z"),
    "ch_offline_since": datetime.strptime(
        "20211118 14:32:23+01:00", "%Y%m%d %H:%M:%S%z"
    ),
    "total_cost": 13.32,
    "ch_total_current": 54,
    "ch_total_voltage": 34,
    "vehicle_status": "offline",
    "ch_actual_kwh": 11,
}

grid = {
    "grid_actual_p1": 12,
    "grid_actual_p2": 14,
    "grid_actual_p3": 15,
    "grid_total_current": 13.7,
}


def fix_timestamps():
    """Change the timestamp to the expected result."""
    charge_point["start_datetime"] = str(
        dt_util.as_local(charge_point["start_datetime"])
    ).replace(" ", "T")
    charge_point["stop_datetime"] = str(
        dt_util.as_local(charge_point["stop_datetime"])
    ).replace(" ", "T")
    charge_point["ch_offline_since"] = str(
        dt_util.as_local(charge_point["ch_offline_since"])
    ).replace(" ", "T")


async def test_sensors(hass: HomeAssistant):
    """Test the underlying sensors."""
    await init_integration(hass, "sensor", data, charge_point, grid)

    fix_timestamps()

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
    key = "ch_actual_v1"
    grid_key = "grid_actual_p1"
    entity_registry = er.async_get(hass)

    connector: Connector = hass.data["bluecurrent"]["uuid"]

    connector.charge_points = {"101": {key: 20}}
    connector.grid = {grid_key: 20}
    async_dispatcher_send(hass, "bluecurrent_value_update_101")
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
    state = hass.states.get("sensor.ch_actual_v2_101")
    assert state is not None
    assert state.state == "unavailable"
    entry = entity_registry.async_get("sensor.ch_actual_v2_101")
    assert entry.unique_id == "ch_actual_v2_101"

    # grid
    state = hass.states.get("sensor.grid_actual_p2")
    assert state is not None
    assert state.state == "unavailable"
    entry = entity_registry.async_get("sensor.grid_actual_p2")
    assert entry.unique_id == "grid_actual_p2"
