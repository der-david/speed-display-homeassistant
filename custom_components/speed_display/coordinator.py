"""MQTT data coordinator for Speed Display."""

from __future__ import annotations

import json
import logging
from typing import Any

from homeassistant.components import mqtt
from homeassistant.core import HomeAssistant
from homeassistant.helpers.event import async_track_time_change
from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import dt as dt_util

from .const import DOMAIN, RANGE_ORDER, SOURCE_FIRMWARE, SOURCE_SIMULATOR, SOURCE_UNKNOWN

_LOGGER = logging.getLogger(__name__)

STORE_VERSION = 1

COUNT_KEYS = [
    "vehicle_passes",
    "overspeed",
    "end_safe",
    "end_neutral",
    "end_fast",
    "same_speed",
    "faster",
    "slower",
    "range_change",
    "same_safe",
    "same_neutral",
    "same_fast",
    "safe_to_neutral",
    "safe_to_fast",
    "neutral_to_safe",
    "neutral_to_fast",
    "fast_to_neutral",
    "fast_to_safe",
    "braked_fast_to_neutral",
    "braked_fast_to_safe",
]

SPEED_ACCUM_KEYS = [
    "average_vehicle_speed",
    "average_max_vehicle_speed",
    "average_min_vehicle_speed",
]

SPEED_EXTREME_KEYS = [
    "max_vehicle_speed",
    "min_vehicle_speed",
]


class SpeedDisplayCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Collect and expose MQTT state for one display."""

    def __init__(self, hass: HomeAssistant, entry) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}:{entry.entry_id}",
            update_method=self._noop_update,
            update_interval=None,
        )
        self.entry = entry
        self.topic_prefix = str(entry.data.get("topic_prefix", "")).strip("/")
        self._unsubs: list[Any] = []
        self._time_unsubs: list[Any] = []
        self._store = Store(hass, STORE_VERSION, f"{DOMAIN}.{entry.entry_id}.json")
        self._loaded = False
        self.data = {
            "status": {},
            "speed": None,
            "threshold": None,
            "vehicle_passing": {},
            "range_transition": {},
            "last_vehicle": {},
            "stats": self._empty_stats(),
            "source": SOURCE_UNKNOWN,
            "device_id": None,
            "display_id": None,
        }

    async def _noop_update(self) -> dict[str, Any]:
        return self.data

    def _infer_source(self, payload: dict[str, Any]) -> str:
        source = str(payload.get("source") or "").strip().lower()
        if source == SOURCE_SIMULATOR:
            return SOURCE_SIMULATOR
        if source == SOURCE_FIRMWARE:
            return SOURCE_FIRMWARE
        return SOURCE_UNKNOWN

    def _update_data(self, **changes: Any) -> None:
        updated = dict(self.data)
        updated.update(changes)
        self.async_set_updated_data(updated)

    async def async_start(self) -> None:
        await self._async_load_stats()
        self._time_unsubs.append(
            async_track_time_change(self.hass, self._handle_midnight, hour=0, minute=0, second=5)
        )
        if not self.topic_prefix:
            _LOGGER.warning("Speed Display integration configured without a topic prefix")
            return
        base = self.topic_prefix

        async def subscribe(topic: str, key: str) -> None:
            unsub = await mqtt.async_subscribe(
                self.hass,
                topic,
                lambda msg: self.hass.loop.call_soon_threadsafe(
                    self._handle_message, key, msg.payload
                ),
            )
            self._unsubs.append(unsub)

        await subscribe(f"{base}/status", "status")
        await subscribe(f"{base}/speed", "speed")
        await subscribe(f"{base}/threshold", "threshold")
        await subscribe(f"{base}/event/range_transition", "range_transition")
        await subscribe(f"{base}/event/vehicle_passing", "vehicle_passing")

    async def async_shutdown(self) -> None:
        while self._unsubs:
            unsub = self._unsubs.pop()
            try:
                unsub()
            except Exception:
                _LOGGER.debug("Error while unsubscribing", exc_info=True)
        while self._time_unsubs:
            unsub = self._time_unsubs.pop()
            try:
                unsub()
            except Exception:
                _LOGGER.debug("Error while removing time listener", exc_info=True)

    def _period_keys(self) -> tuple[str, str]:
        now = dt_util.now()
        iso = now.isocalendar()
        return now.date().isoformat(), f"{iso.year}-W{iso.week:02d}"

    def _empty_period(self) -> dict[str, Any]:
        data: dict[str, Any] = {key: 0 for key in COUNT_KEYS}
        for key in SPEED_ACCUM_KEYS:
            data[key] = None
            data[f"{key}_sum"] = 0.0
            data[f"{key}_count"] = 0
        data["max_vehicle_speed"] = None
        data["min_vehicle_speed"] = None
        return data

    def _empty_stats(self) -> dict[str, Any]:
        day_key, week_key = self._period_keys()
        return {
            "day_key": day_key,
            "week_key": week_key,
            "today": self._empty_period(),
            "week": self._empty_period(),
        }

    async def _async_load_stats(self) -> None:
        if self._loaded:
            return
        stored = await self._store.async_load()
        stats = stored if isinstance(stored, dict) else self._empty_stats()
        stats = self._sanitize_stats(stats)
        self._loaded = True
        self._update_data(stats=stats)
        await self._async_save_stats()

    async def _async_save_stats(self) -> None:
        await self._store.async_save(self.data.get("stats") or self._empty_stats())

    async def async_reset_stats(self, period: str = "all") -> None:
        """Reset persisted statistics."""
        stats = self._sanitize_stats(dict(self.data.get("stats") or {}))
        if period in ("today", "all"):
            stats["day_key"], _ = self._period_keys()
            stats["today"] = self._empty_period()
        if period in ("week", "all"):
            _, stats["week_key"] = self._period_keys()
            stats["week"] = self._empty_period()
        self._update_data(stats=stats)
        await self._async_save_stats()

    def _sanitize_stats(self, stats: dict[str, Any]) -> dict[str, Any]:
        day_key, week_key = self._period_keys()
        sanitized = {
            "day_key": stats.get("day_key") or day_key,
            "week_key": stats.get("week_key") or week_key,
            "today": self._sanitize_period(stats.get("today")),
            "week": self._sanitize_period(stats.get("week")),
        }
        if sanitized["day_key"] != day_key:
            sanitized["day_key"] = day_key
            sanitized["today"] = self._empty_period()
        if sanitized["week_key"] != week_key:
            sanitized["week_key"] = week_key
            sanitized["week"] = self._empty_period()
        return sanitized

    def _sanitize_period(self, period: Any) -> dict[str, Any]:
        result = self._empty_period()
        if not isinstance(period, dict):
            return result
        for key in COUNT_KEYS:
            try:
                result[key] = int(period.get(key, 0) or 0)
            except (TypeError, ValueError):
                result[key] = 0
        for key in SPEED_ACCUM_KEYS:
            try:
                total = float(period.get(f"{key}_sum", 0.0) or 0.0)
                count = int(period.get(f"{key}_count", 0) or 0)
            except (TypeError, ValueError):
                total = 0.0
                count = 0
            result[f"{key}_sum"] = total
            result[f"{key}_count"] = count
            result[key] = round(total / count, 1) if count else None
        for key in SPEED_EXTREME_KEYS:
            result[key] = self._float_or_none(period.get(key))
        return result

    def _handle_midnight(self, now) -> None:
        stats = self._sanitize_stats(dict(self.data.get("stats") or {}))
        self._update_data(stats=stats)
        self.hass.async_create_task(self._async_save_stats())

    def _float_or_none(self, value: Any) -> float | None:
        if value in (None, "", "null"):
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    def _range_name(self, value: Any) -> str | None:
        name = str(value or "").strip().lower()
        return name if name in RANGE_ORDER else None

    def _increment(self, period: dict[str, Any], key: str) -> None:
        period[key] = int(period.get(key, 0) or 0) + 1

    def _add_average(self, period: dict[str, Any], key: str, value: float | None) -> None:
        if value is None:
            return
        period[f"{key}_sum"] = float(period.get(f"{key}_sum", 0.0) or 0.0) + value
        period[f"{key}_count"] = int(period.get(f"{key}_count", 0) or 0) + 1
        period[key] = round(period[f"{key}_sum"] / period[f"{key}_count"], 1)

    def _update_extreme(self, period: dict[str, Any], key: str, value: float | None, *, maximum: bool) -> None:
        if value is None:
            return
        current = self._float_or_none(period.get(key))
        if current is None or (maximum and value > current) or ((not maximum) and value < current):
            period[key] = round(value, 1)

    def _apply_vehicle_passing_stats(self, payload: dict[str, Any]) -> dict[str, Any]:
        stats = self._sanitize_stats(dict(self.data.get("stats") or {}))
        initial_range = self._range_name(payload.get("initial_range"))
        end_range = self._range_name(payload.get("end_range"))
        initial_order = RANGE_ORDER.get(initial_range) if initial_range else None
        end_order = RANGE_ORDER.get(end_range) if end_range else None
        average_speed = self._float_or_none(payload.get("average_speed"))
        max_speed = self._float_or_none(payload.get("max_speed"))
        min_speed = self._float_or_none(payload.get("min_speed"))
        threshold = self._float_or_none((self.data.get("status") or {}).get("speed_limit"))
        neutral_margin = self._float_or_none((self.data.get("status") or {}).get("neutral_margin")) or 0.0

        for period_name in ("today", "week"):
            period = stats[period_name]
            self._increment(period, "vehicle_passes")
            if end_range:
                self._increment(period, f"end_{end_range}")
            if threshold is not None and max_speed is not None and max_speed > (threshold + neutral_margin):
                self._increment(period, "overspeed")
            elif end_range == "fast" or initial_range == "fast":
                self._increment(period, "overspeed")

            if initial_order is not None and end_order is not None:
                if end_order == initial_order:
                    self._increment(period, "same_speed")
                    self._increment(period, f"same_{end_range}")
                elif end_order > initial_order:
                    self._increment(period, "faster")
                    self._increment(period, "range_change")
                    self._increment(period, f"{initial_range}_to_{end_range}")
                else:
                    self._increment(period, "slower")
                    self._increment(period, "range_change")
                    self._increment(period, f"{initial_range}_to_{end_range}")
                    if initial_range == "fast" and end_range in ("neutral", "safe"):
                        self._increment(period, f"braked_fast_to_{end_range}")

            self._add_average(period, "average_vehicle_speed", average_speed)
            self._add_average(period, "average_max_vehicle_speed", max_speed)
            self._add_average(period, "average_min_vehicle_speed", min_speed)
            self._update_extreme(period, "max_vehicle_speed", max_speed, maximum=True)
            self._update_extreme(period, "min_vehicle_speed", min_speed, maximum=False)

        return stats

    def _handle_message(self, key: str, payload_bytes: bytes | bytearray | str) -> None:
        if isinstance(payload_bytes, (bytes, bytearray)):
            raw = bytes(payload_bytes).decode("utf-8", errors="ignore").strip()
        else:
            raw = str(payload_bytes).strip()
        try:
            parsed = json.loads(raw)
        except Exception:
            parsed = raw

        if key == "status" and isinstance(parsed, dict):
            source = self._infer_source(parsed)
            self._update_data(
                status=parsed,
                source=source,
                device_id=parsed.get("device_id"),
                display_id=parsed.get("display_id"),
            )
            return

        if key == "speed":
            speed_value: float | None
            if isinstance(parsed, dict):
                value = parsed.get("speed")
                speed_value = self._float_or_none(value)
                changes = {
                    "speed": speed_value,
                    "device_id": parsed.get("device_id") or self.data.get("device_id"),
                    "display_id": parsed.get("display_id") or self.data.get("display_id"),
                }
                source = self._infer_source(parsed)
                if source != SOURCE_UNKNOWN:
                    changes["source"] = source
                self._update_data(**changes)
                return
            else:
                try:
                    speed_value = None if raw in ("", "null") else float(raw)
                except ValueError:
                    speed_value = None
            self._update_data(speed=speed_value)
            return

        if key == "threshold":
            threshold = self._float_or_none(raw)
            self._update_data(threshold=threshold)
            return

        if isinstance(parsed, dict):
            source = self._infer_source(parsed)
            changes = {
                key: parsed,
                "source": source,
                "device_id": parsed.get("device_id") or self.data.get("device_id"),
                "display_id": parsed.get("display_id") or self.data.get("display_id"),
            }
            if key == "vehicle_passing":
                changes["last_vehicle"] = parsed
                changes["stats"] = self._apply_vehicle_passing_stats(parsed)
                self.hass.async_create_task(self._async_save_stats())
            self._update_data(
                **changes
            )
