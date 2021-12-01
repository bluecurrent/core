"""Config flow for BlueCurrent integration."""
from __future__ import annotations

import logging
from typing import Any

from bluecurrent_api import Client
from bluecurrent_api.errors import InvalidToken, WebsocketError
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_TOKEN
from homeassistant.data_entry_flow import FlowResult

from .const import CARD, DOMAIN, URL

_LOGGER = logging.getLogger(__name__)

DATA_SCHEMA = vol.Schema(
    {vol.Required(CONF_TOKEN): str, vol.Optional("add_card"): bool}
)


async def validate_input(data: dict) -> None:
    """Validate the user input allows us to connect."""
    client = Client()
    result = await client.validate_token(data[CONF_TOKEN], URL)
    if result is False:
        raise InvalidToken


async def get_charge_cards(token: str) -> list:
    """Validate the user input allows us to connect."""

    # can have websocket error or no cards?
    client = Client()
    result: dict[str, list] = await client.get_charge_cards(token, URL)
    return result["data"]


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle the config flow for Blue Current."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_PUSH

    input: dict[str, Any] = {}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""

        errors = {}
        if user_input is not None:

            await self.async_set_unique_id(user_input[CONF_TOKEN])
            self._abort_if_unique_id_configured()

            try:
                await validate_input(user_input)
            except WebsocketError:
                errors["base"] = "cannot_connect"
            except InvalidToken:
                errors["base"] = "invalid_token"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

            if not errors:
                self.input[CONF_TOKEN] = user_input[CONF_TOKEN]

                if user_input.get("add_card"):
                    return await self.async_step_card()
                else:
                    # maybe renamed to BCU_HA
                    self.input[CARD] = {"card_id": "BCU_APP"}
                    return self.async_create_entry(
                        title=user_input[CONF_TOKEN][:5], data=self.input
                    )

        return self.async_show_form(
            step_id="user", data_schema=DATA_SCHEMA, errors=errors
        )

    async def async_step_card(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the card step."""

        token = self.input["token"]

        cards = await get_charge_cards(token)
        card_names = [card["name"] for card in cards]
        card_schema = vol.Schema({vol.Required(CARD): vol.In(card_names)})

        def check_card(card: dict) -> bool:
            assert user_input is not None
            return bool(card["name"] == user_input["card"])

        if user_input is not None:

            selected_card = list(filter(check_card, cards))[0]

            self.input[CARD] = selected_card
            return self.async_create_entry(title=token[:5], data=self.input)

        return self.async_show_form(step_id="card", data_schema=card_schema, errors={})

    async def async_step_import(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle a flow initiated by configuration file."""
        return await self.async_step_user(user_input)
