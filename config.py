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
