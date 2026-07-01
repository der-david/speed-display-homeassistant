"""Speed Display Home Assistant integration."""

from __future__ import annotations

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN, PLATFORMS
from .coordinator import SpeedDisplayCoordinator

SERVICE_RESET_STATS = "reset_stats"
CONF_ENTRY_ID = "entry_id"
CONF_PERIOD = "period"

RESET_STATS_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_ENTRY_ID): str,
        vol.Optional(CONF_PERIOD, default="all"): vol.In(["all", "today", "week"]),
    }
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    coordinator = SpeedDisplayCoordinator(hass, entry)
    await coordinator.async_start()
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    _async_register_services(hass)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    coordinator = hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
    if coordinator is not None:
        await coordinator.async_shutdown()
    return unload_ok


def _async_register_services(hass: HomeAssistant) -> None:
    if hass.services.has_service(DOMAIN, SERVICE_RESET_STATS):
        return

    async def async_reset_stats(call) -> None:
        entry_id = call.data.get(CONF_ENTRY_ID)
        period = call.data.get(CONF_PERIOD, "all")
        coordinators: dict[str, SpeedDisplayCoordinator] = hass.data.get(DOMAIN, {})
        targets = (
            [coordinators[entry_id]]
            if entry_id and entry_id in coordinators
            else list(coordinators.values())
        )
        for coordinator in targets:
            await coordinator.async_reset_stats(period)

    hass.services.async_register(
        DOMAIN,
        SERVICE_RESET_STATS,
        async_reset_stats,
        schema=RESET_STATS_SCHEMA,
    )
