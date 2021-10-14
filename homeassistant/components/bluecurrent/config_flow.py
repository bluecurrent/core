"""Config flow for BlueCurrent integration."""
from __future__ import annotations

import logging
from typing import Any

from bluecurrent_api import Client
from bluecurrent_api.errors import InvalidToken, WebsocketError
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_TOKEN

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_TOKEN): str,
    }
)


async def validate_input(data: dict) -> dict[str, Any]:
    """Validate the user input allows us to connect.

    Data has the keys from DATA_SCHEMA with values provided by the user.
    """

    client = Client()
    result = await client.validate_token(data[CONF_TOKEN])
    if result is False:
        raise InvalidToken

    return {"title": data[CONF_TOKEN][:5]}

    # Return info that you want to store in the config entry.
    # "Title" is what is displayed to the user for this hub device
    # It is stored internally in HA as part of the device config.
    # See `async_step_user` below for how this is used


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Hello World."""

    VERSION = 1
    # Pick one of the available connection classes in homeassistant/config_entries.py
    # This tells HA if it should be asking for updates, or it'll be notified of updates
    # automatically. This example uses PUSH, as the dummy hub will notify HA of
    # changes.
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_PUSH

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""

        errors = {}
        if user_input is not None:

            await self.async_set_unique_id(user_input[CONF_TOKEN])
            self._abort_if_unique_id_configured()

            try:
                info = await validate_input(user_input)
                return self.async_create_entry(title=info["title"], data=user_input)

            except WebsocketError:
                errors["base"] = "cannot_connect"
            except InvalidToken:
                errors["token"] = "invalid_token"

        return self.async_show_form(
            step_id="user", data_schema=DATA_SCHEMA, errors=errors
        )
