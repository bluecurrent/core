"""Support for command line notification services."""

from __future__ import annotations

import logging
import subprocess
from typing import Any

from homeassistant.components.notify import BaseNotificationService
from homeassistant.const import CONF_COMMAND
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.util.process import kill_subprocess

from .const import CONF_COMMAND_TIMEOUT, LOGGER
from .utils import render_template_args

_LOGGER = logging.getLogger(__name__)


def get_service(
    hass: HomeAssistant,
    config: ConfigType,
    discovery_info: DiscoveryInfoType | None = None,
) -> CommandLineNotificationService | None:
    """Get the Command Line notification service."""
    if not discovery_info:
        return None

    notify_config = discovery_info
    command: str = notify_config[CONF_COMMAND]
    timeout: int = notify_config[CONF_COMMAND_TIMEOUT]

    return CommandLineNotificationService(command, timeout)


class CommandLineNotificationService(BaseNotificationService):
    """Implement the notification service for the Command Line service."""

    def __init__(self, command: str, timeout: int) -> None:
        """Initialize the service."""
        self.command = command
        self._timeout = timeout

    def send_message(self, message: str = "", **kwargs: Any) -> None:
        """Send a message to a command line."""
        if not (command := render_template_args(self.hass, self.command)):
            return

        LOGGER.debug("Running with message: %s", message)

        with subprocess.Popen(  # noqa: S602 # shell by design
            command,
            universal_newlines=True,
            stdin=subprocess.PIPE,
            close_fds=False,  # required for posix_spawn
            shell=True,
        ) as proc:
            try:
                proc.communicate(input=message, timeout=self._timeout)
                if proc.returncode != 0:
                    _LOGGER.error(
                        "Command failed (with return code %s): %s",
                        proc.returncode,
                        command,
                    )
            except subprocess.TimeoutExpired:
                _LOGGER.error("Timeout for command: %s", command)
                kill_subprocess(proc)
            except subprocess.SubprocessError:
                _LOGGER.error("Error trying to exec command: %s", command)
