"""Actions for Blue Current integration."""

from datetime import timedelta
import re
from typing import Any

from bluecurrent_api import Client
from bluecurrent_api.types import (
    OverrideCurrentPayload,
)

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import device_registry as dr

from .const import (
    CHARGE_POINTS,
    CURRENT,
    DELAYED_CHARGING,
    DEVICE_IDS,
    DOMAIN,
    END_TIME,
    FRIDAY,
    MONDAY,
    OVERRIDE_END_DAYS,
    OVERRIDE_END_TIME,
    OVERRIDE_START_DAYS,
    OVERRIDE_START_TIME,
    PRICE_BASED_CHARGING,
    SATURDAY,
    SMART_CHARGING,
    START_TIME,
    SUNDAY,
    THURSDAY,
    TUESDAY,
    VALUE,
    WEDNESDAY,
)


async def set_price_based_charging(
    hass: HomeAssistant,
    client: Client,
    charge_points: dict[str, dict],
    service_call: ServiceCall,
) -> None:
    """Set smart charging profile."""
    # device_id = service_call.data["device_id"]
    # expected_departure_time = service_call.data["expected_departure_time"]
    # if not check_time(expected_departure_time):
    #     raise ServiceValidationError("Invalid time format")
    #
    # expected_departure_time = timedelta_to_str(expected_departure_time)
    # expected_charging_session_size = service_call.data["expected_charging_session_size"]
    # immediately_charge = service_call.data["immediately_charge"]
    #
    # device = dr.async_get(hass).devices[device_id]
    # evse_id = list(device.identifiers)[0][1]
    #
    # profile = get_current_smart_charging_profile(charge_points[evse_id])
    # await switch_profile_if_needed(evse_id, client, charge_points, profile, PRICE_BASED_CHARGING)
    #
    # await client.set_price_based_settings(
    #     evse_id,
    #     expected_departure_time,
    #     expected_charging_session_size,
    #     immediately_charge,
    # )


async def set_delayed_charging(
    hass: HomeAssistant,
    client: Client,
    charge_points: dict[str, dict],
    service_call: ServiceCall,
) -> None:
    """Set price based charging."""
    # device_id = service_call.data["device_id"]
    # device = dr.async_get(hass).devices[device_id]
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
    # day_numbers = [days_to_number[day] for day in selected_days]
    # start_time = service_call.data["start_time"]
    # end_time = service_call.data["end_time"]
    # if not check_time(start_time) or not check_time(end_time):
    #     raise ServiceValidationError("Invalid time format")
    #
    # start_time = timedelta_to_str(start_time)
    # end_time = timedelta_to_str(end_time)
    #
    # evse_id = list(device.identifiers)[0][1]
    #
    # profile = get_current_smart_charging_profile(charge_points[evse_id])
    # await switch_profile_if_needed(evse_id, client, charge_points, profile, DELAYED_CHARGING)
    #
    # await client.set_delayed_charging_settings(
    #     evse_id, day_numbers, start_time, end_time
    # )


async def switch_profile_if_needed(
    evse_id: str,
    client: Client,
    charge_points: dict[str, dict],
    current_profile: str | None,
    new_profile: str,
) -> None:
    """Change to a new smart charging profile. Turn the previous profile off when this profile was enabled."""
    # change_profile_functions = {
    #     PRICE_BASED_CHARGING: client.set_price_based_charging,
    #     DELAYED_CHARGING: client.set_delayed_charging,
    # }
    #
    # if current_profile != new_profile:
    #     await change_profile_functions[new_profile](evse_id, True)
    #     charge_points[evse_id][new_profile][VALUE] = True
    #     if current_profile is not None:
    #         charge_points[evse_id][current_profile][VALUE] = False
    #         await change_profile_functions[current_profile](evse_id, False)
    #


