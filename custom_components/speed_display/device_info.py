"""Device metadata helpers for Speed Display entities."""

from __future__ import annotations

from typing import Any

from .const import DOMAIN, SOURCE_SIMULATOR


def speed_display_device_info(data: dict[str, Any], entry) -> dict[str, Any]:
    """Build Home Assistant device info from MQTT metadata with safe fallbacks."""
    status = data.get("status") or {}
    device = status.get("device") if isinstance(status.get("device"), dict) else {}
    identifiers = device.get("identifiers")
    if isinstance(identifiers, list) and identifiers:
        identifier = str(identifiers[0])
    else:
        identifier = str(data.get("device_id") or entry.entry_id)

    display_id = data.get("display_id") or entry.data.get("display_id") or "?"
    simulated = data.get("source") == SOURCE_SIMULATOR

    return {
        "identifiers": {(DOMAIN, identifier)},
        "name": device.get("name") or f"Speed Display {display_id}",
        "manufacturer": device.get("manufacturer") or "DIY",
        "model": device.get(
            "model",
            "Browser Radar Sign Simulator" if simulated else "Speed Display Firmware",
        ),
    }
