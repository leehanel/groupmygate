from __future__ import annotations

import logging
from typing import Optional

import requests

GROUPME_POST_URL = "https://api.groupme.com/v3/bots/post"
GROUPME_IMAGE_URL = "https://image.groupme.com/pictures"
logger = logging.getLogger(__name__)


class GroupMeClient:
    def __init__(self, bot_id: str, access_token: str = "") -> None:
        self.bot_id = bot_id
        self.access_token = access_token

    def send_message(self, text: str) -> None:
        if not self.bot_id:
            raise ValueError("GROUPME_BOT_ID is missing")

        logger.info("Sending GroupMe bot reply: %r", text)
        response = requests.post(
            GROUPME_POST_URL,
            json={"bot_id": self.bot_id, "text": text},
            timeout=10,
        )
        logger.info("GroupMe bot reply response status=%s body=%r", response.status_code, response.text)
        response.raise_for_status()

    def _upload_image(self, image_bytes: bytes, content_type: str) -> str:
        if not self.access_token:
            raise ValueError("GROUPME_ACCESS_TOKEN is missing")

        headers = {
            "X-Access-Token": self.access_token,
            "Content-Type": content_type,
        }
        response = requests.post(
            GROUPME_IMAGE_URL,
            data=image_bytes,
            headers=headers,
            timeout=10,
        )
        logger.info("GroupMe image upload response status=%s body=%r", response.status_code, response.text)
        response.raise_for_status()

        payload = response.json()
        picture_url: Optional[str] = payload.get("payload", {}).get("picture_url")
        if not picture_url:
            raise ValueError("GroupMe image upload did not return picture_url")
        return picture_url

    def send_image_message(self, text: str, image_bytes: bytes, content_type: str = "image/jpeg") -> None:
        if not self.bot_id:
            raise ValueError("GROUPME_BOT_ID is missing")

        picture_url = self._upload_image(image_bytes, content_type)
        payload = {
            "bot_id": self.bot_id,
            "text": text,
            "attachments": [
                {
                    "type": "image",
                    "url": picture_url,
                }
            ],
        }

        logger.info("Sending GroupMe bot image message text=%r image_url=%r", text, picture_url)
        response = requests.post(GROUPME_POST_URL, json=payload, timeout=10)
        logger.info("GroupMe bot image message response status=%s body=%r", response.status_code, response.text)
        response.raise_for_status()

    def send_video_link_message(self, text: str, video_url: str) -> None:
        self.send_message(f"{text}\n{video_url}")
