# Speed Display Home Assistant Integration

This repo will hold the HA-facing abstraction around the displays.

License: GNU Affero General Public License v3.0 or later.

Planned scope:

- MQTT entity modeling for one or more displays
- optional config flow and discovery helpers
- sensors, counters, and utility helpers for Home Assistant dashboards
- simulator support via the same MQTT topic contract, marked by `source=simulator` and `simulated=true`

The integration reads the same MQTT topics as the firmware and exposes the source as a sensor plus a `simulated` binary sensor.

The display firmware stays HA-agnostic. MQTT remains the primary integration path.
