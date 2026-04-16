from __future__ import annotations

import logging

import paho.mqtt.publish as mqtt_publish

logger = logging.getLogger(__name__)


class MQTTClient:
    def __init__(self, broker: str, port: int, username: str = "", password: str = "") -> None:
        self.broker = broker
        self.port = port
        self._auth = {"username": username, "password": password} if username else None

    def publish(self, topic: str, payload: str = "") -> None:
        mqtt_publish.single(
            topic,
            payload=payload,
            hostname=self.broker,
            port=self.port,
            auth=self._auth,
        )
        logger.info("MQTT published to %s: %r", topic, payload)
