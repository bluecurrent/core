"""Blue Current DataUpdateCoordinator."""

import asyncio
from contextlib import suppress
from typing import Any

from bluecurrent_api import Client
from bluecurrent_api.exceptions import RequestLimitReached, WebsocketError

from homeassistant.const import ATTR_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import DOMAIN, EVSE_ID, LOGGER, MODEL_TYPE

CHARGE_POINTS = "CHARGE_POINTS"
DATA = "data"
DELAY = 5

GRID = "GRID"
OBJECT = "object"
VALUE_TYPES = ["CH_STATUS"]


class BlueCurrentCoordinator(DataUpdateCoordinator[None]):
    """Blue Current DataUpdateCoordinator."""

    charge_points: dict[str, dict]
    grid: dict[str, Any]

    def __init__(self, hass: HomeAssistant, client: Client) -> None:
        """Init Blue Current DataUpdateCoordinator."""
        super().__init__(
            hass,
            LOGGER,
            name=DOMAIN,
        )
        self.charge_points = {}
        self.grid = {}
        self.client = client

    async def on_data(self, message: dict) -> None:
        """Handle received data."""

        object_name: str = message[OBJECT]

        # gets charge point ids
        if object_name == CHARGE_POINTS:
            charge_points_data: list = message[DATA]
            await self.handle_charge_point_data(charge_points_data)

        # gets charge point key / values
        elif object_name in VALUE_TYPES:
            value_data: dict = message[DATA]
            evse_id = value_data.pop(EVSE_ID)
            self.update_charge_point(evse_id, value_data)

        # gets grid key / values
        elif GRID in object_name:
            data: dict = message[DATA]
            self.grid = data
            self.async_set_updated_data(None)

    async def handle_charge_point_data(self, charge_points_data: list) -> None:
        """Handle incoming chargepoint data."""
        await asyncio.gather(
            *(
                self.handle_charge_point(
                    entry[EVSE_ID], entry[MODEL_TYPE], entry[ATTR_NAME]
                )
                for entry in charge_points_data
            ),
            self.client.get_grid_status(charge_points_data[0][EVSE_ID]),
        )

    async def handle_charge_point(self, evse_id: str, model: str, name: str) -> None:
        """Add the chargepoint and request their data."""
        self.add_charge_point(evse_id, model, name)
        await self.client.get_status(evse_id)

    def add_charge_point(self, evse_id: str, model: str, name: str) -> None:
        """Add a charge point to charge_points."""
        self.charge_points[evse_id] = {
            MODEL_TYPE: model,
            ATTR_NAME: name,
        }
        self.async_set_updated_data(None)

    def update_charge_point(self, evse_id: str, data: dict) -> None:
        """Update the charge point data."""
        self.charge_points[evse_id].update(data)
        self.async_set_updated_data(None)

    async def on_open(self) -> None:
        """Fetch data when connection is established."""
        await self.client.get_charge_points()

    async def run_task(self) -> None:
        """Start the receive loop."""
        try:
            while True:
                try:
                    await self.client.connect(self.on_data, self.on_open)
                except RequestLimitReached:
                    LOGGER.warning(
                        "Request limit reached. reconnecting at 00:00 (Europe/Amsterdam)"
                    )
                    delay = self.client.get_next_reset_delta().seconds
                except WebsocketError:
                    LOGGER.debug("Disconnected, retrying in background")
                    delay = DELAY

                self._on_disconnect()
                await asyncio.sleep(delay)
        finally:
            await self._disconnect()

    def _on_disconnect(self) -> None:
        """Dispatch signals to update entity states."""
        self.async_update_listeners()

    async def _disconnect(self) -> None:
        """Disconnect from the websocket."""
        with suppress(WebsocketError):
            await self.client.disconnect()
            self._on_disconnect()

    @property
    def connected(self) -> bool:
        """Returns the connection status."""
        return self.client.is_connected()
