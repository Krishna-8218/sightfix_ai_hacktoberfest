import json
import logging
from openai import OpenAI
from config import Config
from services.screenshot_service import ScreenshotService

logger = logging.getLogger(__name__)

class AIService:
    def __init__(self):
        self._client: OpenAI | None = None
        self._screenshot_svc = ScreenshotService()

    def _get_client(self) -> OpenAI:
        if self._client is None:
            key = Config.API_KEY.strip() if Config.API_KEY else ""
            self._client = OpenAI(
                base_url=Config.API_BASE,
                api_key=key if key else "ollama",
                timeout=Config.TIMEOUT,
            )
        return self._client
