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
        img = self._resize(img)
        self._last_screenshot = img
        self._last_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return img

    def _resize(self, img: Image.Image) -> Image.Image:
        max_dim = Config.MAX_IMAGE_DIM
        if img.width <= max_dim and img.height <= max_dim:
            return img
        ratio = min(max_dim / img.width, max_dim / img.height)
        new_size = (int(img.width * ratio), int(img.height * ratio))
        return img.resize(new_size, Image.LANCZOS)

    def image_to_base64(self, img: Image.Image, fmt: str = "PNG") -> str:
        buf = io.BytesIO()
        img.save(buf, format=fmt)
        return base64.b64encode(buf.getvalue()).decode("utf-8")

    def image_to_bytes(self, img: Image.Image, fmt: str = "PNG") -> bytes:
        buf = io.BytesIO()
        img.save(buf, format=fmt)
        return buf.getvalue()
