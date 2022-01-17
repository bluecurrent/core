"""Config flow for BlueCurrent integration."""
from __future__ import annotations

import logging
from typing import Any

from bluecurrent_api import Client
from bluecurrent_api.errors import InvalidToken, NoCardsFound, WebsocketError
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_API_TOKEN, CONF_NAME
from homeassistant.data_entry_flow import FlowResult

from .const import CARD, DOMAIN

_LOGGER = logging.getLogger(__name__)

DATA_SCHEMA = vol.Schema(
    {vol.Required(CONF_API_TOKEN): str, vol.Optional("add_card"): bool}
)


async def validate_input(client: Client, api_token: str) -> None:
    """Validate the user input allows us to connect."""
    await client.validate_api_token(api_token)


async def get_charge_cards(client: Client) -> list:
    """Validate the user input allows us to connect."""
    cards: list = await client.get_charge_cards()
    return cards


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle the config flow for Blue Current."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_PUSH

    input: dict[str, Any] = {}
    client = Client()

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""

        errors = {}
        if user_input is not None:

            api_token = user_input[CONF_API_TOKEN]

            await self.async_set_unique_id(api_token)
            self._abort_if_unique_id_configured()

            try:
                await validate_input(self.client, api_token)
            except WebsocketError:
                errors["base"] = "cannot_connect"
            except InvalidToken:
                errors["base"] = "invalid_token"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

            if not errors:
                self.input[CONF_API_TOKEN] = api_token

                if user_input.get("add_card"):
                    return await self.async_step_card()
                else:
                    # maybe renamed to BCU_HA
                    self.input[CARD] = "BCU_APP"
                    return self.async_create_entry(
                        title=user_input[CONF_API_TOKEN][:5], data=self.input
                    )

        return self.async_show_form(
            step_id="user", data_schema=DATA_SCHEMA, errors=errors
        )

    async def async_step_card(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the card step."""
        errors = {}
        api_token = self.input[CONF_API_TOKEN]
        try:
            cards = await get_charge_cards(self.client)
        except WebsocketError:
            errors["base"] = "cannot_connect"
        except NoCardsFound:
            errors["base"] = "no_cards_found"

        if not errors:
            card_names = [card[CONF_NAME] for card in cards]
            card_schema = vol.Schema({vol.Required(CARD): vol.In(card_names)})

            def check_card(card: dict) -> bool:
                assert user_input is not None
                return bool(card[CONF_NAME] == user_input[CARD])

            if user_input is not None:

                selected_card = list(filter(check_card, cards))[0]

                self.input[CARD] = selected_card["uid"]
                return self.async_create_entry(title=api_token[:5], data=self.input)

            return self.async_show_form(step_id=CARD, data_schema=card_schema)

        return self.async_show_form(
            step_id="user", data_schema=DATA_SCHEMA, errors=errors
        )

    async def async_step_import(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle a flow initiated by configuration file."""
        return await self.async_step_user(user_input)
