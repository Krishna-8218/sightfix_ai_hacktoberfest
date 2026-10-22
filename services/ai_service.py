import json
import logging
from openai import OpenAI, APIError, APIConnectionError, APITimeoutError
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

    def test_connection(self) -> tuple[bool, str]:
        try:
            client = self._get_client()
            client.models.list()
            return True, "Connected to AI provider."
        except APIConnectionError:
            return False, f"Cannot reach {Config.API_BASE}. Is the server running?"
        except APIError as exc:
            return False, f"API error: {exc.message}"
        except Exception as exc:
            return False, f"Connection failed: {exc}"
