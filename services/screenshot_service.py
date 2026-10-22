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
