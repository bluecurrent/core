"""Actions for Blue Current integration."""

import re
from typing import Any

from bluecurrent_api import Client

from homeassistant.core import ServiceCall

from . import Connector
from .const import DELAYED_CHARGING, PRICE_BASED_CHARGING, SMART_CHARGING, VALUE

# from homeassistant.exceptions import ServiceValidationError
# from homeassistant.helpers import device_registry as dr


async def set_price_based_charging(
    connector: Connector, service_call: ServiceCall
) -> None:
    """Set smart charging profile."""

    # def check_session_size(size: int) -> bool:
    #     """Check if the given session size is between or equal to 1 and 80."""
    #     return 1 <= size <= 80
    #
    # client = connector.client
    #
    # device_id = service_call.data["device_id"]
    # expected_departure_time = service_call.data["expected_departure_time"]
    # if not check_time(expected_departure_time):
    #     raise ServiceValidationError
    #
    # expected_departure_time = remove_seconds(expected_departure_time)
    # expected_charging_session_size = service_call.data["expected_charging_session_size"]
    # immediately_charge = service_call.data["immediately_charge"]
    #
    # if not check_session_size(expected_charging_session_size) or not check_session_size(
    #     immediately_charge
    # ):
    #     raise ServiceValidationError
    #
    # device = dr.async_get(connector.hass).devices[device_id]
    # evse_id = list(device.identifiers)[0][1]
    #
    # profile = get_current_smart_charging_profile(connector.charge_points[evse_id])
    # await switch_profile_if_needed(evse_id, client, profile, PRICE_BASED_CHARGING)
    #
    # await client.set_price_based_settings(
    #     evse_id,
    #     expected_departure_time,
    #     expected_charging_session_size,
    #     immediately_charge,
    # )


async def set_delayed_charging(connector: Connector, service_call: ServiceCall) -> None:
    """Set price based charging."""
    # client = connector.client
    #
    # device_id = service_call.data["device_id"]
    # device = dr.async_get(connector.hass).devices[device_id]
    #
    # days_to_number = {
    #     "monday": 1,
    #     "tuesday": 2,
    #     "wednesday": 3,
    #     "thursday": 4,
    #     "friday": 5,
    #     "saturday": 6,
    #     "sunday": 7,
    # }
    #
    # selected_days = service_call.data["days"]
    #
    # day_numbers = list(map(lambda day: days_to_number[day], selected_days))
    # start_time: str = service_call.data["start_time"]
    # end_time = service_call.data["end_time"]
    # if not check_time(start_time) or not check_time(end_time):
    #     raise ServiceValidationError
    #
    # start_time = remove_seconds(start_time)
    # end_time = remove_seconds(end_time)
    #
    # evse_id = list(device.identifiers)[0][1]
    #
    # profile = get_current_smart_charging_profile(connector.charge_points[evse_id])
    # await switch_profile_if_needed(evse_id, client, profile, DELAYED_CHARGING)
    #
    # await client.save_scheduled_delayed_charging(
    #     evse_id, day_numbers, start_time, end_time
    # )


async def switch_profile_if_needed(
    evse_id: str, client: Client, current_profile: str | None, new_profile: str
) -> None:
    """Change to a new smart charging profile. Turn the previous profile off when this profile was enabled."""
    # change_profile_functions = {
    #     PRICE_BASED_CHARGING: client.set_price_based_charging,
    #     DELAYED_CHARGING: client.set_delayed_charging,
    # }
    #
    # if current_profile != new_profile:
    #     await change_profile_functions[new_profile](evse_id, True)
    #     if current_profile is not None:
    #         await change_profile_functions[current_profile](evse_id, False)


def get_current_smart_charging_profile(charge_point: dict[str, Any]) -> str | None:
    """Get the currently active smart charging profile for the given charge point."""
    if charge_point[SMART_CHARGING]:
        if charge_point[PRICE_BASED_CHARGING][VALUE]:
            return PRICE_BASED_CHARGING
        if charge_point[DELAYED_CHARGING][VALUE]:
            return DELAYED_CHARGING
    return None


def check_time(time: str) -> bool:
    """Check if time format is correctly. Seconds are optional, because they are not send to the API."""
    return bool(re.compile("^[0-2][0-9]:[0-5][0-9](:[0-5][0-9])*$").match(time))


def remove_seconds(time: str) -> str:
    """Remove the seconds from the time, when in the time string."""
    if time.count(":") == 2:
        return time.rsplit(":", 1)[0]
    return time
