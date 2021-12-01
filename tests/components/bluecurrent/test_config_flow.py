"""Test the BlueCurrent config flow."""
from unittest.mock import patch

import pytest

from homeassistant import config_entries
from homeassistant.components.bluecurrent.config_flow import (
    InvalidToken,
    WebsocketError,
    validate_input,
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


async def test_default_card(hass: HomeAssistant) -> None:
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
                "token": "123",
            },
        )
        await hass.async_block_till_done()

    assert result2["type"] == RESULT_TYPE_CREATE_ENTRY
    assert result2["title"] == "123"
    assert result2["data"] == {"token": "123", "card": {"card_id": "BCU_APP"}}


async def test_user_card(hass: HomeAssistant) -> None:
    """Test if the user can set a custom card."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == RESULT_TYPE_FORM
    assert result["errors"] == {}

    with patch(
        "homeassistant.components.bluecurrent.config_flow.validate_input",
        return_value=True,
    ), patch(
        "homeassistant.components.bluecurrent.config_flow.get_charge_cards",
        return_value=[{"name": "card 1", "id": 1}, {"name": "card 2", "id": 2}],
    ), patch(
        "homeassistant.components.bluecurrent.async_setup_entry",
        return_value=True,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"token": "123", "add_card": True},
        )
        await hass.async_block_till_done()

    with patch(
        "homeassistant.components.bluecurrent.config_flow.get_charge_cards",
        return_value=[{"name": "card 1", "id": 1}, {"name": "card 2", "id": 2}],
    ), patch(
        "homeassistant.components.bluecurrent.async_setup_entry",
        return_value=True,
    ):
        result3 = await hass.config_entries.flow.async_configure(
            result2["flow_id"],
            {"card": "card 1"},
        )
        await hass.async_block_till_done()

    assert result2["type"] == RESULT_TYPE_FORM

    assert result3["type"] == RESULT_TYPE_CREATE_ENTRY
    assert result3["title"] == "123"
    assert result3["data"] == {"token": "123", "card": {"name": "card 1", "id": 1}}


async def test_form_invalid_token(hass: HomeAssistant) -> None:
    """Test we handle invalid token."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "homeassistant.components.bluecurrent.config_flow.validate_input",
        side_effect=InvalidToken,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "token": "123",
            },
        )

    assert result2["type"] == RESULT_TYPE_FORM
    assert result2["errors"] == {"base": "invalid_token"}


async def test_form_exception(hass: HomeAssistant) -> None:
    """Test we handle invalid token."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "homeassistant.components.bluecurrent.config_flow.validate_input",
        side_effect=Exception,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "token": "123",
            },
        )

    assert result2["type"] == RESULT_TYPE_FORM
    assert result2["errors"] == {"base": "unknown"}


async def test_form_cannot_connect(hass: HomeAssistant) -> None:
    """Test we handle cannot connect error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "homeassistant.components.bluecurrent.config_flow.validate_input",
        side_effect=WebsocketError,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "token": "123",
            },
        )

    assert result2["type"] == RESULT_TYPE_FORM
    assert result2["errors"] == {"base": "cannot_connect"}


async def test_validate_input(hass: HomeAssistant):
    """Test the valildate input function."""

    with pytest.raises(InvalidToken):
        with patch(
            "homeassistant.components.bluecurrent.config_flow.Client.validate_token",
            return_value=False,
        ):
            await validate_input({"token": "123"})
