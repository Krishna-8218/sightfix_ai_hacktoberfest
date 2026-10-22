"""
Test GUI initialization and component workflow in offscreen mode.
"""

import os
import sys
from pathlib import Path

# Set Qt offscreen platform before creating QApplication
os.environ["QT_QPA_PLATFORM"] = "offscreen"

project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from PySide6.QtWidgets import QApplication
from ui.main_window import MainWindow
from ui.styles import STYLESHEET
from config import Config


def test_gui():
    print("Testing GUI initialization...")
    app = QApplication.instance()
    if not app:
        app = QApplication(sys.argv)
    app.setStyleSheet(STYLESHEET)

    window = MainWindow()
    window.show()

    print("Verifying window title & dimensions...")
    assert Config.APP_NAME in window.windowTitle()
    assert window.width() >= 1000
    assert window.height() >= 700

    print("Testing navigation through sidebar...")
    window._navigate(1)  # Settings
    assert window._stack.currentIndex() == 1
    window._navigate(2)  # About
    assert window._stack.currentIndex() == 2
    window._navigate(0)  # Dashboard
    assert window._stack.currentIndex() == 0

    print("Testing Demo mode trigger...")
    window._on_demo()
    assert window._current_status in (window.STATUS_DEMO, window.STATUS_AWAITING)
    assert window._diagnosis_container.isVisible()
    assert window._code_fix_container.isVisible()
    assert window._verification_container.isVisible()
    assert window._current_patch is not None

    print("Testing Demo Code Fix application...")
    window._on_apply_code_fix()
    assert "Demo Mode" in window._code_fix_status.text()
    assert window._btn_undo_fix.isVisible()

    print("Testing Demo verification...")
    window._on_verify()
    assert window._verification_result_container.isVisible()
    assert window._btn_run_script.isVisible()

    print("Processing Qt events...")
    app.processEvents()

    print("All GUI workflow tests PASSED successfully!")


if __name__ == "__main__":
    test_gui()
