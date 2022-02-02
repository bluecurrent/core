"""The tests for BlueCurrent device conditions."""
from __future__ import annotations

import pytest

from homeassistant.components import automation
from homeassistant.components.bluecurrent import DOMAIN
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import device_registry, entity_registry
from homeassistant.setup import async_setup_component

from tests.common import (
    MockConfigEntry,
    assert_lists_same,
    async_get_device_automations,
    async_mock_service,
    mock_device_registry,
    mock_registry,
)


@pytest.fixture
def device_reg(hass: HomeAssistant) -> device_registry.DeviceRegistry:
    """Return an empty, loaded, registry."""
    return mock_device_registry(hass)


@pytest.fixture
def entity_reg(hass: HomeAssistant) -> entity_registry.EntityRegistry:
    """Return an empty, loaded, registry."""
    return mock_registry(hass)


@pytest.fixture
def calls(hass: HomeAssistant) -> list[ServiceCall]:
    """Track calls to a mock service."""
    return async_mock_service(hass, "test", "automation")


async def test_get_conditions(
    hass: HomeAssistant,
    device_reg: device_registry.DeviceRegistry,
    entity_reg: entity_registry.EntityRegistry,
) -> None:
    """Test we get the expected conditions from a bluecurrent."""
    config_entry = MockConfigEntry(domain=DOMAIN, data={})
    config_entry.add_to_hass(hass)
    evse_id = "101"
    device_entry = device_reg.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        identifiers={(DOMAIN, evse_id)},
    )
    entity_reg.async_get_or_create(DOMAIN, "activity", "101", device_id=device_entry.id)
    entity_reg.async_get_or_create(
        DOMAIN, "vehicle_status", "101", device_id=device_entry.id
    )
    expected_conditions = [
        {
            "condition": "device",
            "domain": DOMAIN,
            "device_id": device_entry.id,
            "entity_id": "sensor.activity_101",
            "type": "available",
        },
        {
            "condition": "device",
            "domain": DOMAIN,
            "device_id": device_entry.id,
            "entity_id": "sensor.activity_101",
            "type": "charging",
        },
        {
            "condition": "device",
            "domain": DOMAIN,
            "device_id": device_entry.id,
            "entity_id": "sensor.activity_101",
            "type": "unavailable",
        },
        {
            "condition": "device",
            "domain": DOMAIN,
            "device_id": device_entry.id,
            "entity_id": "sensor.activity_101",
            "type": "error",
        },
        {
            "condition": "device",
            "domain": DOMAIN,
            "device_id": device_entry.id,
            "entity_id": "sensor.activity_101",
            "type": "offline",
        },
        {
            "condition": "device",
            "domain": DOMAIN,
            "device_id": device_entry.id,
            "entity_id": "sensor.vehicle_status_101",
            "type": "standby",
        },
        {
            "condition": "device",
            "domain": DOMAIN,
            "device_id": device_entry.id,
            "entity_id": "sensor.vehicle_status_101",
            "type": "vehicle_detected",
        },
        {
            "condition": "device",
            "domain": DOMAIN,
            "device_id": device_entry.id,
            "entity_id": "sensor.vehicle_status_101",
            "type": "ready",
        },
        {
            "condition": "device",
            "domain": DOMAIN,
            "device_id": device_entry.id,
            "entity_id": "sensor.vehicle_status_101",
            "type": "with_ventilation",
        },
        {
            "condition": "device",
            "domain": DOMAIN,
            "device_id": device_entry.id,
            "entity_id": "sensor.vehicle_status_101",
            "type": "no_power",
        },
        {
            "condition": "device",
            "domain": DOMAIN,
            "device_id": device_entry.id,
            "entity_id": "sensor.vehicle_status_101",
            "type": "vehicle_error",
        },
    ]
    conditions = await async_get_device_automations(hass, "condition", device_entry.id)
    assert_lists_same(conditions, expected_conditions)


