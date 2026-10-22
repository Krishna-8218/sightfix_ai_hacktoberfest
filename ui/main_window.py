import logging
from pathlib import Path
from typing import Optional
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import QMainWindow, QWidget
from PIL import Image

logger = logging.getLogger(__name__)

class CaptureWorker(QThread):
    finished = Signal(int, object)
    error = Signal(int, str)
    def __init__(self, svc, scan_id: int):
        super().__init__()
        self._svc = svc
        self._scan_id = scan_id
    def run(self):
        try:
            img = self._svc.capture(allow_synthetic_fallback=True)
            self.finished.emit(self._scan_id, img)
        except Exception as e:
            self.error.emit(self._scan_id, str(e))
