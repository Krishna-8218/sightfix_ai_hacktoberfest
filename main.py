"""
SightFix AI — Application Entry Point

Launch the PySide6 desktop application.
"""

import sys
import logging
from pathlib import Path

# Ensure the project root is on sys.path
project_root = Path(__file__).resolve().parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont

from config import Config
from ui.styles import STYLESHEET
from ui.main_window import MainWindow


def setup_logging():
    """Configure structured logging to stderr (never to a file by default)."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
        stream=sys.stderr,
    )
    # Suppress noisy libraries
    logging.getLogger("openai").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)


def main():
    setup_logging()
    logger = logging.getLogger("sightfix")
    logger.info("Starting %s v%s", Config.APP_NAME, Config.APP_VERSION)
    logger.info("Model: %s @ %s", Config.MODEL, Config.API_BASE)

    app = QApplication(sys.argv)
    app.setApplicationName(Config.APP_NAME)
    app.setApplicationVersion(Config.APP_VERSION)

    # Apply global stylesheet
    app.setStyleSheet(STYLESHEET)

    # Set default font
    font = QFont("Segoe UI", 10)
    font.setStyleStrategy(QFont.PreferAntialias)
    app.setFont(font)

    window = MainWindow()
    window.show()
    window.raise_()
    window.activateWindow()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
