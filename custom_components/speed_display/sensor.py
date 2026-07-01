"""Sensors for Speed Display."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.const import EntityCategory
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .const import SOURCE_SIMULATOR
from .coordinator import SpeedDisplayCoordinator

ValueFn = Callable[[dict[str, Any]], Any]
AttributesFn = Callable[[dict[str, Any]], dict[str, Any]]
UnitFn = Callable[[dict[str, Any]], str | None]


@dataclass(frozen=True)
class SpeedDisplaySensorDescription:
    """Description for one Speed Display sensor."""

    key: str
    name: str
    value_fn: ValueFn
    icon: str | None = None
    device_class: SensorDeviceClass | None = None
    entity_category: EntityCategory | None = None
    state_class: SensorStateClass | None = None
    unit_fn: UnitFn | None = None
    attributes_fn: AttributesFn | None = None


def _status(data: dict[str, Any]) -> dict[str, Any]:
    return data.get("status") or {}


def _last_vehicle(data: dict[str, Any]) -> dict[str, Any]:
    return data.get("last_vehicle") or {}


def _stats(data: dict[str, Any], period: str, key: str) -> Any:
    return ((data.get("stats") or {}).get(period) or {}).get(key)


def _unit(data: dict[str, Any]) -> str | None:
    return _status(data).get("unit") or ((data.get("speed") is not None) and "km/h") or None


def _last_vehicle_attrs(data: dict[str, Any]) -> dict[str, Any]:
    return dict(_last_vehicle(data))


class SpeedDisplaySensor(CoordinatorEntity[SpeedDisplayCoordinator], SensorEntity):
    """Generic sensor backed by the shared coordinator."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: SpeedDisplayCoordinator,
        description: SpeedDisplaySensorDescription,
    ) -> None:
        super().__init__(coordinator)
        self._description = description
        self._value_fn = description.value_fn
        self._attr_name = description.name
        self._attr_unique_id = f"{coordinator.entry.entry_id}_{description.key}"
        self._attr_icon = description.icon
        self._attr_entity_category = description.entity_category
        self._attr_state_class = description.state_class

    @property
    def native_value(self) -> Any:
        return self._value_fn(self.coordinator.data)

    @property
    def native_unit_of_measurement(self) -> str | None:
        unit_fn = self._description.unit_fn
        return unit_fn(self.coordinator.data) if unit_fn is not None else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        attrs = {
            "source": self.coordinator.data.get("source"),
            "simulated": self.coordinator.data.get("source") == SOURCE_SIMULATOR,
            "device_id": self.coordinator.data.get("device_id"),
            "display_id": self.coordinator.data.get("display_id"),
        }
        attributes_fn = self._description.attributes_fn
        if attributes_fn is not None:
            attrs.update(attributes_fn(self.coordinator.data))
        return attrs

    @property
    def device_info(self):
        data = self.coordinator.data
        display_id = data.get("display_id") or self.coordinator.entry.data.get("display_id") or "?"
        simulated = data.get("source") == SOURCE_SIMULATOR
        model = "Browser Radar Sign Simulator" if simulated else "Speed Display Firmware"
        return {
            "identifiers": {(DOMAIN, data.get("device_id") or self.coordinator.entry.entry_id)},
            "name": f"Speed Display {display_id}",
            "manufacturer": "DIY",
            "model": model,
        }


