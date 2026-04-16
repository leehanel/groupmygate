# GroupMe Trigger Bot (Python)

This is a Python GroupMe bot callback framework that responds to specific triggers.

## Features

- GroupMe bot callback endpoint at `/groupme/webhook`
- Trigger-based command routing
- GroupMe bot message sender
- Optional Frigate snapshot posting for `!gate`
- Prometheus metrics endpoint
- Basic pytest test coverage

## Setup

1. Activate your virtual environment.
2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Copy `.env.example` to `.env` and fill in values:

   - `GROUPME_BOT_ID`: your GroupMe bot id
   - `GROUPME_ACCESS_TOKEN`: required for image uploads (Frigate snapshots)
   - `PORT`: callback server port (default `3000`)
   - `FRIGATE_API_BASE_URL`: Frigate URL this service uses for API/media fetches (example: `http://frigate:5000`)
   - `FRIGATE_FRONTEND_BASE_URL`: Frigate URL linked back to users in GroupMe (example: `https://frigate.example.com`)
   - `FRIGATE_CAMERA`: Frigate camera name to snapshot for `!gate`
   - `FRIGATE_CLIP_SECONDS`: clip duration for `!gate video` (default `30`)

## Run

```bash
export PYTHONPATH=src
python src/groupme_bot/app.py
```

The bot exposes:

- callback endpoint: `http://localhost:3000/groupme/webhook`
- metrics endpoint: `http://localhost:3000/metrics`

## Testing

```bash
export PYTHONPATH=src
pytest -q
```

## Docker

1. Create `.env` from `.env.example` and set `GROUPME_BOT_ID`.
2. Build the image:

   ```bash
   docker build -t groupmygate:latest .
   ```

3. Run tests in Docker:

   ```bash
   docker compose --profile test run --rm test
   ```

4. Start the webhook service:

   ```bash
   docker compose up --build app
   ```

5. Stop containers:

   ```bash
   docker compose down
   ```

## Configure GroupMe bot callback

Set your bot callback URL in GroupMe to:

`https://your-domain/groupme/webhook`

For local testing, use ngrok:

```bash
ngrok http 3000
```

## Add a new trigger

Edit `src/groupme_bot/handlers/triggers.py` and append a `Trigger` entry to `TRIGGERS`.

## Gate commands

- `!gate open`: opens gate, then posts a snapshot image and a Frigate review link
- `!gate video`: posts a snapshot image and a Frigate review link to the full clip window

Use `FRIGATE_API_BASE_URL` for the container-to-Frigate network path and `FRIGATE_FRONTEND_BASE_URL` for the public URL users can open from GroupMe.
