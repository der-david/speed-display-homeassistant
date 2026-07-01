"""Binary sensors for Speed Display."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity
from homeassistant.const import EntityCategory
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, SOURCE_SIMULATOR
from .coordinator import SpeedDisplayCoordinator

ValueFn = Callable[[dict[str, Any]], bool]


@dataclass(frozen=True)
class SpeedDisplayBinarySensorDescription:
    """Description for one binary sensor."""

    key: str
    name: str
    value_fn: ValueFn
    icon: str | None = None
    device_class: BinarySensorDeviceClass | None = None
    entity_category: EntityCategory | None = None


class SpeedDisplayBinarySensor(CoordinatorEntity[SpeedDisplayCoordinator], BinarySensorEntity):
    """Generic binary sensor backed by the coordinator."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: SpeedDisplayCoordinator,
        description: SpeedDisplayBinarySensorDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._value_fn = description.value_fn
        self._attr_name = description.name
        self._attr_unique_id = f"{coordinator.entry.entry_id}_{description.key}"
        self._attr_icon = description.icon
        self._attr_entity_category = description.entity_category

    @property
    def is_on(self) -> bool:
        return self._value_fn(self.coordinator.data)

    @property
    def device_info(self):
        data = self.coordinator.data
        display_id = data.get("display_id") or self.coordinator.entry.data.get("display_id") or "?"
        model = "Browser Radar Sign Simulator" if self.is_on else "Speed Display Firmware"
        return {
            "identifiers": {(DOMAIN, data.get("device_id") or self.coordinator.entry.entry_id)},
            "name": f"Speed Display {display_id}",
            "manufacturer": "DIY",
            "model": model,
        }


BINARY_SENSOR_DESCRIPTIONS = [
    SpeedDisplayBinarySensorDescription(
        "simulated",
        "Simulated",
        lambda data: data.get("source") == SOURCE_SIMULATOR,
        icon="mdi:test-tube",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SpeedDisplayBinarySensorDescription(
        "vehicle_active",
        "Vehicle Active",
        lambda data: bool((data.get("status") or {}).get("vehicle_active")),
        icon="mdi:car",
    ),
    SpeedDisplayBinarySensorDescription(
        "network_reboot_required",
        "Network Reboot Required",
        lambda data: bool((data.get("status") or {}).get("network_reboot_required")),
        icon="mdi:restart-alert",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
]


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator: SpeedDisplayCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            SpeedDisplayBinarySensor(coordinator, description)
            for description in BINARY_SENSOR_DESCRIPTIONS
        ]
    )
