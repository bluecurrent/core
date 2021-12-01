"""Test BlueCurrent Init Component."""

from unittest.mock import patch

from homeassistant.components.bluecurrent import DOMAIN
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

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
