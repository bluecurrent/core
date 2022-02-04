"""Test BlueCurrent Init Component."""

from unittest.mock import patch

from bluecurrent_api.client import Client
from bluecurrent_api.errors import WebsocketError
import pytest

from homeassistant.components import bluecurrent
from homeassistant.components.bluecurrent import (
    DOMAIN,
    Connector,
    async_setup_entry,
    set_entities_unavalible,
)
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from . import init_integration

from tests.common import MockConfigEntry


async def test_load_and_unload_entry(hass: HomeAssistant):
    """Test load and unload."""

    with patch("homeassistant.components.bluecurrent.PLATFORMS", []), patch(
        "homeassistant.components.bluecurrent.Connector.connect", return_value={True}
    ), patch(
        "homeassistant.components.bluecurrent.Connector.start_loop", return_value={True}
    ):
        config_entry = MockConfigEntry(
            domain=DOMAIN,
            entry_id="uuid",
            unique_id="uuid",
            data={"api_token": "123", "card": "123"},
        )
        config_entry.add_to_hass(hass)

        await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

        assert config_entry.state == ConfigEntryState.LOADED

        assert await hass.config_entries.async_unload(config_entry.entry_id)
        assert config_entry.state == ConfigEntryState.NOT_LOADED


async def test_config_not_ready(hass: HomeAssistant):
    """Tests if ConfigEntryNotReady is raised when connect raises a WebsockerError."""
    with patch(
        "homeassistant.components.bluecurrent.Connector.connect",
        side_effect=WebsocketError,
    ), pytest.raises(ConfigEntryNotReady):
        config_entry = MockConfigEntry(
            domain=DOMAIN,
            entry_id="uuid",
            unique_id="uuid",
            data={"api_token": "123", "card": "123"},
        )
        config_entry.add_to_hass(hass)

        await async_setup_entry(hass, config_entry)


async def test_async_setup(hass: HomeAssistant):
    """Tests async_setup."""
    # need to patch validate_input in config_flow
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        entry_id="uuid",
        unique_id="uuid",
        data={"api_token": "123", "card": "123"},
    )
    config_entry.add_to_hass(hass)
    result = await bluecurrent.async_setup(hass, config_entry.data)
    assert result is True


async def test_set_entities_unavalible(hass: HomeAssistant):
    """Tests set_entities_unavailable."""

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
    }

    await init_integration(hass, "sensor", data, charge_point)

    set_entities_unavalible(hass, "uuid")
    state = hass.states.get("sensor.ch_actual_v1_101")

    for key in charge_point:
        state = hass.states.get(f"sensor.{key}_101")
        assert state.state == "unavailable"


