from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Config:
    port: int
    groupme_bot_id: str
    groupme_access_token: str
    mqtt_broker: str
    mqtt_port: int
    mqtt_username: str
    mqtt_password: str
    gate_mqtt_topic: str
    frigate_api_base_url: str
    frigate_frontend_base_url: str
    frigate_camera: str
    frigate_clip_seconds: int
    frigate_request_timeout: float



def load_config() -> Config:
    legacy_frigate_base_url = os.getenv("FRIGATE_BASE_URL", "")
    frigate_api_base_url = os.getenv("FRIGATE_API_BASE_URL", legacy_frigate_base_url or "http://frigate:5000")
    frigate_frontend_base_url = os.getenv("FRIGATE_FRONTEND_BASE_URL", "http://localhost:5000")

    return Config(
        port=int(os.getenv("PORT", "3000")),
        groupme_bot_id=os.getenv("GROUPME_BOT_ID", ""),
        groupme_access_token=os.getenv("GROUPME_ACCESS_TOKEN", ""),
        mqtt_broker=os.getenv("MQTT_BROKER", "localhost"),
        mqtt_port=int(os.getenv("MQTT_PORT", "1883")),
        mqtt_username=os.getenv("MQTT_USERNAME", ""),
        mqtt_password=os.getenv("MQTT_PASSWORD", ""),
        gate_mqtt_topic=os.getenv("GATE_MQTT_TOPIC", "/home-commands/gate/open"),
        frigate_api_base_url=frigate_api_base_url,
        frigate_frontend_base_url=frigate_frontend_base_url,
        frigate_camera=os.getenv("FRIGATE_CAMERA", ""),
        frigate_clip_seconds=int(os.getenv("FRIGATE_CLIP_SECONDS", "30")),
        frigate_request_timeout=float(os.getenv("FRIGATE_REQUEST_TIMEOUT", "5")),
    )
