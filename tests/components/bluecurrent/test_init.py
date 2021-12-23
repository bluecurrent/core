"""Test BlueCurrent Init Component."""

from unittest.mock import patch

from bluecurrent_api.errors import WebsocketError
import pytest

from homeassistant.components import bluecurrent
from homeassistant.components.bluecurrent import (
    DOMAIN,
    Connector,
    async_setup,
    async_setup_entry,
)
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

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
            data={"token": "123", "card": {"123"}},
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
            data={"token": "123", "card": {"123"}},
        )
        config_entry.add_to_hass(hass)

        await async_setup_entry(hass, config_entry)


async def test_async_setup(hass: HomeAssistant):
    """Tests async_setup."""
    result = await async_setup(hass, {"bluecurrent": {"token": "123", "card": "123"}})
    assert result is True


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
        "homeassistant.components.bluecurrent.Connector.handle_success"
    ) as handle_success, patch(
        "homeassistant.components.bluecurrent.Connector.get_charge_point_data",
        return_value={True},
    ), patch.object(
        bluecurrent, "Client", TestClient
    ):
        config_entry = MockConfigEntry(
            domain=DOMAIN,
            entry_id="uuid",
            unique_id="uuid",
            data={"token": "123", "card": {"123"}},
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
                "actual_v1": 12,
                "actual_v2": 14,
                "actual_v3": 15,
                "actual_p1": 12,
                "actual_p2": 14,
                "actual_p3": 15,
                "activity": "charging",
                "start_session": "2021-11-18T14:12:23",
                "stop_session": "2021-11-18T14:32:23",
                "offline_since": "2021-11-18T14:32:23",
                "total_cost": 10.52,
                "vehicle_status": "A",
                "actual_kwh": 10,
                "evse_id": "101",
            },
        }
        await connector.on_data(data)
        assert connector.charge_points == {
            "101": {
                "model_type": "hidden",
                "actual_v1": 12,
                "actual_v2": 14,
                "actual_v3": 15,
                "actual_p1": 12,
                "actual_p2": 14,
                "actual_p3": 15,
                "activity": "charging",
                "start_session": "2021-11-18T14:12:23",
                "stop_session": "2021-11-18T14:32:23",
                "offline_since": "2021-11-18T14:32:23",
                "total_cost": 10.52,
                "vehicle_status": "A",
                "actual_kwh": 10,
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
        test_dispatch.assert_called_with()

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
                "activity": "unavailable",
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
                "activity": "unavailable",
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
                "activity": "available",
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
                "activity": "available",
            }
        }
        test_dispatch.assert_called_with("101")

        # test SOFT_RESET
        data = {"object": "SOFT_RESET", "success": True}
        await connector.on_data(data)
        handle_success.assert_called_with(True, "SOFT_RESET")

        # test REBOOT
        data = {"object": "REBOOT", "success": False}
        await connector.on_data(data)
        handle_success.assert_called_with(False, "REBOOT")

        # test ERROR
        data = {"object": "REBOOT", "success": False, "error": "error"}
        assert await connector.on_data(data) is None
