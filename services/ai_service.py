import json
import logging
import re
from openai import OpenAI, APIError, APIConnectionError, APITimeoutError
from PIL import Image
from config import Config
from services.screenshot_service import ScreenshotService

logger = logging.getLogger(__name__)

DIAGNOSIS_SYSTEM_PROMPT = """\
You are SightFix AI, an expert desktop troubleshooting assistant.
Analyse the screenshot for visible technical errors or misconfigurations.
Respond ONLY with a JSON object:
{"has_issue": true, "problems": [{"title": "", "evidence": "", "cause": "", "confidence": "high", "solution_steps": [], "commands": [], "verification": ""}], "summary": ""}
"""

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

    def diagnose(self, image: Image.Image) -> dict:
        b64 = self._screenshot_svc.image_to_base64(image)
        client = self._get_client()
        response = client.chat.completions.create(
            model=Config.MODEL,
            messages=[
                {"role": "system", "content": DIAGNOSIS_SYSTEM_PROMPT},
                {"role": "user", "content": [
                    {"type": "text", "text": "Analyse screenshot for errors."},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}}
                ]}
            ],
            temperature=0.2,
            max_tokens=2048,
        )
        return self._parse_response(response)

    @staticmethod
    def _parse_response(response) -> dict:
        raw = response.choices[0].message.content.strip()
        if raw.startswith("```"):
            lines = [l for l in raw.split("\n") if not l.strip().startswith("```")]
            raw = "\n".join(lines).strip()
        match = re.search(r'\{.*\}', raw, re.DOTALL)
        if match:
            return json.loads(match.group())
        return json.loads(raw)
