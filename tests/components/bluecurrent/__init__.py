"""Tests for the BlueCurrent integration."""
from __future__ import annotations

from unittest.mock import patch

from homeassistant.components import bluecurrent
from homeassistant.components.bluecurrent.const import DOMAIN, SWITCHES
from homeassistant.config_entries import ConfigEntryState

from tests.common import MockConfigEntry


class TestClient:
    """Test class to mock the client."""

    async def disconnect(self):
        """Test disconnect."""

    async def get_status(self, evse_id):
        """Test get_status."""

    async def set_available(self, evse_id, value):
        """Test set_available."""

    async def set_plug_and_charge(self, evse_id, value):
        """Test set_plug_and_charge."""

    async def set_public_charging(self, evse_id, value):
        """Test set_public_charging."""


TEST_SWITCHES = (
    {
        "key": "plug_and_charge",
        "function": TestClient.set_plug_and_charge,
        "name": "Plug and charge",
        "icon": "mdi:ev-plug-type2",
    },
    {
        "key": "public_charging",
        "function": TestClient.set_public_charging,
        "name": "Public charging",
        "icon": "mdi:account-group",
    },
    {
        "key": "available",
        "function": TestClient.set_available,
        "name": "Available",
        "icon": "mdi:power",
    },
)


async def init_integration(hass, platform, data: dict, charge_point: dict, grid={}):
    """Set up the octoprint integration in Home Assistant."""

    data["101"].update(charge_point)
    with patch("homeassistant.components.bluecurrent.PLATFORMS", [platform]), patch(
        "homeassistant.components.bluecurrent.Connector.connect", return_value={True}
    ), patch(
        "homeassistant.components.bluecurrent.Connector.start_loop", return_value={True}
    ), patch(
        "homeassistant.components.bluecurrent.Connector.grid", grid
    ), patch(
        "homeassistant.components.bluecurrent.Connector.charge_points", data
    ), patch.object(
        bluecurrent, "Client", TestClient
    ), patch.dict(
        SWITCHES[0], TEST_SWITCHES[0]
    ), patch.dict(
        SWITCHES[1], TEST_SWITCHES[1]
    ), patch.dict(
        SWITCHES[2], TEST_SWITCHES[2]
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
