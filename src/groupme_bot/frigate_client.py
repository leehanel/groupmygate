from __future__ import annotations

import logging
import time
from typing import Optional
from urllib.parse import urlencode

import requests

logger = logging.getLogger(__name__)


class FrigateClient:
    def __init__(
        self,
        api_base_url: str,
        frontend_base_url: str,
        camera: str,
        clip_seconds: int = 30,
        request_timeout: float = 5.0,
    ) -> None:
        self.api_base_url = api_base_url.rstrip("/")
        self.frontend_base_url = (frontend_base_url or api_base_url).rstrip("/")
        self.camera = camera.strip()
        self.clip_seconds = clip_seconds
        self.request_timeout = request_timeout

    def enabled(self) -> bool:
        return bool(self.api_base_url and self.camera)

    def _get_clip_window(self) -> tuple[int, int]:
        end_ts = int(time.time())
        start_ts = end_ts - max(self.clip_seconds, 1)
        return start_ts, end_ts

    def _build_public_clip_url(self, start_ts: int, end_ts: int) -> str:
        query = urlencode(
            {
                "cameras": self.camera,
                "after": start_ts,
                "before": end_ts,
                "time_range": "custom",
            }
        )
        return f"{self.frontend_base_url}/review?{query}"

    def _build_fetch_clip_url(self, start_ts: int, end_ts: int) -> str:
        return f"{self.api_base_url}/api/{self.camera}/start/{start_ts}/end/{end_ts}/clip.mp4?download=1"

    def get_snapshot(self) -> Optional[tuple[bytes, str]]:
        if not self.enabled():
            return None

        snapshot_base = f"{self.api_base_url}/api/{self.camera}/latest.jpg"
        snapshot_url = f"{snapshot_base}?ts={int(time.time())}"

        try:
            response = requests.get(snapshot_url, timeout=self.request_timeout)
            response.raise_for_status()
            content_type = response.headers.get("Content-Type", "image/jpeg")
            return response.content, content_type
        except Exception:
            logger.exception("Failed to fetch Frigate snapshot from %r", snapshot_url)
            return None

    def get_clip_url(self) -> Optional[str]:
        if not self.enabled():
            return None

        start_ts, end_ts = self._get_clip_window()
        return self._build_public_clip_url(start_ts, end_ts)

    def get_clip(self) -> Optional[tuple[bytes, str, str]]:
        if not self.enabled():
            return None

        start_ts, end_ts = self._get_clip_window()
        public_clip_url = self._build_public_clip_url(start_ts, end_ts)
        fetch_clip_url = self._build_fetch_clip_url(start_ts, end_ts)

        try:
            response = requests.get(fetch_clip_url, timeout=self.request_timeout)
            response.raise_for_status()
            content_type = response.headers.get("Content-Type", "video/mp4")
            return response.content, content_type, public_clip_url
        except Exception:
            logger.exception("Failed to fetch Frigate clip from %r", fetch_clip_url)
            return None
