"""
SightFix AI — Screenshot Service

Captures the primary desktop screen using the `mss` library.
Handles image resizing and optional persistence.
"""

import io
import base64
import logging
from datetime import datetime
from pathlib import Path

import mss
import mss.tools
from PIL import Image

from config import Config

logger = logging.getLogger(__name__)


class ScreenshotService:
    """Captures, processes, and optionally stores desktop screenshots."""

    def __init__(self):
        self._last_screenshot: Image.Image | None = None
        self._last_timestamp: str | None = None

    # ── Public API ────────────────────────────────────────────────────

    def capture(self, allow_synthetic_fallback: bool = False) -> Image.Image:
        """
        Capture the primary monitor and return a PIL Image.

        If running in a headless environment or locked Windows session where GDI BitBlt
        fails, and allow_synthetic_fallback is True, returns a generated diagnostic test image.

        Raises RuntimeError on failure when no fallback is permitted.
        """
        img = None
        last_error = None

        # 1. Primary capture method: mss
        try:
            with mss.MSS() as sct:
                monitor = sct.monitors[1] if len(sct.monitors) > 1 else sct.monitors[0]
                raw = sct.grab(monitor)
                img = Image.frombytes("RGB", raw.size, raw.bgra, "raw", "BGRX")
        except Exception as exc:
            last_error = exc
            logger.warning("mss capture failed (%s), attempting ImageGrab fallback...", exc)

        # 2. Fallback capture method: PIL ImageGrab
        if img is None:
            try:
                from PIL import ImageGrab
                grabbed = ImageGrab.grab()
                if grabbed:
                    img = grabbed.convert("RGB")
            except Exception as exc:
                last_error = exc
                logger.warning("PIL ImageGrab capture failed: %s", exc)

        # 3. Headless / test fallback if requested
        if img is None and allow_synthetic_fallback:
            logger.info("Using synthetic desktop screenshot for headless/test session")
            img = self._create_synthetic_screen()

        if img is None:
            logger.exception("Screenshot capture failed across all providers")
            raise RuntimeError(
                f"Failed to capture desktop screen: {last_error}\n"
                "Note: Screen capture requires an active, unlocked desktop session."
            )

        # Resize for the AI model
        img = self._resize(img)

        self._last_screenshot = img
        self._last_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if Config.SAVE_SCREENSHOTS:
            self._save(img)

        logger.info("Screenshot captured: %dx%d", img.width, img.height)
        return img

    def _create_synthetic_screen(self) -> Image.Image:
        """Generate a simulated desktop screenshot for testing and headless environments."""
        from PIL import ImageDraw
        img = Image.new("RGB", (1280, 720), color="#1e1e2e")
        draw = ImageDraw.Draw(img)
        # Draw window frame
        draw.rectangle([50, 50, 1230, 670], fill="#181825", outline="#313244", width=2)
        draw.rectangle([50, 50, 1230, 90], fill="#11111b")
        draw.ellipse([65, 65, 75, 75], fill="#f38ba8")
        draw.ellipse([85, 65, 95, 75], fill="#f9e2af")
        draw.ellipse([105, 65, 115, 75], fill="#a6e3a1")
        draw.text((130, 62), "Terminal — sightfix_ai", fill="#cdd6f4")
        # Draw terminal error text
        lines = [
            "PS D:\\projects\\demo> python app.py",
            "Traceback (most recent call last):",
            '  File "app.py", line 2, in <module>',
            "    import requests",
            "ModuleNotFoundError: No module named 'requests'",
            "PS D:\\projects\\demo> _",
        ]
        y = 120
        for line in lines:
            color = "#f38ba8" if "Error" in line else "#cdd6f4"
            draw.text((70, y), line, fill=color)
            y += 30
        return img

    def get_last(self) -> Image.Image | None:
        """Return the most recent screenshot, or None."""
        return self._last_screenshot

    def get_last_timestamp(self) -> str | None:
        return self._last_timestamp

    def image_to_base64(self, img: Image.Image, fmt: str = "PNG") -> str:
        """Encode a PIL Image as a base64 data string."""
        buf = io.BytesIO()
        img.save(buf, format=fmt)
        return base64.b64encode(buf.getvalue()).decode("utf-8")

    def image_to_bytes(self, img: Image.Image, fmt: str = "PNG") -> bytes:
        """Return raw bytes of a PIL Image."""
        buf = io.BytesIO()
        img.save(buf, format=fmt)
        return buf.getvalue()

    # ── Internal ──────────────────────────────────────────────────────

    def _resize(self, img: Image.Image) -> Image.Image:
        """Down-scale large screenshots to fit model input limits."""
        max_dim = Config.MAX_IMAGE_DIM
        if img.width <= max_dim and img.height <= max_dim:
            return img
        ratio = min(max_dim / img.width, max_dim / img.height)
        new_size = (int(img.width * ratio), int(img.height * ratio))
        return img.resize(new_size, Image.LANCZOS)

    def _save(self, img: Image.Image) -> Path:
        """Persist screenshot to disk."""
        out_dir = Config.SCREENSHOT_DIR
        out_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = out_dir / f"screenshot_{ts}.png"
        img.save(path, "PNG")
        logger.info("Screenshot saved to %s", path)
        return path