async def set_user_override(
    hass: HomeAssistant,
    client: Client,
    charge_points: dict[str, dict],
    schedules: dict[str, Any],
    service_call: ServiceCall,
) -> None:
    """Set user override action."""
    device_ids = service_call.data[DEVICE_IDS]
    devices = [dr.async_get(hass).devices[device_id] for device_id in device_ids]

    current = service_call.data[CURRENT]

    override_start_time = service_call.data[OVERRIDE_START_TIME]
    override_start_days = service_call.data[OVERRIDE_START_DAYS]

    override_end_time = service_call.data[OVERRIDE_END_TIME]
    override_end_days = service_call.data[OVERRIDE_END_DAYS]

    days_to_code = {
        MONDAY: "MO",
        TUESDAY: "TU",
        WEDNESDAY: "WE",
        THURSDAY: "TH",
        FRIDAY: "FR",
        SATURDAY: "SA",
        SUNDAY: "SU",
    }

    start_day_code = [days_to_code[day] for day in override_start_days]
    end_day_code = [days_to_code[day] for day in override_end_days]

    start_time = timedelta_to_str(override_start_time)
    end_time = timedelta_to_str(override_end_time)

    evse_ids = [
        next(
            identifier[1]
            for identifier in device.identifiers
            if identifier[0] == DOMAIN
        )
        for device in devices
    ]

    existing_schedule_ids = list(
        {
            schedule_id
            for schedule_id, schedule in schedules.items()
            if bool(set(schedule["charge_points"]) & set(evse_ids))
        }
    )

    # existing_schedule_ids = list({charge_points[evse_id].get("schedule_id") for evse_id in evse_ids})

    override_current_payload = OverrideCurrentPayload(
        chargepoints=evse_ids,
        overridestarttime=start_time,
        overridestartdays=start_day_code,
        overridestoptime=end_time,
        overridestopdays=end_day_code,
        overridevalue=current,
    )

    # When all charge points in the action has a schedule_id of None, no charge point has a schedule yet.
    if len(existing_schedule_ids) == 0:
        # Create schedule with new data.
        await client.set_user_override_current(override_current_payload)
        # print("[0] Created new schedule " + str(override_current_payload))
    # When the schedule id length is but not None, all charge points have the same schedule id.
    elif len(existing_schedule_ids) == 1:
        # Update schedule with new data.
        await client.edit_user_override_current(
            existing_schedule_ids[0], override_current_payload
        )
        # print("[1] edit user override for schedule: " + str(existing_schedule_ids[0]))
    # The charge points in the action have different or no schedule id.
    else:
        # Remove charge points from schedule when they have a schedule ID
        for schedule_id in existing_schedule_ids:
            schedules[schedule_id][CHARGE_POINTS] = [
                i for i in schedules[schedule_id][CHARGE_POINTS] if i not in evse_ids
            ]
            # print(
            #     "[2] Removing existing schedule with ID "
            #     + schedule_id
            #     + " "
            #     + str(schedules[schedule_id]["charge_points"])
            # )

            if len(schedules[schedule_id][CHARGE_POINTS]) == 0:
                schedules.pop(schedule_id)
                # print(
                #     "[3] Schedule with no charge points anymore removed " + schedule_id
                # )
                await client.clear_user_override_current(schedule_id)
            else:
                schedule = schedules[schedule_id]
                # Update the schedule so that the user is removed.
                await client.edit_user_override_current(
                    schedule_id,
                    OverrideCurrentPayload(
                        chargepoints=schedule[CHARGE_POINTS],
                        overridestarttime=schedule[START_TIME],
                        overridestartdays=schedule[OVERRIDE_START_DAYS],
                        overridestoptime=schedule[END_TIME],
                        overridestopdays=schedule[OVERRIDE_END_DAYS],
                        overridevalue=schedule["current"],
                    ),
                )

        # print("[4] Set new override current " + str(override_current_payload))
        await client.set_user_override_current(override_current_payload)


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


def timedelta_to_str(time: timedelta) -> str:
    """Convert time delta to an acceptable string format."""
    seconds = int(time.total_seconds())
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    return f"{hours:02d}:{minutes:02d}"
