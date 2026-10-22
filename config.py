"""
SightFix AI — Configuration Module

Loads settings from environment variables (.env file) with sensible defaults
for local Ollama + Qwen2.5-VL-7B-Instruct setup.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root
_PROJECT_ROOT = Path(__file__).resolve().parent
load_dotenv(_PROJECT_ROOT / ".env")


class Config:
    """Centralized, immutable-at-read configuration."""

    # ── AI Model ──────────────────────────────────────────────────────
    API_BASE: str = os.getenv("SIGHTFIX_API_BASE", "http://localhost:11434/v1")
    API_KEY: str = os.getenv("SIGHTFIX_API_KEY", "ollama")
    MODEL: str = os.getenv("SIGHTFIX_MODEL", "qwen2.5vl:3b")
    TIMEOUT: int = int(os.getenv("SIGHTFIX_TIMEOUT", "120"))

    # ── Image Processing ──────────────────────────────────────────────
    MAX_IMAGE_DIM: int = int(os.getenv("SIGHTFIX_MAX_IMAGE_DIM", "1280"))

    # ── Screenshot Storage ────────────────────────────────────────────
    SAVE_SCREENSHOTS: bool = os.getenv("SIGHTFIX_SAVE_SCREENSHOTS", "false").lower() == "true"
    SCREENSHOT_DIR: Path = Path(os.getenv("SIGHTFIX_SCREENSHOT_DIR", str(_PROJECT_ROOT / "screenshots")))

    # ── Application Metadata ──────────────────────────────────────────
    APP_NAME: str = "SightFix AI"
    APP_VERSION: str = "1.0.0"
    APP_DESCRIPTION: str = "AI-Powered Desktop Troubleshooter"

    # ── Safety ────────────────────────────────────────────────────────
    # Commands that are explicitly allowed for automated execution.
    # Anything outside this list requires manual user action.
    SAFE_COMMANDS_ALLOWLIST: list[str] = [
        "pip install",
        "pip list",
        "python --version",
        "pip --version",
        "systeminfo",
        "ipconfig",
        "hostname",
        "whoami",
        "tasklist",
        "echo",
    ]

    # Patterns that are always blocked, regardless of allowlist.
    BLOCKED_PATTERNS: list[str] = [
        "rm -rf",
        "del /s",
        "format",
        "shutdown",
        "restart",
        "reg delete",
        "reg add",
        "net user",
        "net localgroup",
        "Set-ExecutionPolicy",
        "Invoke-Expression",
        "iex",
        "Remove-Item -Recurse",
        "Start-Process",
        "runas",
        "sudo",
        "chmod",
        "chown",
        "mkfs",
        "dd if=",
        "> /dev/",
        "powershell -enc",
        "powershell -e ",
        "cmd /c",
        "| bash",
        "| sh",
        "| cmd",
        "curl | ",
        "wget | ",
    ]

    @classmethod
    def is_model_configured(cls) -> bool:
        """Check whether a model endpoint appears to be configured."""
        return bool(cls.API_BASE and cls.MODEL)

    @classmethod
    def summary(cls) -> dict:
        """Return a safe summary of current config (no secrets)."""
        return {
            "api_base": cls.API_BASE,
            "model": cls.MODEL,
            "timeout": cls.TIMEOUT,
            "max_image_dim": cls.MAX_IMAGE_DIM,
            "save_screenshots": cls.SAVE_SCREENSHOTS,
        }
