"""Sensors for Speed Display."""

from __future__ import annotations

from typing import Any, Callable

from homeassistant.components.sensor import SensorEntity
from homeassistant.const import EntityCategory
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import SpeedDisplayCoordinator


class SpeedDisplaySensor(CoordinatorEntity[SpeedDisplayCoordinator], SensorEntity):
    """Generic sensor backed by the shared coordinator."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: SpeedDisplayCoordinator,
        key: str,
        name: str,
        value_fn: Callable[[dict[str, Any]], Any],
        icon: str | None = None,
        entity_category: EntityCategory | None = None,
    ) -> None:
        super().__init__(coordinator)
        self._key = key
        self._value_fn = value_fn
        self._attr_name = name
        self._attr_unique_id = f"{coordinator.entry.entry_id}_{key}"
        self._attr_icon = icon
        self._attr_entity_category = entity_category

    @property
    def native_value(self) -> Any:
        return self._value_fn(self.coordinator.data)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {
            "source": self.coordinator.data.get("source"),
            "simulated": self.coordinator.data.get("simulated"),
            "device_id": self.coordinator.data.get("device_id"),
            "display_id": self.coordinator.data.get("display_id"),
        }

    @property
    def device_info(self):
        data = self.coordinator.data
        display_id = data.get("display_id") or self.coordinator.entry.data.get("display_id") or "?"
        source = data.get("source") or self.coordinator.source_hint
        simulated = bool(data.get("simulated"))
        model = "Browser Radar Sign Simulator" if simulated else "Speed Display Firmware"
        return {
            "identifiers": {(DOMAIN, data.get("device_id") or self.coordinator.entry.entry_id)},
            "name": f"Speed Display {display_id}",
            "manufacturer": "DIY",
            "model": model if source else model,
        }


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator: SpeedDisplayCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            SpeedDisplaySensor(
                coordinator,
                "speed",
                "Speed",
                lambda data: data.get("speed"),
                icon="mdi:speedometer",
            ),
            SpeedDisplaySensor(
                coordinator,
                "state",
                "State",
                lambda data: (data.get("status") or {}).get("state"),
                icon="mdi:state-machine",
                entity_category=EntityCategory.DIAGNOSTIC,
            ),
            SpeedDisplaySensor(
                coordinator,
                "source",
                "Source",
                lambda data: data.get("source"),
                icon="mdi:source-branch",
                entity_category=EntityCategory.DIAGNOSTIC,
            ),
            SpeedDisplaySensor(
                coordinator,
                "last_range",
                "Last Range",
                lambda data: (data.get("status") or {}).get("last_speed_range"),
                icon="mdi:signal",
                entity_category=EntityCategory.DIAGNOSTIC,
            ),
        ]
    )

