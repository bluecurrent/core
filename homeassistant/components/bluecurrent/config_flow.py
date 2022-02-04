"""Config flow for BlueCurrent integration."""
from __future__ import annotations

from typing import Any

from bluecurrent_api import Client
from bluecurrent_api.errors import InvalidToken, WebsocketError
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_API_TOKEN
from homeassistant.data_entry_flow import FlowResult

from .const import DOMAIN, LOGGER

DATA_SCHEMA = vol.Schema({vol.Required(CONF_API_TOKEN): str})


async def validate_input(api_token: str) -> None:
    """Validate the api token."""
    client = Client()
    await client.validate_api_token(api_token)


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

            api_token = user_input[CONF_API_TOKEN]
            await self.async_set_unique_id(api_token)
            self._abort_if_unique_id_configured()

            try:
                await validate_input(api_token)
            except WebsocketError:
                errors["base"] = "cannot_connect"
            except InvalidToken:
                errors["base"] = "invalid_token"
            except Exception:  # pylint: disable=broad-except
                LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

            if not errors:
                self.input[CONF_API_TOKEN] = api_token
                return self.async_create_entry(
                    title=user_input[CONF_API_TOKEN][:5], data=self.input
                )

        return self.async_show_form(
            step_id="user", data_schema=DATA_SCHEMA, errors=errors
        )

    async def async_step_import(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle a flow initiated by the configuration file."""
        return await self.async_step_user(user_input)
