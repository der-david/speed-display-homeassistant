# Workflow

This repo contains the Home Assistant abstraction layer.

Recommended update flow:

1. Keep MQTT topic contracts aligned with the firmware and simulator.
2. Add or adjust HA entities, dashboards, helpers, or config flow logic here.
3. If the payload or topic schema changes, update the docs in this repo and the other repos together.
4. Commit and release the HA integration independently from firmware and simulator.

The integration should stay HA-focused and not duplicate firmware runtime logic.