SENSOR_DESCRIPTIONS: list[SpeedDisplaySensorDescription] = [
    SpeedDisplaySensorDescription(
        "speed",
        "Speed",
        lambda data: data.get("speed"),
        icon="mdi:speedometer",
        state_class=SensorStateClass.MEASUREMENT,
        unit_fn=_unit,
    ),
    SpeedDisplaySensorDescription(
        "threshold",
        "Threshold",
        lambda data: _status(data).get("speed_limit") or data.get("threshold"),
        icon="mdi:speedometer-medium",
        entity_category=EntityCategory.DIAGNOSTIC,
        state_class=SensorStateClass.MEASUREMENT,
        unit_fn=_unit,
    ),
    SpeedDisplaySensorDescription(
        "neutral_margin",
        "Neutral Margin",
        lambda data: _status(data).get("neutral_margin"),
        icon="mdi:plus-minus",
        entity_category=EntityCategory.DIAGNOSTIC,
        state_class=SensorStateClass.MEASUREMENT,
        unit_fn=_unit,
    ),
    SpeedDisplaySensorDescription(
        "state",
        "State",
        lambda data: _status(data).get("state"),
        icon="mdi:state-machine",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SpeedDisplaySensorDescription(
        "source",
        "Source",
        lambda data: data.get("source"),
        icon="mdi:source-branch",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SpeedDisplaySensorDescription(
        "last_range",
        "Last Range",
        lambda data: _status(data).get("last_speed_range"),
        icon="mdi:signal",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SpeedDisplaySensorDescription(
        "last_direction",
        "Last Direction",
        lambda data: _status(data).get("last_direction"),
        icon="mdi:arrow-decision",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SpeedDisplaySensorDescription(
        "network",
        "Network",
        lambda data: _status(data).get("network"),
        icon="mdi:wifi",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SpeedDisplaySensorDescription(
        "mqtt",
        "MQTT",
        lambda data: _status(data).get("mqtt"),
        icon="mdi:lan-connect",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SpeedDisplaySensorDescription(
        "last_vehicle_initial_speed",
        "Last Vehicle Initial Speed",
        lambda data: _last_vehicle(data).get("initial_speed"),
        icon="mdi:speedometer",
        state_class=SensorStateClass.MEASUREMENT,
        unit_fn=_unit,
        attributes_fn=_last_vehicle_attrs,
    ),
    SpeedDisplaySensorDescription(
        "last_vehicle_end_speed",
        "Last Vehicle End Speed",
        lambda data: _last_vehicle(data).get("end_speed"),
        icon="mdi:speedometer",
        state_class=SensorStateClass.MEASUREMENT,
        unit_fn=_unit,
        attributes_fn=_last_vehicle_attrs,
    ),
    SpeedDisplaySensorDescription(
        "last_vehicle_average_speed",
        "Last Vehicle Average Speed",
        lambda data: _last_vehicle(data).get("average_speed"),
        icon="mdi:speedometer-slow",
        state_class=SensorStateClass.MEASUREMENT,
        unit_fn=_unit,
        attributes_fn=_last_vehicle_attrs,
    ),
    SpeedDisplaySensorDescription(
        "last_vehicle_min_speed",
        "Last Vehicle Min Speed",
        lambda data: _last_vehicle(data).get("min_speed"),
        icon="mdi:speedometer-slow",
        state_class=SensorStateClass.MEASUREMENT,
        unit_fn=_unit,
        attributes_fn=_last_vehicle_attrs,
    ),
    SpeedDisplaySensorDescription(
        "last_vehicle_max_speed",
        "Last Vehicle Max Speed",
        lambda data: _last_vehicle(data).get("max_speed"),
        icon="mdi:speedometer",
        state_class=SensorStateClass.MEASUREMENT,
        unit_fn=_unit,
        attributes_fn=_last_vehicle_attrs,
    ),
    SpeedDisplaySensorDescription(
        "last_vehicle_initial_range",
        "Last Vehicle Initial Range",
        lambda data: _last_vehicle(data).get("initial_range"),
        icon="mdi:signal",
        attributes_fn=_last_vehicle_attrs,
    ),
    SpeedDisplaySensorDescription(
        "last_vehicle_end_range",
        "Last Vehicle End Range",
        lambda data: _last_vehicle(data).get("end_range"),
        icon="mdi:signal",
        attributes_fn=_last_vehicle_attrs,
    ),
    SpeedDisplaySensorDescription(
        "last_vehicle_direction",
        "Last Vehicle Direction",
        lambda data: _last_vehicle(data).get("direction"),
        icon="mdi:arrow-decision",
        attributes_fn=_last_vehicle_attrs,
    ),
    SpeedDisplaySensorDescription(
        "last_vehicle_duration",
        "Last Vehicle Duration",
        lambda data: _last_vehicle(data).get("duration_s"),
        icon="mdi:timer-outline",
        state_class=SensorStateClass.MEASUREMENT,
        unit_fn=lambda data: "s",
        attributes_fn=_last_vehicle_attrs,
    ),
]


COUNT_SENSOR_LABELS = {
    "vehicle_passes": ("Vehicle Passes", "mdi:car"),
    "overspeed": ("Overspeed", "mdi:speedometer"),
    "end_safe": ("Ended Safe", "mdi:check-circle-outline"),
    "end_neutral": ("Ended Neutral", "mdi:alert-circle-outline"),
    "end_fast": ("Ended Fast", "mdi:alert-octagon-outline"),
    "same_speed": ("Same Range", "mdi:equal"),
    "faster": ("Faster", "mdi:arrow-up-bold"),
    "slower": ("Slower", "mdi:arrow-down-bold"),
    "range_change": ("Range Change", "mdi:swap-vertical-bold"),
    "same_safe": ("Same Safe", "mdi:check-circle-outline"),
    "same_neutral": ("Same Neutral", "mdi:alert-circle-outline"),
    "same_fast": ("Same Fast", "mdi:alert-octagon-outline"),
    "safe_to_neutral": ("Safe To Neutral", "mdi:arrow-top-right-thick"),
    "safe_to_fast": ("Safe To Fast", "mdi:arrow-top-right-thick"),
    "neutral_to_safe": ("Neutral To Safe", "mdi:arrow-bottom-right-thick"),
    "neutral_to_fast": ("Neutral To Fast", "mdi:arrow-top-right-thick"),
    "fast_to_neutral": ("Fast To Neutral", "mdi:arrow-bottom-right-thick"),
    "fast_to_safe": ("Fast To Safe", "mdi:arrow-bottom-right-thick"),
    "braked_fast_to_neutral": ("Braked Fast To Neutral", "mdi:car-brake-alert"),
    "braked_fast_to_safe": ("Braked Fast To Safe", "mdi:car-brake-parking"),
}

SPEED_SENSOR_LABELS = {
    "average_vehicle_speed": ("Average Vehicle Speed", "mdi:speedometer-slow"),
    "average_max_vehicle_speed": ("Average Max Vehicle Speed", "mdi:speedometer"),
    "average_min_vehicle_speed": ("Average Min Vehicle Speed", "mdi:speedometer-slow"),
    "max_vehicle_speed": ("Max Vehicle Speed", "mdi:speedometer"),
    "min_vehicle_speed": ("Min Vehicle Speed", "mdi:speedometer-slow"),
}


def _period_name(period: str) -> str:
    if period == "today":
        return "Today"
    if period == "week":
        return "This Week"
    return "Total"


for _period in ("today", "week", "total"):
    for _key, (_label, _icon) in COUNT_SENSOR_LABELS.items():
        SENSOR_DESCRIPTIONS.append(
            SpeedDisplaySensorDescription(
                f"{_key}_{_period}",
                f"{_label} {_period_name(_period)}",
                lambda data, period=_period, key=_key: _stats(data, period, key),
                icon=_icon,
                state_class=SensorStateClass.TOTAL_INCREASING,
            )
        )
    for _key, (_label, _icon) in SPEED_SENSOR_LABELS.items():
        SENSOR_DESCRIPTIONS.append(
            SpeedDisplaySensorDescription(
                f"{_key}_{_period}",
                f"{_label} {_period_name(_period)}",
                lambda data, period=_period, key=_key: _stats(data, period, key),
                icon=_icon,
                state_class=SensorStateClass.MEASUREMENT,
                unit_fn=_unit,
            )
        )


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator: SpeedDisplayCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([SpeedDisplaySensor(coordinator, description) for description in SENSOR_DESCRIPTIONS])