async def test_if_actvivity_state(
    hass: HomeAssistant, calls: list[ServiceCall]
) -> None:
    """Test for activity condition."""

    assert await async_setup_component(
        hass,
        automation.DOMAIN,
        {
            automation.DOMAIN: [
                {
                    "trigger": {"platform": "event", "event_type": event_type},
                    "condition": [
                        {
                            "condition": "device",
                            "domain": DOMAIN,
                            "device_id": "",
                            "entity_id": "sensor.activity_101",
                            "type": activity_type,
                        }
                    ],
                    "action": {
                        "service": "test.automation",
                        "data_template": {"some": f"{activity_type} - {event_type}"},
                    },
                }
                for activity_type, event_type in (
                    ("available", "test_event_1"),
                    ("charging", "test_event_2"),
                    ("unavailable", "test_event_3"),
                    ("error", "test_event_4"),
                    ("offline", "test_event_5"),
                )
            ]
        },
    )

    hass.states.async_set("sensor.activity_101", "available")
    for i in range(1, 6):
        hass.bus.async_fire(f"test_event_{i}")
    await hass.async_block_till_done()
    assert len(calls) == 1
    assert calls[0].data["some"] == "available - test_event_1"

    hass.states.async_set("sensor.activity_101", "charging")
    for i in range(1, 6):
        hass.bus.async_fire(f"test_event_{i}")
    await hass.async_block_till_done()
    assert len(calls) == 2
    assert calls[1].data["some"] == "charging - test_event_2"

    hass.states.async_set("sensor.activity_101", "unavailable")
    for i in range(1, 6):
        hass.bus.async_fire(f"test_event_{i}")
    await hass.async_block_till_done()
    assert len(calls) == 3
    assert calls[2].data["some"] == "unavailable - test_event_3"

    hass.states.async_set("sensor.activity_101", "error")
    for i in range(1, 6):
        hass.bus.async_fire(f"test_event_{i}")
    await hass.async_block_till_done()
    assert len(calls) == 4
    assert calls[3].data["some"] == "error - test_event_4"

    hass.states.async_set("sensor.activity_101", "offline")
    for i in range(1, 6):
        hass.bus.async_fire(f"test_event_{i}")
    await hass.async_block_till_done()
    assert len(calls) == 5
    assert calls[4].data["some"] == "offline - test_event_5"


async def test_if_vehicle_status_state(
    hass: HomeAssistant, calls: list[ServiceCall]
) -> None:
    """Test for vehicle_status condition."""

    assert await async_setup_component(
        hass,
        automation.DOMAIN,
        {
            automation.DOMAIN: [
                {
                    "trigger": {"platform": "event", "event_type": event_type},
                    "condition": [
                        {
                            "condition": "device",
                            "domain": DOMAIN,
                            "device_id": "",
                            "entity_id": "sensor.vehicle_status_101",
                            "type": activity_type,
                        }
                    ],
                    "action": {
                        "service": "test.automation",
                        "data_template": {"some": f"{activity_type} - {event_type}"},
                    },
                }
                for activity_type, event_type in (
                    ("standby", "test_event_1"),
                    ("vehicle_detected", "test_event_2"),
                    ("ready", "test_event_3"),
                    ("with_ventilation", "test_event_4"),
                    ("no_power", "test_event_5"),
                    ("vehicle_error", "test_event_6"),
                )
            ]
        },
    )

    hass.states.async_set("sensor.vehicle_status_101", "standby")
    for i in range(1, 7):
        hass.bus.async_fire(f"test_event_{i}")
    await hass.async_block_till_done()
    assert len(calls) == 1
    assert calls[0].data["some"] == "standby - test_event_1"

    hass.states.async_set("sensor.vehicle_status_101", "vehicle_detected")
    for i in range(1, 7):
        hass.bus.async_fire(f"test_event_{i}")
    await hass.async_block_till_done()
    assert len(calls) == 2
    assert calls[1].data["some"] == "vehicle_detected - test_event_2"

    hass.states.async_set("sensor.vehicle_status_101", "ready")
    for i in range(1, 7):
        hass.bus.async_fire(f"test_event_{i}")
    await hass.async_block_till_done()
    assert len(calls) == 3
    assert calls[2].data["some"] == "ready - test_event_3"

    hass.states.async_set("sensor.vehicle_status_101", "with_ventilation")
    for i in range(1, 7):
        hass.bus.async_fire(f"test_event_{i}")
    await hass.async_block_till_done()
    assert len(calls) == 4
    assert calls[3].data["some"] == "with_ventilation - test_event_4"

    hass.states.async_set("sensor.vehicle_status_101", "no_power")
    for i in range(1, 7):
        hass.bus.async_fire(f"test_event_{i}")
    await hass.async_block_till_done()
    assert len(calls) == 5
    assert calls[4].data["some"] == "no_power - test_event_5"

    hass.states.async_set("sensor.vehicle_status_101", "vehicle_error")
    for i in range(1, 7):
        hass.bus.async_fire(f"test_event_{i}")
    await hass.async_block_till_done()
    assert len(calls) == 6
    assert calls[5].data["some"] == "vehicle_error - test_event_6"