async def test_on_data(hass: HomeAssistant):
    """Test on_data."""

    class TestClient:
        """Test class to mock the client."""

        async def get_grid_status(self, evse_id):
            """Test get_grid_status."""

        async def disconnect(self):
            """Test disconnect."""

    with patch("homeassistant.components.bluecurrent.PLATFORMS", []), patch(
        "homeassistant.components.bluecurrent.Connector.connect", return_value={True}
    ), patch(
        "homeassistant.components.bluecurrent.Connector.start_loop", return_value={True}
    ), patch(
        "homeassistant.components.bluecurrent.Connector.dispatch_signal"
    ) as test_dispatch, patch(
        "homeassistant.components.bluecurrent.Connector.get_charge_point_data",
        return_value={True},
    ), patch.object(
        bluecurrent, "Client", TestClient
    ):
        config_entry = MockConfigEntry(
            domain=DOMAIN,
            entry_id="uuid",
            unique_id="uuid",
            data={"api_token": "123", "card": "123"},
        )
        config_entry.add_to_hass(hass)

        await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

        connector: Connector = hass.data["bluecurrent"]["uuid"]

        # test CHARGE_POINTS
        data = {
            "object": "CHARGE_POINTS",
            "data": [{"evse_id": "101", "model_type": "hidden"}],
        }
        await connector.on_data(data)
        assert connector.charge_points == {"101": {"model_type": "hidden"}}

        # test CH_STATUS
        data = {
            "object": "CH_STATUS",
            "data": {
                "ch_actual_v1": 12,
                "ch_actual_v2": 14,
                "ch_actual_v3": 15,
                "ch_actual_p1": 12,
                "ch_actual_p2": 14,
                "ch_actual_p3": 15,
                "ch_activity": "charging",
                "start_datetime": "2021-11-18T14:12:23",
                "stop_datetime": "2021-11-18T14:32:23",
                "ch_offline_since": "2021-11-18T14:32:23",
                "total_cost": 10.52,
                "vehicle_status": "A",
                "ch_actual_kwh": 10,
                "evse_id": "101",
            },
        }
        await connector.on_data(data)
        assert connector.charge_points == {
            "101": {
                "model_type": "hidden",
                "ch_actual_v1": 12,
                "ch_actual_v2": 14,
                "ch_actual_v3": 15,
                "ch_actual_p1": 12,
                "ch_actual_p2": 14,
                "ch_actual_p3": 15,
                "ch_activity": "charging",
                "start_datetime": "2021-11-18T14:12:23",
                "stop_datetime": "2021-11-18T14:32:23",
                "ch_offline_since": "2021-11-18T14:32:23",
                "total_cost": 10.52,
                "vehicle_status": "A",
                "ch_actual_kwh": 10,
                "available": False,
            }
        }

        test_dispatch.assert_called_once_with("101")

        # test GRID_STATUS
        data = {
            "object": "GRID_STATUS",
            "data": {
                "grid_actual_p1": 12,
                "grid_actual_p2": 14,
                "grid_actual_p3": 15,
            },
        }
        await connector.on_data(data)
        assert connector.grid == {
            "grid_actual_p1": 12,
            "grid_actual_p2": 14,
            "grid_actual_p3": 15,
        }
        test_dispatch.assert_called()

        # reset charge_point
        connector.charge_points["101"] = {}

        # test CH_SETTINGS
        data = {
            "object": "CH_SETTINGS",
            "data": {
                "available": False,
                "plug_and_charge": False,
                "public_charging": False,
                "evse_id": "101",
            },
        }
        await connector.on_data(data)
        assert connector.charge_points == {
            "101": {
                "available": False,
                "plug_and_charge": False,
                "public_charging": False,
                "ch_activity": "unavailable",
            }
        }
        test_dispatch.assert_called_with("101")

        # test PUBLIC_CHARGING
        data = {"object": "PUBLIC_CHARGING", "result": True, "evse_id": "101"}
        await connector.on_data(data)
        assert connector.charge_points == {
            "101": {
                "available": False,
                "plug_and_charge": False,
                "public_charging": True,
                "ch_activity": "unavailable",
            }
        }
        test_dispatch.assert_called_with("101")

        # test AVAILABLE
        data = {"object": "AVAILABLE", "result": True, "evse_id": "101"}
        await connector.on_data(data)
        assert connector.charge_points == {
            "101": {
                "available": True,
                "plug_and_charge": False,
                "public_charging": True,
                "ch_activity": "available",
            }
        }
        test_dispatch.assert_called_with("101")

        # test PLUG_AND_CHARGE
        data = {"object": "PLUG_AND_CHARGE", "result": True, "evse_id": "101"}
        await connector.on_data(data)
        assert connector.charge_points == {
            "101": {
                "available": True,
                "plug_and_charge": True,
                "public_charging": True,
                "ch_activity": "available",
            }
        }
        test_dispatch.assert_called_with("101")

        # test SOFT_RESET
        data = {"object": "SOFT_RESET", "success": True}
        await connector.on_data(data)

        # test REBOOT
        data = {"object": "REBOOT", "success": False}
        await connector.on_data(data)

        # test ERROR
        data = {"object": "REBOOT", "success": False, "error": "error"}
        assert await connector.on_data(data) is None


async def test_dispatch_signal(hass: HomeAssistant):
    """Tests dispatch_signal."""
    with patch(
        "homeassistant.components.bluecurrent.async_dispatcher_send"
    ) as test_async_dispatcher_send:
        config_entry = MockConfigEntry(
            domain=DOMAIN,
            entry_id="uuid",
            unique_id="uuid",
            data={"api_token": "123", "card": "123"},
        )

        connector = Connector(hass, config_entry, Client)

        connector.dispatch_signal("101")
        test_async_dispatcher_send.assert_called_with(
            hass, "bluecurrent_value_update_101"
        )

        connector.dispatch_signal()
        test_async_dispatcher_send.assert_called_with(hass, "bluecurrent_grid_update")


async def test_reconnect(hass: HomeAssistant):
    """Tests reconnect."""

    with patch(
        "homeassistant.components.bluecurrent.Connector.connect",
        side_effect=WebsocketError,
    ), patch(
        "homeassistant.components.bluecurrent.async_call_later"
    ) as test_async_call_later:

        config_entry = MockConfigEntry(
            domain=DOMAIN,
            entry_id="uuid",
            unique_id="uuid",
            data={"api_token": "123", "card": "123"},
        )

        connector = Connector(hass, config_entry, Client)
        await connector.reconnect()

        test_async_call_later.assert_called_with(hass, 100, connector.reconnect)
