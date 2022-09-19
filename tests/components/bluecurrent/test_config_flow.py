"""Test the BlueCurrent config flow."""
from unittest.mock import patch

from homeassistant import config_entries
from homeassistant.components.bluecurrent.config_flow import (
    InvalidToken,
    WebsocketError,
)
from homeassistant.components.bluecurrent.const import DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import RESULT_TYPE_CREATE_ENTRY, RESULT_TYPE_FORM


async def test_form(hass: HomeAssistant) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == RESULT_TYPE_FORM
    assert result["errors"] == {}


async def test_user(hass: HomeAssistant) -> None:
    """Test if the default card is set."""

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == RESULT_TYPE_FORM
    assert result["errors"] == {}

    with patch(
        "homeassistant.components.bluecurrent.config_flow.validate_input",
        return_value={True},
    ), patch(
        "homeassistant.components.bluecurrent.async_setup_entry",
        return_value=True,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "api_token": "123",
            },
        )
        await hass.async_block_till_done()

    assert result2["type"] == RESULT_TYPE_CREATE_ENTRY
    assert result2["title"] == "123"
    assert result2["data"] == {"api_token": "123"}


async def test_form_invalid_token(hass: HomeAssistant) -> None:
    """Test we handle invalid api token."""
    with patch(
        "homeassistant.components.bluecurrent.config_flow.validate_input",
        side_effect=InvalidToken,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
            data={"api_token": "123"},
        )
        assert result["errors"] == {"base": "invalid_token"}


async def test_form_exception(hass: HomeAssistant) -> None:
    """Test we handle invalid token."""
    with patch(
        "homeassistant.components.bluecurrent.config_flow.validate_input",
        side_effect=Exception,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
            data={"api_token": "123"},
        )
        assert result["errors"] == {"base": "unknown"}


async def test_form_cannot_connect(hass: HomeAssistant) -> None:
    """Test we handle cannot connect error."""

    with patch(
        "homeassistant.components.bluecurrent.config_flow.validate_input",
        side_effect=WebsocketError,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
            data={"api_token": "123"},
        )
        assert result["errors"] == {"base": "cannot_connect"}
