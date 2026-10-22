import os
from pathlib import Path
from dotenv import load_dotenv

_PROJECT_ROOT = Path(__file__).resolve().parent
load_dotenv(_PROJECT_ROOT / ".env")

class Config:
    API_BASE: str = os.getenv("SIGHTFIX_API_BASE", "http://localhost:11434/v1")
    API_KEY: str = os.getenv("SIGHTFIX_API_KEY", "ollama")
    MODEL: str = os.getenv("SIGHTFIX_MODEL", "qwen2.5vl:3b")
    TIMEOUT: int = int(os.getenv("SIGHTFIX_TIMEOUT", "120"))

    MAX_IMAGE_DIM: int = int(os.getenv("SIGHTFIX_MAX_IMAGE_DIM", "1280"))
    SAVE_SCREENSHOTS: bool = os.getenv("SIGHTFIX_SAVE_SCREENSHOTS", "false").lower() == "true"
    SCREENSHOT_DIR: Path = Path(os.getenv("SIGHTFIX_SCREENSHOT_DIR", str(_PROJECT_ROOT / "screenshots")))

    APP_NAME: str = "SightFix AI"
    APP_VERSION: str = "1.0.0"
    APP_DESCRIPTION: str = "AI-Powered Desktop Troubleshooter"

    SAFE_COMMANDS_ALLOWLIST: list[str] = [
        "pip install", "pip list", "python --version", "pip --version",
        "systeminfo", "ipconfig", "hostname", "whoami", "tasklist", "echo",
    ]
