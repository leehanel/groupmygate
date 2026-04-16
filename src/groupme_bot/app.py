from __future__ import annotations

import logging
from typing import Any

from dotenv import load_dotenv
from flask import Flask, Response, request
from prometheus_client import CONTENT_TYPE_LATEST, Counter, generate_latest

from groupme_bot.config import load_config
from groupme_bot.frigate_client import FrigateClient
from groupme_bot.groupme_client import GroupMeClient
from groupme_bot.mqtt_client import MQTTClient
from groupme_bot.handlers.triggers import HELP_TEXT, configure_gate_topic, route_message

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
cfg = load_config()
client = GroupMeClient(cfg.groupme_bot_id, cfg.groupme_access_token)
mqtt = MQTTClient(cfg.mqtt_broker, cfg.mqtt_port, cfg.mqtt_username, cfg.mqtt_password)
frigate = FrigateClient(
    cfg.frigate_api_base_url,
    cfg.frigate_frontend_base_url,
    cfg.frigate_camera,
    cfg.frigate_clip_seconds,
    cfg.frigate_request_timeout,
)
configure_gate_topic(cfg.gate_mqtt_topic)

MESSAGES_RECEIVED = Counter(
    "groupme_messages_received_total",
    "Total number of GroupMe callback messages received",
)
TRIGGERS_FIRED = Counter(
    "groupme_triggers_fired_total",
    "Total number of triggers that produced a reply",
    ["trigger_name"],
)
SEND_ERRORS = Counter(
    "groupme_send_errors_total",
    "Total number of errors sending a reply to GroupMe",
)


def validate_required_config() -> None:
    missing: list[str] = []

    if cfg.port <= 0:
        missing.append("PORT")
    if not cfg.groupme_bot_id:
        missing.append("GROUPME_BOT_ID")
    if not cfg.gate_mqtt_topic:
        missing.append("GATE_MQTT_TOPIC")
    if cfg.frigate_api_base_url and cfg.frigate_camera and not cfg.groupme_access_token:
        missing.append("GROUPME_ACCESS_TOKEN")

    if missing:
        message = "Missing or invalid required config values: " + ", ".join(missing)
        logging.error(message)
        raise ValueError(message)


def _is_from_self(message: dict[str, Any]) -> bool:
    sender_type = message.get("sender_type")
    return sender_type == "bot"


def process_groupme_message(message: dict[str, Any]) -> None:
    text = message.get("text", "")
    if not text:
        logger.info("Ignoring message without text sender=%r", message.get("name"))
        return
    if _is_from_self(message):
        logger.info("Ignoring bot-originated message sender=%r text=%r", message.get("name"), text)
        return

    logger.info(
        "Received GroupMe message sender=%r sender_type=%r text=%r",
        message.get("name"),
        message.get("sender_type"),
        text,
    )
    MESSAGES_RECEIVED.inc()

    reply, trigger_name, mqtt_topic = route_message(message, text)
    if not reply:
        return

    gate_command_succeeded = True
    TRIGGERS_FIRED.labels(trigger_name=trigger_name).inc()
    if mqtt_topic:
        try:
            logger.info("Publishing MQTT for trigger=%s topic=%r", trigger_name, mqtt_topic)
            mqtt.publish(mqtt_topic)
        except Exception as e:
            logger.error("Failed to publish MQTT topic=%r: %s", mqtt_topic, e)
            reply = f"Failed to execute '{trigger_name}' command. Please contact the admin."
            gate_command_succeeded = False

    logger.info("Replying to GroupMe for trigger=%s reply=%r", trigger_name, reply)
    client.send_message(reply)

    if trigger_name in {"gate_open", "gate_video"} and gate_command_succeeded:
        snapshot = frigate.get_snapshot()
        if snapshot:
            image_bytes, content_type = snapshot
            logger.info("Posting Frigate snapshot image to GroupMe for trigger=%s", trigger_name)
            try:
                client.send_image_message("Gate snapshot", image_bytes, content_type)
            except Exception:
                SEND_ERRORS.inc()
                logger.exception("Failed to post Frigate snapshot image to GroupMe")

    if trigger_name == "gate_open" and gate_command_succeeded:
        clip_url = frigate.get_clip_url()
        if clip_url:
            logger.info("Posting Frigate review URL to GroupMe for trigger=%s", trigger_name)
            try:
                client.send_video_link_message("Gate review", clip_url)
            except Exception:
                SEND_ERRORS.inc()
                logger.exception("Failed to post Frigate review URL to GroupMe")

    if trigger_name == "gate_video":
        clip_url = frigate.get_clip_url()
        if clip_url:
            logger.info("Posting Frigate review URL to GroupMe for trigger=%s", trigger_name)
            try:
                client.send_video_link_message("Full gate clip", clip_url)
            except Exception:
                SEND_ERRORS.inc()
                logger.exception("Failed to post Frigate review URL to GroupMe")


def build_startup_announcement() -> str:
    return f"GroupMyGate is listening. {HELP_TEXT}"


@app.get("/metrics")
def metrics() -> Response:
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)


@app.post("/groupme/webhook")
def groupme_webhook() -> Response:
    payload = request.get_json(silent=True) or {}
    try:
        process_groupme_message(payload)
    except Exception:
        SEND_ERRORS.inc()
        logger.exception("Failed to process GroupMe webhook payload")
    return Response(status=200)


def announce_startup() -> None:
    announcement = build_startup_announcement()
    try:
        logger.info("Sending startup announcement to GroupMe")
        client.send_message(announcement)
    except Exception:
        SEND_ERRORS.inc()
        logger.exception("Failed to send startup announcement")


if __name__ == "__main__":
    validate_required_config()
    announce_startup()
    logger.info("Prometheus metrics available on :%s/metrics", cfg.port)
    logger.info("GroupMe callback listening on :%s/groupme/webhook", cfg.port)
    app.run(host="0.0.0.0", port=cfg.port)
