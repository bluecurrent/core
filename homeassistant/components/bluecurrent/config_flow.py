"""Config flow for BlueCurrent integration."""
from __future__ import annotations

import logging
from typing import Any

from bluecurrent_api import Client
from bluecurrent_api.errors import InvalidToken, WebsocketError
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_TOKEN

from .const import DOMAIN, URL

_LOGGER = logging.getLogger(__name__)

DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_TOKEN): str,
    }
)


async def validate_input(data: dict) -> None:
    """Validate the user input allows us to connect."""
    client = Client()
    result = await client.validate_token(data[CONF_TOKEN], URL)
    if result is False:
        raise InvalidToken


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle the config flow for Blue Current."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_PUSH

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
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

                return self.async_create_entry(
                    title=user_input[CONF_TOKEN][:5], data=user_input
                )

        return self.async_show_form(
            step_id="user", data_schema=DATA_SCHEMA, errors=errors
        )
