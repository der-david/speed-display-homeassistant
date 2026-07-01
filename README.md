# Speed Display Home Assistant Integration

This repo will hold the HA-facing abstraction around the displays.

License: GNU Affero General Public License v3.0 or later.

Planned scope:

- MQTT entity modeling for one or more displays
- MQTT discovery for firmware and simulator devices
- sensors, counters, and utility helpers for Home Assistant dashboards
- simulator support via the same MQTT topic contract, marked by `source=simulator`

The MQTT payload contract uses `source` as the only origin field. `source=firmware` means a physical display, `source=simulator` means a browser simulator. A `simulated` binary sensor is derived from that value for dashboards and filters.

The display firmware stays HA-agnostic. MQTT remains the primary integration path.

Home Assistant dashboards are not created automatically by the integration. Ship reusable Lovelace YAML examples or a dedicated custom card if the dashboard should be packaged with the project.
