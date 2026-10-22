import io
import base64
import logging
from datetime import datetime
from pathlib import Path
import mss
from PIL import Image
from config import Config

logger = logging.getLogger(__name__)

class ScreenshotService:
    def __init__(self):
        self._last_screenshot: Image.Image | None = None
        self._last_timestamp: str | None = None

    def capture(self) -> Image.Image:
        with mss.MSS() as sct:
            monitor = sct.monitors[1] if len(sct.monitors) > 1 else sct.monitors[0]
            raw = sct.grab(monitor)
            img = Image.frombytes("RGB", raw.size, raw.bgra, "raw", "BGRX")
        self._last_screenshot = img
        return img
