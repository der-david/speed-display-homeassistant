"""MQTT data coordinator for Speed Display."""

from __future__ import annotations

import json
import logging
from typing import Any

from homeassistant.components import mqtt
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import DOMAIN, SOURCE_FIRMWARE, SOURCE_SIMULATOR, SOURCE_UNKNOWN

_LOGGER = logging.getLogger(__name__)


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
        self.data = {
            "status": {},
            "speed": None,
            "threshold": None,
            "vehicle_passing": {},
            "range_transition": {},
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
        if not self.topic_prefix:
            _LOGGER.warning("Speed Display integration configured without a topic prefix")
            return
        base = self.topic_prefix

        async def subscribe(topic: str, key: str) -> None:
            unsub = await mqtt.async_subscribe(
                self.hass,
                topic,
                lambda msg: self._handle_message(key, msg.payload),
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

    def _handle_message(self, key: str, payload_bytes: bytes) -> None:
        raw = payload_bytes.decode("utf-8", errors="ignore").strip()
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
                try:
                    speed_value = None if value in (None, "", "null") else float(value)
                except (TypeError, ValueError):
                    speed_value = None
            else:
                try:
                    speed_value = None if raw in ("", "null") else float(raw)
                except ValueError:
                    speed_value = None
            self._update_data(speed=speed_value)
            return

        if key == "threshold":
            try:
                threshold = None if raw in ("", "null") else float(raw)
            except ValueError:
                threshold = None
            self._update_data(threshold=threshold)
            return

        if isinstance(parsed, dict):
            source = self._infer_source(parsed)
            self._update_data(
                **{
                    key: parsed,
                    "source": source,
                }
            )
