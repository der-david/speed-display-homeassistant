# Speed Display for Home Assistant

Home Assistant custom integration for Speed Display firmware and the browser simulator.

The integration listens to the display MQTT contract and creates one Home Assistant device per configured MQTT topic prefix. It does not create helper entities, automations, or scripts. Vehicle statistics are computed and persisted inside the integration.

## Installation

### HACS custom repository

1. Open HACS.
2. Go to `Integrations`.
3. Open `Custom repositories`.
4. Add `https://github.com/der-david/speed-display-homeassistant`.
5. Select category `Integration`.
6. Install `Speed Display`.
7. Restart Home Assistant.

### Manual installation

Copy `custom_components/speed_display` into your Home Assistant `custom_components` directory and restart Home Assistant.

## Setup

Add one integration entry per physical display or simulator:

1. Go to `Settings -> Devices & services -> Add integration`.
2. Search for `Speed Display`.
3. Enter a display name.
4. Enter the MQTT topic prefix used by the display or simulator.

Examples:

- Physical display: `speed-display/1`
- Simulator: `speed-display/sim`

MQTT must already be configured in Home Assistant.

## MQTT topics

The integration subscribes to:

- `<topic_prefix>/status`
- `<topic_prefix>/speed`
- `<topic_prefix>/threshold`
- `<topic_prefix>/event/range_transition`
- `<topic_prefix>/event/vehicle_passing`

Firmware and simulator should publish `source=firmware` or `source=simulator` in JSON payloads.

## Entities

Current display state:

- Speed
- Threshold
- Neutral Margin
- State
- Source
- Last Range
- Last Direction
- Network
- MQTT
- Simulated
- Vehicle Active
- Network Reboot Required

Last vehicle:

- Initial Speed
- End Speed
- Average Speed
- Min Speed
- Max Speed
- Initial Range
- End Range
- Direction
- Duration

Daily, weekly, and total counters:

- Vehicle Passes
- Overspeed
- Ended Safe / Neutral / Fast
- Same Range
- Faster
- Slower
- Range Change
- Same Safe / Neutral / Fast
- Safe to Neutral
- Safe to Fast
- Neutral to Safe
- Neutral to Fast
- Fast to Neutral
- Fast to Safe
- Braked Fast to Neutral
- Braked Fast to Safe

Daily, weekly, and total speed statistics:

- Average Vehicle Speed
- Average Max Vehicle Speed
- Average Min Vehicle Speed
- Max Vehicle Speed
- Min Vehicle Speed

## Statistics semantics

Statistics and last-vehicle sensors are based on complete `vehicle_passing` events, not intermediate `range_transition` events. Range-transition events remain available on MQTT for external consumers, but the integration does not expose them as separate Home Assistant entities.

`same`, `faster`, and `slower` are mutually exclusive and are derived from `initial_range` and `end_range`:

- `safe < neutral < fast`
- same range: `initial_range == end_range`
- faster: `end_range` is higher than `initial_range`
- slower: `end_range` is lower than `initial_range`

`range_change` is counted when `initial_range != end_range`.

`overspeed` is counted when `max_speed > speed_limit + neutral_margin`. If no current threshold data is available, a vehicle that starts or ends in `fast` is counted as overspeed.

## Reset statistics

The integration provides the service:

```yaml
service: speed_display.reset_stats
data:
  period: today
```

`period` can be:

- `all`
- `today`
- `week`

`all` resets today, this week, and total statistics. `today` and `week` only reset their respective rolling period.

If `entry_id` is omitted, all configured Speed Display entries are reset.

## License

GNU Affero General Public License v3.0 or later.
