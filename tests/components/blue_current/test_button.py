"""The tests for Blue Current buttons."""

import pytest
from syrupy.assertion import SnapshotAssertion

from homeassistant.components.blue_current.const import (
    DELAYED_CHARGING,
    PRICE_BASED_CHARGING,
    SMART_CHARGING,
    VALUE,
)
from homeassistant.components.button import DOMAIN as BUTTON_DOMAIN, SERVICE_PRESS
from homeassistant.const import ATTR_ENTITY_ID, STATE_UNKNOWN, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from . import DEFAULT_CHARGE_POINT, init_integration

from tests.common import MockConfigEntry, snapshot_platform

charge_point_buttons = [
    "stop_charge_session",
    "reset",
    "reboot",
    "boost_charge_session",
]


async def test_buttons_created(
    hass: HomeAssistant,
    snapshot: SnapshotAssertion,
    config_entry: MockConfigEntry,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test if all buttons are created."""
    await init_integration(hass, config_entry, Platform.BUTTON)

    await snapshot_platform(hass, entity_registry, snapshot, config_entry.entry_id)


@pytest.mark.freeze_time("2023-01-13 12:00:00+00:00")
async def test_charge_point_buttons(
    hass: HomeAssistant, config_entry: MockConfigEntry
) -> None:
    """Test the underlying charge point buttons."""
    await init_integration(hass, config_entry, Platform.BUTTON)

    for button in charge_point_buttons:
        state = hass.states.get(f"button.101_{button}")
        assert state is not None
        assert state.state == STATE_UNKNOWN

        await hass.services.async_call(
            BUTTON_DOMAIN,
            SERVICE_PRESS,
            {ATTR_ENTITY_ID: f"button.101_{button}"},
            blocking=True,
        )

        state = hass.states.get(f"button.101_{button}")
        assert state
        assert state.state == "2023-01-13T12:00:00+00:00"


async def test_boost_button_without_smart_charging(
    hass: HomeAssistant, config_entry: MockConfigEntry
) -> None:
    """Test boost button functionality."""
    charge_point = DEFAULT_CHARGE_POINT.copy()
    integration = await init_integration(
        hass, config_entry, Platform.BUTTON, charge_point
    )
    client = integration[0]

    await hass.services.async_call(
        BUTTON_DOMAIN,
        SERVICE_PRESS,
        {ATTR_ENTITY_ID: "button.101_boost_charge_session"},
        blocking=True,
    )

    client.override_price_based_charging_profile.assert_not_called()
    client.override_delayed_charging_profile.assert_not_called()

    charge_point[SMART_CHARGING] = True
    charge_point[PRICE_BASED_CHARGING] = {VALUE: True}
    charge_point[DELAYED_CHARGING] = {VALUE: False}

    await hass.services.async_call(
        BUTTON_DOMAIN,
        SERVICE_PRESS,
        {ATTR_ENTITY_ID: "button.101_boost_charge_session"},
        blocking=True,
    )

    client.override_price_based_charging_profile.assert_called_once()
    client.override_delayed_charging_profile.assert_not_called()

    await hass.services.async_call(
        BUTTON_DOMAIN,
        SERVICE_PRESS,
        {ATTR_ENTITY_ID: "button.101_boost_charge_session"},
        blocking=True,
    )

    client.override_price_based_charging_profile.reset_mock()

    charge_point[PRICE_BASED_CHARGING] = {VALUE: False}
    charge_point[DELAYED_CHARGING] = {VALUE: True}

    await hass.services.async_call(
        BUTTON_DOMAIN,
        SERVICE_PRESS,
        {ATTR_ENTITY_ID: "button.101_boost_charge_session"},
        blocking=True,
    )

    client.override_price_based_charging_profile.assert_not_called()
    client.override_delayed_charging_profile.assert_called_once()
