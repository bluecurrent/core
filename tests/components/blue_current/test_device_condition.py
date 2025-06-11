"""The tests for Blue Current device conditions."""

from __future__ import annotations

from pytest_unordered import unordered

from homeassistant.components import automation
from homeassistant.components.blue_current import DOMAIN
from homeassistant.components.device_automation import DeviceAutomationType
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import device_registry as dr, entity_registry as er
from homeassistant.setup import async_setup_component

from tests.common import MockConfigEntry, async_get_device_automations

ACTIVITY_TYPES = ["available", "charging", "unavailable", "error", "offline"]
VEHICLE_STATUS_TYPES = [
    "standby",
    "vehicle_detected",
    "ready",
    "no_power",
    "vehicle_error",
]


async def test_get_conditions(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test we get the expected conditions from blue current integration."""
    config_entry = MockConfigEntry(domain=DOMAIN, data={})
    config_entry.add_to_hass(hass)
    evse_id = "101"
    device_entry = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        identifiers={(DOMAIN, evse_id)},
    )
    entity_registry.async_get_or_create(
        DOMAIN, "activity", "101", device_id=device_entry.id
    )
    entity_registry.async_get_or_create(
        DOMAIN, "vehicle_status", "101", device_id=device_entry.id
    )

    base_condition = {
        "condition": "device",
        "domain": DOMAIN,
        "device_id": device_entry.id,
        "metadata": {},
    }

    expected_conditions_activity = [
        {"entity_id": "sensor.101_activity", "type": t, **base_condition}
        for t in ACTIVITY_TYPES
    ]

    expected_conditions_vehicle_status = [
        {"entity_id": "sensor.101_vehicle_status", "type": t, **base_condition}
        for t in VEHICLE_STATUS_TYPES
    ]

    conditions = await async_get_device_automations(
        hass, DeviceAutomationType.CONDITION, device_entry.id
    )

    assert conditions == unordered(
        expected_conditions_activity + expected_conditions_vehicle_status
    )


async def test_if_state_for_activity(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    config_entry: MockConfigEntry,
    service_calls: list[ServiceCall],
) -> None:
    """Test for turn_on and turn_off conditions for activity."""
    config_entry.add_to_hass(hass)

    device_entry = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        identifiers={(DOMAIN, "101")},
    )

    assert await async_setup_component(
        hass,
        automation.DOMAIN,
        {
            automation.DOMAIN: [
                {
                    "trigger": {"platform": "event", "event_type": f"{t}-event"},
                    "condition": [
                        {
                            "condition": "device",
                            "domain": DOMAIN,
                            "device_id": device_entry.id,
                            "entity_id": "sensor.101_activity",
                            "type": t,
                        }
                    ],
                    "action": {
                        "service": "test.automation",
                        "data_template": {
                            "some": t
                            + " - {{ trigger.platform }} - {{ trigger.event.event_type }}"
                        },
                    },
                }
                for t in ACTIVITY_TYPES
            ]
        },
    )

    hass.states.async_set("sensor.101_activity", "available")
    hass.bus.async_fire("available-event")
    await hass.async_block_till_done()
    assert len(service_calls) == 1
    assert service_calls[0].data["some"] == "available - event - available-event"

    hass.states.async_set("sensor.101_activity", "charging")
    hass.bus.async_fire("charging-event")
    await hass.async_block_till_done()
    assert len(service_calls) == 2
    assert service_calls[1].data["some"] == "charging - event - charging-event"

    hass.states.async_set("sensor.101_activity", "unavailable")
    hass.bus.async_fire("unavailable-event")
    await hass.async_block_till_done()
    assert len(service_calls) == 3
    assert service_calls[2].data["some"] == "unavailable - event - unavailable-event"

    hass.states.async_set("sensor.101_activity", "error")
    hass.bus.async_fire("error-event")
    await hass.async_block_till_done()
    assert len(service_calls) == 4
    assert service_calls[3].data["some"] == "error - event - error-event"

    hass.states.async_set("sensor.101_activity", "offline")
    hass.bus.async_fire("offline-event")
    await hass.async_block_till_done()
    assert len(service_calls) == 5
    assert service_calls[4].data["some"] == "offline - event - offline-event"


async def test_if_state_for_vehicle_status(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    config_entry: MockConfigEntry,
    service_calls: list[ServiceCall],
) -> None:
    """Test for turn_on and turn_off conditions for vehicle status."""
    config_entry.add_to_hass(hass)

    device_entry = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        identifiers={(DOMAIN, "101")},
    )

    assert await async_setup_component(
        hass,
        automation.DOMAIN,
        {
            automation.DOMAIN: [
                {
                    "trigger": {"platform": "event", "event_type": f"{t}-event"},
                    "condition": [
                        {
                            "condition": "device",
                            "domain": DOMAIN,
                            "device_id": device_entry.id,
                            "entity_id": "sensor.101_vehicle_status",
                            "type": t,
                        }
                    ],
                    "action": {
                        "service": "test.automation",
                        "data_template": {
                            "some": t
                            + " - {{ trigger.platform }} - {{ trigger.event.event_type }}"
                        },
                    },
                }
                for t in VEHICLE_STATUS_TYPES
            ]
        },
    )

    hass.states.async_set("sensor.101_vehicle_status", "standby")
    hass.bus.async_fire("standby-event")
    await hass.async_block_till_done()
    assert len(service_calls) == 1
    assert service_calls[0].data["some"] == "standby - event - standby-event"

    hass.states.async_set("sensor.101_vehicle_status", "vehicle_detected")
    hass.bus.async_fire("vehicle_detected-event")
    await hass.async_block_till_done()
    assert len(service_calls) == 2
    assert (
        service_calls[1].data["some"]
        == "vehicle_detected - event - vehicle_detected-event"
    )

    hass.states.async_set("sensor.101_vehicle_status", "ready")
    hass.bus.async_fire("ready-event")
    await hass.async_block_till_done()
    assert len(service_calls) == 3
    assert service_calls[2].data["some"] == "ready - event - ready-event"

    hass.states.async_set("sensor.101_vehicle_status", "no_power")
    hass.bus.async_fire("no_power-event")
    await hass.async_block_till_done()
    assert len(service_calls) == 4
    assert service_calls[3].data["some"] == "no_power - event - no_power-event"

    hass.states.async_set("sensor.101_vehicle_status", "vehicle_error")
    hass.bus.async_fire("vehicle_error-event")
    await hass.async_block_till_done()
    assert len(service_calls) == 5
    assert (
        service_calls[4].data["some"] == "vehicle_error - event - vehicle_error-event"
    )
