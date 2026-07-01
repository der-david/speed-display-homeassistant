"""Binary sensors for Speed Display."""

from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, SOURCE_SIMULATOR
from .coordinator import SpeedDisplayCoordinator


class SpeedDisplaySimulatedBinarySensor(CoordinatorEntity[SpeedDisplayCoordinator], BinarySensorEntity):
    """Expose whether the source is simulated."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: SpeedDisplayCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_name = "Simulated"
        self._attr_unique_id = f"{coordinator.entry.entry_id}_simulated"
        self._attr_icon = "mdi:test-tube"

    @property
    def is_on(self) -> bool:
        return self.coordinator.data.get("source") == SOURCE_SIMULATOR

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


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator: SpeedDisplayCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([SpeedDisplaySimulatedBinarySensor(coordinator)])
