# AGENTS

## Purpose
This repository is a Python GroupMe webhook bot that routes incoming messages through trigger handlers, optionally publishes MQTT commands, and can post Frigate snapshots/review links.

## Quick Start For Agents
- Use Python and pytest only.
- Create/activate a virtual environment, then install dependencies:
  - `pip install -r requirements.txt`
- Set runtime imports:
  - `export PYTHONPATH=src`
- Run app locally:
  - `python src/groupme_bot/app.py`
- Run tests:
  - `pytest -q`
- Docker options:
  - `docker compose --profile test run --rm test`
  - `docker compose up --build app`

## High-Value File Map
- App entrypoint and webhook flow: [src/groupme_bot/app.py](src/groupme_bot/app.py)
- Trigger definitions and routing: [src/groupme_bot/handlers/triggers.py](src/groupme_bot/handlers/triggers.py)
- Config/env loading: [src/groupme_bot/config.py](src/groupme_bot/config.py)
- External integrations:
  - GroupMe: [src/groupme_bot/groupme_client.py](src/groupme_bot/groupme_client.py)
  - MQTT: [src/groupme_bot/mqtt_client.py](src/groupme_bot/mqtt_client.py)
  - Frigate: [src/groupme_bot/frigate_client.py](src/groupme_bot/frigate_client.py)
- Integration-style app tests: [tests/test_app_processing.py](tests/test_app_processing.py)
- Trigger behavior tests: [tests/test_triggers.py](tests/test_triggers.py)

## Architecture Notes
- Flask endpoint `/groupme/webhook` accepts GroupMe callbacks.
- `process_groupme_message` routes text via `route_message` and sends response messages.
- Trigger matches return `(reply, trigger_name, mqtt_topic)`.
- MQTT publish is optional per-trigger.
- For gate commands, app may post Frigate snapshot and review link.
- Prometheus metrics exposed at `/metrics`.

## Conventions To Follow
- Keep changes small and module-local.
- Preserve type hints and current logging style.
- Prefer extending trigger behavior in `triggers.py` rather than branching logic in `app.py`.
- When adding behavior, add/adjust pytest coverage in `tests/` in the same change.
- In tests, mock external side effects (GroupMe, MQTT, Frigate) with `monkeypatch`; do not call real services.

## Common Task: Add A New Trigger
1. Add a `Trigger(...)` entry to `TRIGGERS` in [src/groupme_bot/handlers/triggers.py](src/groupme_bot/handlers/triggers.py).
2. If needed, add helper reply/match functions near existing helpers.
3. If trigger needs MQTT, set `mqtt_topic` (or follow gate pattern with startup configuration).
4. Add tests in [tests/test_triggers.py](tests/test_triggers.py) and, if app-level effects matter, in [tests/test_app_processing.py](tests/test_app_processing.py).
5. Run `PYTHONPATH=src pytest -q`.

## Config And Environment Gotchas
- Required for startup validation:
  - `GROUPME_BOT_ID`
  - `GATE_MQTT_TOPIC`
  - valid `PORT` (> 0)
- `GROUPME_ACCESS_TOKEN` is required when Frigate snapshot uploads are enabled.
- Keep `PYTHONPATH=src` set for local runs/tests unless your environment already provides it.
- For full env reference, use [.env.example](.env.example).

## Canonical Docs
- Project setup, run, docker, and trigger notes: [README.md](README.md)
- Environment variable reference: [.env.example](.env.example)
