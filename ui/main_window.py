"""
SightFix AI — Main Window

The complete PySide6 GUI: sidebar, dashboard, file inspection, code repair,
screenshot diagnosis, safe action approval, verification, settings, and about views.
"""

import os
import sys
import logging
from pathlib import Path
from typing import Optional

from PySide6.QtCore import (
    Qt, QThread, Signal, QSize, QTimer,
)
from PySide6.QtGui import QPixmap, QImage, QFont, QGuiApplication
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QStackedWidget, QScrollArea, QFrame,
    QSizePolicy, QProgressBar, QMessageBox, QTextEdit, QLineEdit,
    QFileDialog, QApplication,
)
from PIL import Image

from config import Config
from services.screenshot_service import ScreenshotService
from services.ai_service import AIService
from services.diagnosis_service import DiagnosisService, Diagnosis, Problem, VerificationResult
from services.action_service import ActionService
from services.verification_service import VerificationService
from services.code_service import CodeService, FileInspectionResult, CodePatch

logger = logging.getLogger(__name__)


# ═════════════════════════════════════════════════════════════════════
#  Background Workers (QThread)
# ═════════════════════════════════════════════════════════════════════

class CaptureWorker(QThread):
    """Captures a screenshot in a background thread."""
    finished = Signal(int, object)  # scan_id, PIL Image or None
    error = Signal(int, str)

    def __init__(self, svc: ScreenshotService, scan_id: int):
        super().__init__()
        self._svc = svc
        self._scan_id = scan_id

    def run(self):
        try:
            img = self._svc.capture(allow_synthetic_fallback=True)
            self.finished.emit(self._scan_id, img)
        except Exception as e:
            self.error.emit(self._scan_id, str(e))


class DiagnoseWorker(QThread):
    """Runs AI vision diagnosis in a background thread."""
    finished = Signal(int, object)  # scan_id, raw dict
    error = Signal(int, str)

    def __init__(self, ai_svc: AIService, image: Image.Image, scan_id: int):
        super().__init__()
        self._ai = ai_svc
        self._image = image
        self._scan_id = scan_id

    def run(self):
        try:
            result = self._ai.diagnose(self._image)
            self.finished.emit(self._scan_id, result)
        except Exception as e:
            self.error.emit(self._scan_id, str(e))


class InspectFileWorker(QThread):
    """Inspects a source file directly from disk, runs py_compile, and asks AI for patch."""
    finished = Signal(int, object)  # scan_id, Diagnosis
    error = Signal(int, str)

    def __init__(self, ai_svc: AIService, file_path: Path, scan_id: int):
        super().__init__()
        self._ai = ai_svc
        self._file_path = file_path
        self._scan_id = scan_id

    def run(self):
        try:
            # 1. Read directly from disk & run py_compile
            inspection = CodeService.inspect_file(self._file_path)

            patch = None
            ai_diag = ""

            # 2. If compiler error found, request code repair
            if inspection.has_error and inspection.compiler_result.has_error:
                cr = inspection.compiler_result
                res = self._ai.repair_code(
                    file_path=str(self._file_path),
                    file_content=inspection.file_content,
                    compiler_output=cr.stderr or cr.error_msg,
                    error_line=cr.error_line,
                )

                if res.get("has_fix") and res.get("original_code") and res.get("replacement_code"):
                    patch = CodeService.validate_patch(
                        file_path=self._file_path,
                        original_code=res.get("original_code", ""),
                        replacement_code=res.get("replacement_code", ""),
                        affected_line=res.get("affected_line") or cr.error_line or 1,
                        explanation=res.get("explanation", ""),
                        expected_hash=inspection.content_hash,
                    )
                    ai_diag = res.get("diagnosis", "")

            # 3. Create fresh diagnosis bound to this file only
            diag = DiagnosisService.create_file_diagnosis(
                inspection=inspection,
                patch=patch,
                ai_diag_text=ai_diag,
            )
            self.finished.emit(self._scan_id, diag)

        except Exception as e:
            logger.exception("InspectFileWorker failed")
            self.error.emit(self._scan_id, str(e))


class VerifyWorker(QThread):
    """Runs screenshot verification analysis in a background thread."""
    finished = Signal(int, object)  # scan_id, raw dict
    error = Signal(int, str)

    def __init__(self, ai_svc: AIService, image: Image.Image, problem_text: str, scan_id: int):
        super().__init__()
        self._ai = ai_svc
        self._image = image
        self._problem_text = problem_text
        self._scan_id = scan_id

    def run(self):
        try:
            result = self._ai.verify(self._image, self._problem_text)
            self.finished.emit(self._scan_id, result)
        except Exception as e:
            self.error.emit(self._scan_id, str(e))


class ConnectionTestWorker(QThread):
    """Tests AI endpoint connectivity in background."""
    finished = Signal(bool, str)

    def __init__(self, ai_svc: AIService):
        super().__init__()
        self._ai = ai_svc

    def run(self):
        ok, msg = self._ai.test_connection()
        self.finished.emit(ok, msg)


# ═════════════════════════════════════════════════════════════════════
#  Helper Functions
# ═════════════════════════════════════════════════════════════════

def _make_label(text: str, cls: str = "", object_name: str = "") -> QLabel:
    lbl = QLabel(text)
    if cls:
        lbl.setProperty("class", cls)
    if object_name:
        lbl.setObjectName(object_name)
    lbl.setWordWrap(True)
    return lbl


def _make_card() -> QFrame:
    frame = QFrame()
    frame.setProperty("class", "card")
    return frame


def _make_divider() -> QFrame:
    div = QFrame()
    div.setObjectName("sidebarDivider")
    div.setFixedHeight(1)
    return div


def _icon_text(icon_char: str, text: str) -> str:
    return f"  {icon_char}   {text}"


# ═════════════════════════════════════════════════════════════════════
#  Main Window
# ═════════════════════════════════════════════════════════════════════

class MainWindow(QMainWindow):
    """The main SightFix AI application window."""

    STATUS_IDLE = "idle"
    STATUS_CAPTURING = "capturing"
    STATUS_ANALYZING = "analyzing"
    STATUS_AWAITING = "awaiting_approval"
    STATUS_EXECUTING = "executing"
    STATUS_VERIFIED = "verified"
    STATUS_FAILED = "failed"
    STATUS_DEMO = "demo"

    STATUS_LABELS = {
        "idle": "● Idle",
        "capturing": "◉ Capturing…",
        "analyzing": "◉ Analyzing…",
        "awaiting_approval": "◉ Awaiting Approval",
        "executing": "◉ Executing…",
        "verified": "● Verified",
        "failed": "● Failed",
        "demo": "◉ Demo Mode",
    }

    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{Config.APP_NAME} — {Config.APP_DESCRIPTION}")
        self.setMinimumSize(1100, 750)
        self.resize(1280, 850)

        # Services
        self._screenshot_svc = ScreenshotService()
        self._ai_svc = AIService()
        self._diag_svc = DiagnosisService()
        self._action_svc = ActionService()
        self._code_svc = CodeService()

        # State management (Scan ID prevents race conditions & stale responses)
        self._scan_id: int = 0
        self._selected_file: Optional[Path] = None
        self._current_image: Optional[Image.Image] = None
        self._current_diagnosis: Optional[Diagnosis] = None
        self._current_patch: Optional[CodePatch] = None
        self._current_status = self.STATUS_IDLE
        self._worker = None

        # Build UI
        self._build_ui()
        self._set_status(self.STATUS_IDLE)

    # ─── UI Construction ──────────────────────────────────────────

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)

        root_layout = QHBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        root_layout.addWidget(self._build_sidebar())

        self._stack = QStackedWidget()
        root_layout.addWidget(self._stack, 1)

        self._page_dashboard = self._build_dashboard_page()
        self._page_settings = self._build_settings_page()
        self._page_about = self._build_about_page()

        self._stack.addWidget(self._page_dashboard)
        self._stack.addWidget(self._page_settings)
        self._stack.addWidget(self._page_about)

        self._stack.setCurrentWidget(self._page_dashboard)

    # ─── Sidebar ──────────────────────────────────────────────────

    def _build_sidebar(self) -> QWidget:
        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        lay = QVBoxLayout(sidebar)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(2)

        title = QLabel("🔍 SightFix")
        title.setObjectName("appTitle")
        lay.addWidget(title)

        subtitle = QLabel("AI Desktop Troubleshooter")
        subtitle.setObjectName("appSubtitle")
        lay.addWidget(subtitle)

        lay.addWidget(_make_divider())

        self._nav_buttons: list[QPushButton] = []

        btn_dash = QPushButton(_icon_text("🏠", "Dashboard"))
        btn_dash.setCheckable(True)
        btn_dash.setChecked(True)
        btn_dash.clicked.connect(lambda: self._navigate(0))
        lay.addWidget(btn_dash)
        self._nav_buttons.append(btn_dash)

        btn_settings = QPushButton(_icon_text("⚙️", "Settings"))
        btn_settings.setCheckable(True)
        btn_settings.clicked.connect(lambda: self._navigate(1))
        lay.addWidget(btn_settings)
        self._nav_buttons.append(btn_settings)

        btn_about = QPushButton(_icon_text("ℹ️", "About"))
        btn_about.setCheckable(True)
        btn_about.clicked.connect(lambda: self._navigate(2))
        lay.addWidget(btn_about)
        self._nav_buttons.append(btn_about)

        lay.addWidget(_make_divider())

        self._status_badge = QLabel("● Idle")
        self._status_badge.setObjectName("statusBadge")
        self._status_badge.setAlignment(Qt.AlignCenter)
        lay.addWidget(self._status_badge)

        self._conn_label = QLabel("")
        self._conn_label.setObjectName("appSubtitle")
        self._conn_label.setAlignment(Qt.AlignCenter)
        self._conn_label.setWordWrap(True)
        lay.addWidget(self._conn_label)

        lay.addStretch(1)

        ver = QLabel(f"v{Config.APP_VERSION}")
        ver.setObjectName("appSubtitle")
        ver.setAlignment(Qt.AlignCenter)
        lay.addWidget(ver)
        lay.addSpacing(12)

        return sidebar

    def _navigate(self, index: int):
        for i, btn in enumerate(self._nav_buttons):
            btn.setChecked(i == index)
        self._stack.setCurrentIndex(index)

    # ─── Dashboard Page ───────────────────────────────────────────

    def _build_dashboard_page(self) -> QWidget:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        container = QWidget()
        lay = QVBoxLayout(container)
        lay.setContentsMargins(32, 28, 32, 28)
        lay.setSpacing(20)

        heading = _make_label(f"Welcome to {Config.APP_NAME}", "heading")
        lay.addWidget(heading)

        sub = _make_label(
            "Inspect a specific source file for real compiler errors and patches, "
            "or capture your screen for visual diagnosis.",
            "subheading",
        )
        lay.addWidget(sub)

        # Status row
        status_row = QHBoxLayout()
        status_row.setSpacing(12)

        self._card_model = self._info_card("AI Model", Config.MODEL, "🤖")
        status_row.addWidget(self._card_model)

        self._card_endpoint = self._info_card("Endpoint", Config.API_BASE, "🌐")
        status_row.addWidget(self._card_endpoint)

        self._card_status_info = self._info_card("Status", "Ready", "📡")
        status_row.addWidget(self._card_status_info)

        lay.addLayout(status_row)

        # ── Action Buttons Row ──
        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)

        self._btn_inspect_file = QPushButton("📂  Inspect Current File")
        self._btn_inspect_file.setObjectName("btnInspectFile")
        self._btn_inspect_file.setToolTip("Select a source file to compile and generate a real code repair patch")
        self._btn_inspect_file.clicked.connect(self._on_inspect_file)
        btn_row.addWidget(self._btn_inspect_file)

        self._btn_diagnose = QPushButton("🔍  Diagnose My Screen")
        self._btn_diagnose.setObjectName("btnDiagnose")
        self._btn_diagnose.setToolTip("Capture desktop screenshot and diagnose visual issues")
        self._btn_diagnose.clicked.connect(self._on_diagnose)
        btn_row.addWidget(self._btn_diagnose)

        self._btn_demo = QPushButton("🎮  Run Demo")
        self._btn_demo.setObjectName("btnDemo")
        self._btn_demo.setToolTip("Simulate real syntax repair on calculate_total.py")
        self._btn_demo.clicked.connect(self._on_demo)
        btn_row.addWidget(self._btn_demo)

        lay.addLayout(btn_row)

        # ── Selected File Banner (Always displays absolute path) ──
        self._file_banner = QFrame()
        self._file_banner.setObjectName("fileSelectionBanner")
        self._file_banner.setVisible(False)
        fb_lay = QHBoxLayout(self._file_banner)
        fb_lay.setContentsMargins(12, 8, 12, 8)
        self._file_banner_icon = QLabel("📄")
        fb_lay.addWidget(self._file_banner_icon)
        self._file_banner_text = _make_label("No file selected", "sectionTitle")
        fb_lay.addWidget(self._file_banner_text, 1)
        self._file_banner_status = QLabel("")
        self._file_banner_status.setProperty("class", "badge")
        fb_lay.addWidget(self._file_banner_status)
        lay.addWidget(self._file_banner)

        # ── Progress bar ──
        self._progress = QProgressBar()
        self._progress.setRange(0, 0)
        self._progress.setVisible(False)
        self._progress.setFixedHeight(4)
        lay.addWidget(self._progress)

        # ── Screenshot area (collapsible when inspecting file) ──
        self._screenshot_box = QWidget()
        sb_lay = QVBoxLayout(self._screenshot_box)
        sb_lay.setContentsMargins(0, 0, 0, 0)
        sb_lay.setSpacing(6)

        self._screenshot_label = QLabel("No screenshot captured yet.\nClick 'Diagnose My Screen' above to capture.")
        self._screenshot_label.setObjectName("screenshotPreview")
        self._screenshot_label.setAlignment(Qt.AlignCenter)
        self._screenshot_label.setMinimumHeight(200)
        self._screenshot_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        sb_lay.addWidget(self._screenshot_label)

        ts_row = QHBoxLayout()
        self._ts_label = QLabel("")
        self._ts_label.setProperty("class", "subheading")
        ts_row.addWidget(self._ts_label)
        ts_row.addStretch()

        self._btn_retake = QPushButton("↻  Retake Screenshot")
        self._btn_retake.setObjectName("btnRetake")
        self._btn_retake.setVisible(False)
        self._btn_retake.clicked.connect(self._on_capture)
        ts_row.addWidget(self._btn_retake)
        sb_lay.addLayout(ts_row)

        lay.addWidget(self._screenshot_box)

        # ── 1. Diagnosis Results Panel ──
        self._diagnosis_container = QWidget()
        self._diagnosis_container.setVisible(False)
        self._build_diagnosis_ui(self._diagnosis_container)
        lay.addWidget(self._diagnosis_container)

        # ── 2. Proposed Code Fix Panel (Core Feature) ──
        self._code_fix_container = QWidget()
        self._code_fix_container.setVisible(False)
        self._build_code_fix_ui(self._code_fix_container)
        lay.addWidget(self._code_fix_container)

        # ── 3. Shell Actions Panel (For non-code shell commands) ──
        self._action_container = QWidget()
        self._action_container.setVisible(False)
        self._build_action_ui(self._action_container)
        lay.addWidget(self._action_container)

        # ── 4. Verification & Validation Panel ──
        self._verification_container = QWidget()
        self._verification_container.setVisible(False)
        self._build_verification_ui(self._verification_container)
        lay.addWidget(self._verification_container)

        lay.addStretch()
        scroll.setWidget(container)
        return scroll

    def _info_card(self, title: str, value: str, icon: str) -> QFrame:
        card = _make_card()
        lay = QVBoxLayout(card)
        lay.setSpacing(4)

        header = QHBoxLayout()
        header.addWidget(_make_label(icon))
        header.addWidget(_make_label(title, "sectionSubtitle"))
        header.addStretch()
        lay.addLayout(header)

        val_label = _make_label(value, "sectionTitle")
        val_label.setObjectName(f"card_{title.lower().replace(' ', '_')}_value")
        lay.addWidget(val_label)
        card._value_label = val_label
        return card

    # ─── Fresh State Reset (Prevents Stale Diagnosis) ─────────────

    def _reset_scan_state(self) -> int:
        """
        Increment scan_id and purge all previous diagnosis, patches,
        evidence, commands, and verification results.
        Returns the new active scan_id.
        """
        self._scan_id += 1
        active_scan = self._scan_id

        # Clear state
        self._current_diagnosis = None
        self._current_patch = None

        # Reset UI panels
        self._diagnosis_container.setVisible(False)
        self._code_fix_container.setVisible(False)
        self._action_container.setVisible(False)
        self._verification_container.setVisible(False)
        self._verification_result_container.setVisible(False)
        self._exec_output.setVisible(False)
        self._exec_output.clear()
        self._diff_viewer.clear()
        self._btn_undo_fix.setVisible(False)
        self._btn_run_script.setVisible(False)

        # Clear problem cards
        while self._problems_layout.count():
            item = self._problems_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Clear verification layout
        while self._verification_result_layout.count():
            item = self._verification_result_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self._progress.setVisible(True)
        return active_scan

    # ─── Diagnosis UI ─────────────────────────────────────────────

    def _build_diagnosis_ui(self, parent: QWidget):
        lay = QVBoxLayout(parent)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(12)

        self._demo_banner = QLabel("⚡ DEMO MODE — This is a simulated diagnosis and code repair.")
        self._demo_banner.setObjectName("demoBanner")
        self._demo_banner.setAlignment(Qt.AlignCenter)
        self._demo_banner.setVisible(False)
        lay.addWidget(self._demo_banner)

        header_row = QHBoxLayout()
        header_row.addWidget(_make_label("Diagnosis Results", "sectionTitle"))
        header_row.addStretch()
        self._confidence_badge = QLabel("")
        self._confidence_badge.setProperty("class", "badge")
        header_row.addWidget(self._confidence_badge)
        lay.addLayout(header_row)

        self._summary_label = _make_label("", "subheading")
        lay.addWidget(self._summary_label)

        self._problems_layout = QVBoxLayout()
        self._problems_layout.setSpacing(12)
        lay.addLayout(self._problems_layout)

    def _display_diagnosis(self, diag: Diagnosis):
        self._current_diagnosis = diag
        self._demo_banner.setVisible(diag.is_demo)
        self._summary_label.setText(diag.summary)

        # Clear previous problems
        while self._problems_layout.count():
            item = self._problems_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not diag.has_issue:
            self._confidence_badge.setText("✅ Clean (No Errors)")
            self._confidence_badge.setProperty("class", "badge badgeLow")
            self._confidence_badge.style().unpolish(self._confidence_badge)
            self._confidence_badge.style().polish(self._confidence_badge)
            self._diagnosis_container.setVisible(True)
            self._code_fix_container.setVisible(False)
            self._action_container.setVisible(False)
            self._set_status(self.STATUS_IDLE)
            return

        for i, prob in enumerate(diag.problems, 1):
            card = self._build_problem_card(i, prob)
            self._problems_layout.addWidget(card)

        if diag.problems:
            conf = diag.problems[0].confidence
            badge_cls = {
                "high": "badge badgeHigh",
                "medium": "badge badgeMedium",
                "low": "badge badgeLow",
            }.get(conf, "badge")
            self._confidence_badge.setText(f"Confidence: {conf.upper()}")
            self._confidence_badge.setProperty("class", badge_cls)
            self._confidence_badge.style().unpolish(self._confidence_badge)
            self._confidence_badge.style().polish(self._confidence_badge)

        self._diagnosis_container.setVisible(True)

        # Check for Code Patch
        if diag.code_patch and diag.code_patch.is_valid:
            self._display_code_patch(diag.code_patch)
            self._code_fix_container.setVisible(True)
            self._set_status(self.STATUS_AWAITING)
        else:
            self._code_fix_container.setVisible(False)

        # Check for Shell Commands (only shown if commands actually exist!)
        has_commands = any(p.commands for p in diag.problems)
        if has_commands:
            self._populate_action_panel(diag)
            self._action_container.setVisible(True)
            if not diag.code_patch:
                self._set_status(self.STATUS_AWAITING)
        else:
            self._action_container.setVisible(False)

        # Verification container ready
        self._verification_container.setVisible(True)

    def _build_problem_card(self, index: int, prob: Problem) -> QFrame:
        card = QFrame()
        card.setObjectName("problemCard")
        lay = QVBoxLayout(card)
        lay.setSpacing(8)

        lay.addWidget(_make_label(f"Problem {index}: {prob.title}", "sectionTitle"))

        if prob.evidence:
            lay.addWidget(_make_label("Evidence / Diagnostic Output:", "sectionSubtitle"))
            ev = QLabel(prob.evidence)
            ev.setObjectName("evidenceBox")
            ev.setWordWrap(True)
            ev.setTextInteractionFlags(Qt.TextSelectableByMouse)
            lay.addWidget(ev)

        if prob.cause:
            lay.addWidget(_make_label("Cause:", "sectionSubtitle"))
            lay.addWidget(_make_label(prob.cause))

        if prob.solution_steps:
            lay.addWidget(_make_label("Recommended Steps:", "sectionSubtitle"))
            steps_text = "\n".join(f"  {i}. {s}" for i, s in enumerate(prob.solution_steps, 1))
            steps_lbl = _make_label(steps_text)
            steps_lbl.setTextInteractionFlags(Qt.TextSelectableByMouse)
            lay.addWidget(steps_lbl)

        if prob.commands:
            lay.addWidget(_make_label("Diagnostic Commands:", "sectionSubtitle"))
            for cmd in prob.commands:
                cmd_lbl = QLabel(f"$ {cmd}")
                cmd_lbl.setObjectName("commandBox")
                cmd_lbl.setTextInteractionFlags(Qt.TextSelectableByMouse)
                lay.addWidget(cmd_lbl)

        if prob.verification:
            lay.addWidget(_make_label("Verification Target:", "sectionSubtitle"))
            lay.addWidget(_make_label(prob.verification))

        return card

    # ─── Proposed Code Fix UI ─────────────────────────────────────

    def _build_code_fix_ui(self, parent: QWidget):
        lay = QVBoxLayout(parent)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(12)

        card = QFrame()
        card.setObjectName("codeFixCard")
        c_lay = QVBoxLayout(card)
        c_lay.setSpacing(10)

        # Header
        hdr = QHBoxLayout()
        hdr.addWidget(_make_label("🛠️  Proposed Code Fix", "sectionTitle"))
        hdr.addStretch()
        self._code_fix_line_badge = QLabel("")
        self._code_fix_line_badge.setProperty("class", "badge badgeHigh")
        hdr.addWidget(self._code_fix_line_badge)
        c_lay.addLayout(hdr)

        self._code_fix_file_label = _make_label("", "subheading")
        c_lay.addWidget(self._code_fix_file_label)

        self._code_fix_explanation = _make_label("", "")
        c_lay.addWidget(self._code_fix_explanation)

        # Diff View
        c_lay.addWidget(_make_label("Unified Diff (Review changes before applying):", "sectionSubtitle"))
        self._diff_viewer = QTextEdit()
        self._diff_viewer.setObjectName("diffViewer")
        self._diff_viewer.setReadOnly(True)
        self._diff_viewer.setMinimumHeight(130)
        c_lay.addWidget(self._diff_viewer)

        # Actions
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        self._btn_apply_fix = QPushButton("✓  Apply Fix")
        self._btn_apply_fix.setObjectName("btnApplyFix")
        self._btn_apply_fix.clicked.connect(self._on_apply_code_fix)
        btn_row.addWidget(self._btn_apply_fix)

        self._btn_reject_fix = QPushButton("✕  Reject")
        self._btn_reject_fix.setObjectName("btnReject")
        self._btn_reject_fix.clicked.connect(self._on_reject_code_fix)
        btn_row.addWidget(self._btn_reject_fix)

        self._btn_copy_fix = QPushButton("📋  Copy Fix")
        self._btn_copy_fix.setObjectName("btnCopy")
        self._btn_copy_fix.clicked.connect(self._on_copy_code_fix)
        btn_row.addWidget(self._btn_copy_fix)

        self._btn_undo_fix = QPushButton("↩  Undo Fix")
        self._btn_undo_fix.setObjectName("btnUndoFix")
        self._btn_undo_fix.setVisible(False)
        self._btn_undo_fix.clicked.connect(self._on_undo_code_fix)
        btn_row.addWidget(self._btn_undo_fix)

        btn_row.addStretch()
        c_lay.addLayout(btn_row)

        self._code_fix_status = _make_label("", "subheading")
        c_lay.addWidget(self._code_fix_status)

        lay.addWidget(card)

    def _display_code_patch(self, patch: CodePatch):
        """Render the proposed patch with unified diff and explanation."""
        self._current_patch = patch
        self._code_fix_line_badge.setText(f"Line {patch.affected_line}")
        self._code_fix_file_label.setText(f"Target: {patch.file_path}")
        self._code_fix_explanation.setText(f"Explanation: {patch.explanation}")

        # Render styled diff
        diff_text = patch.diff if patch.diff else (
            f"--- {patch.file_path} (original)\n"
            f"+++ {patch.file_path} (replacement)\n"
            f"- {patch.original_code}\n"
            f"+ {patch.replacement_code}"
        )
        self._diff_viewer.setPlainText(diff_text)

        self._btn_apply_fix.setEnabled(True)
        self._btn_apply_fix.setText("✓  Apply Fix")
        self._btn_undo_fix.setVisible(False)
        self._code_fix_status.setText("Awaiting user approval before applying changes to disk.")

    # ─── Code Fix Handlers ────────────────────────────────────────

    def _on_apply_code_fix(self):
        """Apply the validated patch to disk, creating a backup."""
        if not self._current_patch:
            return

        target_file = Path(self._current_patch.file_path)
        if not target_file.is_absolute() and self._selected_file:
            target_file = self._selected_file

        # In demo mode, simulate application
        if self._current_diagnosis and self._current_diagnosis.is_demo:
            self._code_fix_status.setText("🎮 Demo Mode — Simulated fix applied! Backup created.")
            self._btn_apply_fix.setEnabled(False)
            self._btn_undo_fix.setVisible(True)
            self._set_status(self.STATUS_VERIFIED)
            return

        success, msg = CodeService.apply_patch(target_file, self._current_patch)
        if success:
            self._code_fix_status.setText(f"✅ {msg}")
            self._btn_apply_fix.setEnabled(False)
            self._btn_undo_fix.setVisible(True)
            self._btn_verify.setEnabled(True)
            self._set_status(self.STATUS_EXECUTING)
            # Prompt user to verify
            QTimer.singleShot(400, self._on_verify)
        else:
            self._code_fix_status.setText(f"❌ Failed to apply patch: {msg}")
            QMessageBox.warning(self, "Patch Application Failed", msg)

    def _on_reject_code_fix(self):
        """User rejects the patch. Discard patch without modifying file."""
        self._code_fix_container.setVisible(False)
        self._code_fix_status.setText("Patch rejected by user. File was not modified.")
        self._set_status(self.STATUS_IDLE)

    def _on_copy_code_fix(self):
        """Copy the replacement code and diff to clipboard."""
        if not self._current_patch:
            return
        text = (
            f"File: {self._current_patch.file_path} (Line {self._current_patch.affected_line})\n"
            f"Original:\n{self._current_patch.original_code}\n\n"
            f"Replacement:\n{self._current_patch.replacement_code}\n\n"
            f"Diff:\n{self._current_patch.diff}"
        )
        QGuiApplication.clipboard().setText(text)
        self._btn_copy_fix.setText("✅ Copied!")
        QTimer.singleShot(2000, lambda: self._btn_copy_fix.setText("📋  Copy Fix"))

    def _on_undo_code_fix(self):
        """Restore file from backup."""
        if not self._current_patch:
            return
        target_file = Path(self._current_patch.file_path)
        if not target_file.is_absolute() and self._selected_file:
            target_file = self._selected_file

        success, msg = CodeService.restore_backup(target_file)
        if success:
            self._code_fix_status.setText(f"↩ {msg}")
            self._btn_undo_fix.setVisible(False)
            self._btn_apply_fix.setEnabled(True)
            self._set_status(self.STATUS_IDLE)
        else:
            QMessageBox.warning(self, "Restore Failed", msg)

    # ─── Inspect File Action ──────────────────────────────────────

    def _on_inspect_file(self):
        """Prompt user to select a source file directly and run compiler diagnosis."""
        start_dir = str(self._selected_file.parent) if self._selected_file else str(Path.cwd())
        file_path_str, _ = QFileDialog.getOpenFileName(
            self,
            "Select Source File to Inspect",
            start_dir,
            "Python Files (*.py);;All Files (*.*)",
        )
        if not file_path_str:
            return

        file_path = Path(file_path_str).resolve()
        self._selected_file = file_path

        # 1. Update selection banner with absolute path immediately
        self._file_banner.setVisible(True)
        self._file_banner_text.setText(f"Selected File: {file_path}")
        self._file_banner_status.setText("Reading from disk…")
        self._file_banner_status.setProperty("class", "badge badgeMedium")
        self._file_banner_status.style().unpolish(self._file_banner_status)
        self._file_banner_status.style().polish(self._file_banner_status)

        # 2. Reset previous state
        scan_id = self._reset_scan_state()
        self._set_status(self.STATUS_ANALYZING)
        self._btn_inspect_file.setEnabled(False)
        self._btn_diagnose.setEnabled(False)
        self._btn_demo.setEnabled(False)

        # 3. Collapse screenshot preview to give full focus to file inspection
        self._screenshot_box.setVisible(False)

        # 4. Start background worker
        worker = InspectFileWorker(self._ai_svc, file_path, scan_id)
        worker.finished.connect(self._on_file_inspection_done)
        worker.error.connect(self._on_file_inspection_error)
        self._worker = worker
        worker.start()

    def _on_file_inspection_done(self, scan_id: int, diag: Diagnosis):
        if scan_id != self._scan_id:
            logger.info("Ignoring stale file inspection result (scan_id=%d, current=%d)", scan_id, self._scan_id)
            return

        self._progress.setVisible(False)
        self._btn_inspect_file.setEnabled(True)
        self._btn_diagnose.setEnabled(True)
        self._btn_demo.setEnabled(True)

        if diag.has_issue:
            self._file_banner_status.setText("❌ Syntax Error")
            self._file_banner_status.setProperty("class", "badge badgeHigh")
        else:
            self._file_banner_status.setText("✅ Clean (Passed)")
            self._file_banner_status.setProperty("class", "badge badgeLow")

        self._file_banner_status.style().unpolish(self._file_banner_status)
        self._file_banner_status.style().polish(self._file_banner_status)

        self._display_diagnosis(diag)

    def _on_file_inspection_error(self, scan_id: int, msg: str):
        if scan_id != self._scan_id:
            return

        self._progress.setVisible(False)
        self._btn_inspect_file.setEnabled(True)
        self._btn_diagnose.setEnabled(True)
        self._btn_demo.setEnabled(True)
        self._set_status(self.STATUS_FAILED)

        self._file_banner_status.setText("Inspection Error")
        self._file_banner_status.setProperty("class", "badge badgeHigh")
        QMessageBox.warning(self, "File Inspection Error", f"Failed to inspect file:\n\n{msg}")

    # ─── Screen Diagnosis Handlers ────────────────────────────────

    def _on_diagnose(self):
        """Full screen capture workflow."""
        scan_id = self._reset_scan_state()
        self._selected_file = None
        self._file_banner.setVisible(False)
        self._screenshot_box.setVisible(True)

        self._set_status(self.STATUS_CAPTURING)
        self._btn_diagnose.setEnabled(False)
        self._btn_inspect_file.setEnabled(False)
        self._btn_demo.setEnabled(False)

        self.showMinimized()
        QTimer.singleShot(600, lambda: self._do_capture_for_diagnosis(scan_id))

    def _do_capture_for_diagnosis(self, scan_id: int):
        worker = CaptureWorker(self._screenshot_svc, scan_id)
        worker.finished.connect(self._on_capture_done_then_diagnose)
        worker.error.connect(self._on_capture_error)
        self._worker = worker
        worker.start()

    def _on_capture_done_then_diagnose(self, scan_id: int, image: Image.Image):
        if scan_id != self._scan_id:
            return

        self.showNormal()
        self.activateWindow()
        self._current_image = image
        self._show_screenshot(image)
        self._btn_retake.setVisible(True)
        self._ts_label.setText(f"Captured: {self._screenshot_svc.get_last_timestamp()}")

        self._set_status(self.STATUS_ANALYZING)
        worker = DiagnoseWorker(self._ai_svc, image, scan_id)
        worker.finished.connect(self._on_diagnosis_done)
        worker.error.connect(self._on_diagnosis_error)
        self._worker = worker
        worker.start()

    def _on_capture(self):
        scan_id = self._reset_scan_state()
        self.showMinimized()
        QTimer.singleShot(600, lambda: self._do_capture_only(scan_id))

    def _do_capture_only(self, scan_id: int):
        worker = CaptureWorker(self._screenshot_svc, scan_id)
        worker.finished.connect(self._on_capture_only_done)
        worker.error.connect(self._on_capture_error)
        self._worker = worker
        worker.start()

    def _on_capture_only_done(self, scan_id: int, image: Image.Image):
        if scan_id != self._scan_id:
            return

        self.showNormal()
        self.activateWindow()
        self._current_image = image
        self._show_screenshot(image)
        self._ts_label.setText(f"Captured: {self._screenshot_svc.get_last_timestamp()}")
        self._progress.setVisible(False)
        self._set_status(self.STATUS_IDLE)

    def _on_capture_error(self, scan_id: int, msg: str):
        if scan_id != self._scan_id:
            return

        self.showNormal()
        self.activateWindow()
        self._progress.setVisible(False)
        self._btn_diagnose.setEnabled(True)
        self._btn_inspect_file.setEnabled(True)
        self._btn_demo.setEnabled(True)
        self._set_status(self.STATUS_FAILED)
        QMessageBox.critical(self, "Capture Error", f"Failed to capture screenshot:\n\n{msg}")

    def _on_diagnosis_done(self, scan_id: int, raw: dict):
        if scan_id != self._scan_id:
            return

        self._progress.setVisible(False)
        self._btn_diagnose.setEnabled(True)
        self._btn_inspect_file.setEnabled(True)
        self._btn_demo.setEnabled(True)

        diag = self._diag_svc.parse_diagnosis(raw)
        self._display_diagnosis(diag)

    def _on_diagnosis_error(self, scan_id: int, msg: str):
        if scan_id != self._scan_id:
            return

        self._progress.setVisible(False)
        self._btn_diagnose.setEnabled(True)
        self._btn_inspect_file.setEnabled(True)
        self._btn_demo.setEnabled(True)
        self._set_status(self.STATUS_FAILED)
        QMessageBox.warning(
            self, "Analysis Error",
            f"AI analysis failed:\n\n{msg}\n\nCheck your model configuration in Settings."
        )

    # ─── Demo Mode ────────────────────────────────────────────────

    def _on_demo(self):
        """Simulate real syntax repair on calculate_total.py."""
        self._reset_scan_state()
        self._selected_file = Path("calculate_total.py")
        self._set_status(self.STATUS_DEMO)

        self._file_banner.setVisible(True)
        self._file_banner_text.setText("Selected File: calculate_total.py (Simulated Demo)")
        self._file_banner_status.setText("SyntaxError Line 1")
        self._file_banner_status.setProperty("class", "badge badgeHigh")
        self._file_banner_status.style().unpolish(self._file_banner_status)
        self._file_banner_status.style().polish(self._file_banner_status)

        self._screenshot_box.setVisible(False)

        diag = self._diag_svc.get_demo_diagnosis()
        self._display_diagnosis(diag)
        self._progress.setVisible(False)

    # ─── Verification Panel ───────────────────────────────────────

    def _build_verification_ui(self, parent: QWidget):
        lay = QVBoxLayout(parent)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(12)

        hdr = QHBoxLayout()
        hdr.addWidget(_make_label("Verification & Validation", "sectionTitle"))
        hdr.addStretch()
        lay.addLayout(hdr)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        self._btn_verify = QPushButton("🔄  Verify Fix (Compiler Check)")
        self._btn_verify.setObjectName("btnVerify")
        self._btn_verify.clicked.connect(self._on_verify)
        btn_row.addWidget(self._btn_verify)

        self._btn_run_script = QPushButton("▶  Run Script to Test Output")
        self._btn_run_script.setObjectName("btnRunScript")
        self._btn_run_script.setVisible(False)
        self._btn_run_script.clicked.connect(self._on_run_script)
        btn_row.addWidget(self._btn_run_script)

        btn_row.addStretch()
        lay.addLayout(btn_row)

        self._verification_result_container = QWidget()
        self._verification_result_layout = QVBoxLayout(self._verification_result_container)
        self._verification_result_layout.setContentsMargins(0, 0, 0, 0)
        self._verification_result_container.setVisible(False)
        lay.addWidget(self._verification_result_container)

    def _on_verify(self):
        """
        Verify the fix.
        If inspecting a file: runs python -m py_compile on that exact file.
        If diagnosing screen: takes a new screenshot and compares with AI.
        """
        # Clear previous verification results
        while self._verification_result_layout.count():
            item = self._verification_result_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # 1. File verification mode
        if self._selected_file:
            if self._current_diagnosis and self._current_diagnosis.is_demo:
                # Simulated demo verification
                panel = QFrame()
                panel.setObjectName("verificationResolved")
                p_lay = QVBoxLayout(panel)
                p_lay.addWidget(_make_label("✅ Syntax check passed (exit code 0)", "sectionTitle"))
                p_lay.addWidget(_make_label(
                    "Compiler check 'python -m py_compile calculate_total.py' exited with 0.\n"
                    "Syntax validation confirmed. Click 'Run Script' to verify runtime correctness."
                ))
                self._verification_result_layout.addWidget(panel)
                self._verification_result_container.setVisible(True)
                self._btn_run_script.setVisible(True)
                self._set_status(self.STATUS_VERIFIED)
                return

            # Real compilation check
            cr = CodeService.compile_check(self._selected_file)
            panel = QFrame()

            if not cr.has_error:
                panel.setObjectName("verificationResolved")
                p_lay = QVBoxLayout(panel)
                p_lay.addWidget(_make_label(f"✅ Syntax check passed (exit code {cr.exit_code})", "sectionTitle"))
                p_lay.addWidget(_make_label(
                    f"File '{self._selected_file.name}' compiled successfully with no syntax errors.\n"
                    "Note: Syntax validation alone does not prove runtime correctness. "
                    "Click 'Run Script' below to execute."
                ))
                self._btn_run_script.setVisible(True)
                self._set_status(self.STATUS_VERIFIED)
            else:
                panel.setObjectName("verificationFailed")
                p_lay = QVBoxLayout(panel)
                p_lay.addWidget(_make_label(f"❌ Syntax error persists (exit code {cr.exit_code})", "sectionTitle"))
                p_lay.addWidget(_make_label(cr.stderr or cr.error_msg))
                self._btn_run_script.setVisible(False)
                self._set_status(self.STATUS_FAILED)

            self._verification_result_layout.addWidget(panel)
            self._verification_result_container.setVisible(True)
            return

        # 2. Screenshot verification mode
        scan_id = self._reset_scan_state()
        self._set_status(self.STATUS_CAPTURING)
        self.showMinimized()
        QTimer.singleShot(600, lambda: self._do_capture_for_verify(scan_id))

    def _do_capture_for_verify(self, scan_id: int):
        worker = CaptureWorker(self._screenshot_svc, scan_id)
        worker.finished.connect(self._on_verify_capture_done)
        worker.error.connect(self._on_capture_error)
        self._worker = worker
        worker.start()

    def _on_verify_capture_done(self, scan_id: int, image: Image.Image):
        if scan_id != self._scan_id:
            return

        self.showNormal()
        self.activateWindow()
        self._show_screenshot(image)

        problem_text = self._summary_label.text() or "Visible screen error"
        self._set_status(self.STATUS_ANALYZING)
        worker = VerifyWorker(self._ai_svc, image, problem_text, scan_id)
        worker.finished.connect(self._on_verify_done)
        worker.error.connect(self._on_verify_error)
        self._worker = worker
        worker.start()

    def _on_verify_done(self, scan_id: int, raw: dict):
        if scan_id != self._scan_id:
            return

        self._progress.setVisible(False)
        res = self._diag_svc.parse_verification(raw)

        panel = QFrame()
        p_lay = QVBoxLayout(panel)
        if res.resolved is True:
            panel.setObjectName("verificationResolved")
            p_lay.addWidget(_make_label("✅ Problem Resolved", "sectionTitle"))
            p_lay.addWidget(_make_label(res.explanation))
            self._set_status(self.STATUS_VERIFIED)
        elif res.resolved is False:
            panel.setObjectName("verificationFailed")
            p_lay.addWidget(_make_label("❌ Problem Persists", "sectionTitle"))
            p_lay.addWidget(_make_label(res.explanation))
            self._set_status(self.STATUS_FAILED)
        else:
            panel.setObjectName("verificationUncertain")
            p_lay.addWidget(_make_label("⚠️ Resolution Uncertain", "sectionTitle"))
            p_lay.addWidget(_make_label(res.explanation))
            self._set_status(self.STATUS_FAILED)

        self._verification_result_layout.addWidget(panel)
        self._verification_result_container.setVisible(True)

    def _on_verify_error(self, scan_id: int, msg: str):
        if scan_id != self._scan_id:
            return
        self._progress.setVisible(False)
        self._set_status(self.STATUS_FAILED)
        QMessageBox.warning(self, "Verification Error", f"Verification request failed: {msg}")

    def _on_run_script(self):
        """Execute the verified script to confirm runtime output."""
        if not self._selected_file:
            return

        if self._current_diagnosis and self._current_diagnosis.is_demo:
            out_box = QTextEdit()
            out_box.setReadOnly(True)
            out_box.setMaximumHeight(90)
            out_box.setPlainText("Process finished with exit code 0\nOutput:\nTotal: 30")
            self._verification_result_layout.addWidget(out_box)
            return

        success, output, code = CodeService.run_python_script(self._selected_file)
        out_box = QTextEdit()
        out_box.setReadOnly(True)
        out_box.setMaximumHeight(110)
        status_line = f"Process finished with exit code {code} ({'SUCCESS' if success else 'FAILED'})\nOutput:\n{output}"
        out_box.setPlainText(status_line)
        self._verification_result_layout.addWidget(out_box)

    # ─── Shell Actions Panel ──────────────────────────────────────

    def _build_action_ui(self, parent: QWidget):
        lay = QVBoxLayout(parent)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(12)

        lay.addWidget(_make_label("Proposed Diagnostic Commands", "sectionTitle"))

        self._action_detail = QTextEdit()
        self._action_detail.setObjectName("commandBox")
        self._action_detail.setReadOnly(True)
        self._action_detail.setMaximumHeight(100)
        lay.addWidget(self._action_detail)

        self._action_safety_label = _make_label("", "subheading")
        lay.addWidget(self._action_safety_label)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        self._btn_approve = QPushButton("✓  Approve & Execute")
        self._btn_approve.setObjectName("btnApprove")
        self._btn_approve.clicked.connect(self._on_approve)
        btn_row.addWidget(self._btn_approve)

        self._btn_reject = QPushButton("✕  Reject")
        self._btn_reject.setObjectName("btnReject")
        self._btn_reject.clicked.connect(self._on_reject)
        btn_row.addWidget(self._btn_reject)

        self._btn_copy = QPushButton("📋  Copy Instructions")
        self._btn_copy.setObjectName("btnCopy")
        self._btn_copy.clicked.connect(self._on_copy_instructions)
        btn_row.addWidget(self._btn_copy)

        lay.addLayout(btn_row)

        self._exec_output = QTextEdit()
        self._exec_output.setReadOnly(True)
        self._exec_output.setMaximumHeight(140)
        self._exec_output.setVisible(False)
        lay.addWidget(self._exec_output)

    def _populate_action_panel(self, diag: Diagnosis):
        all_commands = []
        for p in diag.problems:
            all_commands.extend(p.commands)

        if not all_commands:
            self._action_container.setVisible(False)
            return

        detail = "Commands to execute:\n" + "\n".join(f"  $ {c}" for c in all_commands)
        self._action_detail.setPlainText(detail)

        safe_cmds = []
        unsafe_cmds = []
        for cmd in all_commands:
            ok, reason = self._action_svc.is_safe(cmd)
            if ok:
                safe_cmds.append(cmd)
            else:
                unsafe_cmds.append((cmd, reason))

        if unsafe_cmds:
            reasons = "\n".join(f"• {c}: {r}" for c, r in unsafe_cmds)
            self._action_safety_label.setText(
                f"⚠️ Some commands cannot be auto-executed:\n{reasons}\nUse 'Copy Instructions' to run manually."
            )
            self._btn_approve.setEnabled(bool(safe_cmds))
        else:
            self._action_safety_label.setText("✅ All commands passed safety checks.")
            self._btn_approve.setEnabled(True)

    def _on_approve(self):
        if not self._current_diagnosis:
            return
        self._set_status(self.STATUS_EXECUTING)
        self._exec_output.setVisible(True)
        self._exec_output.clear()

        out_lines = []
        for p in self._current_diagnosis.problems:
            for cmd in p.commands:
                ok, reason = self._action_svc.is_safe(cmd)
                if not ok:
                    out_lines.append(f"⚠️ SKIPPED (Unsafe): {cmd}\n  {reason}")
                    continue
                out_lines.append(f"▶ Executing: {cmd}")
                res = self._action_svc.execute(cmd)
                out_lines.append(f"Output:\n{res.output}\n")

        self._exec_output.setPlainText("\n".join(out_lines))
        self._set_status(self.STATUS_AWAITING)

    def _on_reject(self):
        self._action_container.setVisible(False)
        self._set_status(self.STATUS_IDLE)

    def _on_copy_instructions(self):
        if not self._current_diagnosis:
            return
        lines = [f"Problem: {p.title}\nEvidence: {p.evidence}\nSteps:\n" + "\n".join(p.solution_steps) for p in self._current_diagnosis.problems]
        QGuiApplication.clipboard().setText("\n\n".join(lines))
        self._btn_copy.setText("✅ Copied!")
        QTimer.singleShot(2000, lambda: self._btn_copy.setText("📋  Copy Instructions"))

    # ─── Settings Page ────────────────────────────────────────────

    def _build_settings_page(self) -> QWidget:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        container = QWidget()
        lay = QVBoxLayout(container)
        lay.setContentsMargins(32, 28, 32, 28)
        lay.setSpacing(16)

        lay.addWidget(_make_label("Settings", "heading"))
        lay.addWidget(_make_label("Configure your AI model endpoint.", "subheading"))

        card = _make_card()
        c_lay = QVBoxLayout(card)
        c_lay.setSpacing(12)

        c_lay.addWidget(_make_label("API Base URL", object_name="fieldLabel"))
        self._settings_api_base = QLineEdit(Config.API_BASE)
        c_lay.addWidget(self._settings_api_base)

        c_lay.addWidget(_make_label("API Key", object_name="fieldLabel"))
        self._settings_api_key = QLineEdit(Config.API_KEY)
        self._settings_api_key.setEchoMode(QLineEdit.Password)
        c_lay.addWidget(self._settings_api_key)

        c_lay.addWidget(_make_label("Model Name", object_name="fieldLabel"))
        self._settings_model = QLineEdit(Config.MODEL)
        c_lay.addWidget(self._settings_model)

        c_lay.addWidget(_make_label("Timeout (seconds)", object_name="fieldLabel"))
        self._settings_timeout = QLineEdit(str(Config.TIMEOUT))
        c_lay.addWidget(self._settings_timeout)

        lay.addWidget(card)

        btn_row = QHBoxLayout()
        btn_apply = QPushButton("💾  Apply Settings")
        btn_apply.setFixedHeight(44)
        btn_apply.clicked.connect(self._on_apply_settings)
        btn_row.addWidget(btn_apply)

        btn_test = QPushButton("🔌  Test Connection")
        btn_test.clicked.connect(self._on_test_connection)
        btn_row.addWidget(btn_test)

        lay.addLayout(btn_row)
        self._settings_status = _make_label("", "subheading")
        lay.addWidget(self._settings_status)

        lay.addStretch()
        scroll.setWidget(container)
        return scroll

    def _on_apply_settings(self):
        Config.API_BASE = self._settings_api_base.text().strip()
        Config.API_KEY = self._settings_api_key.text().strip()
        Config.MODEL = self._settings_model.text().strip()
        try:
            Config.TIMEOUT = int(self._settings_timeout.text().strip())
        except ValueError:
            Config.TIMEOUT = 120

        self._ai_svc._client = None
        self._card_model._value_label.setText(Config.MODEL)
        self._card_endpoint._value_label.setText(Config.API_BASE)
        self._settings_status.setText("✅ Settings applied.")

    def _on_test_connection(self):
        self._settings_status.setText("🔄 Testing connection…")
        worker = ConnectionTestWorker(self._ai_svc)
        worker.finished.connect(self._on_connection_test_done)
        self._worker = worker
        worker.start()

    def _on_connection_test_done(self, ok: bool, msg: str):
        if ok:
            self._settings_status.setText(f"✅ {msg}")
            self._conn_label.setText("✅ Connected")
            self._card_status_info._value_label.setText("Connected")
        else:
            self._settings_status.setText(f"❌ {msg}")
            self._conn_label.setText("❌ Disconnected")
            self._card_status_info._value_label.setText("Disconnected")

    # ─── About Page ───────────────────────────────────────────────

    def _build_about_page(self) -> QWidget:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QWidget()
        lay = QVBoxLayout(container)
        lay.setContentsMargins(32, 28, 32, 28)
        lay.setSpacing(12)

        lay.addWidget(_make_label(f"🔍 {Config.APP_NAME}", "heading"))
        lay.addWidget(_make_label(f"Version {Config.APP_VERSION}", "subheading"))

        card = _make_card()
        c_lay = QVBoxLayout(card)
        c_lay.addWidget(_make_label(
            "SightFix AI diagnoses desktop errors and source-code syntax issues, "
            "proposes validated patches, and verifies fixes with real compiler execution."
        ))
        lay.addWidget(card)
        lay.addStretch()
        scroll.setWidget(container)
        return scroll

    # ─── Utilities ────────────────────────────────────────────────

    def _show_screenshot(self, img: Image.Image):
        if img.mode != "RGB":
            img = img.convert("RGB")
        data = img.tobytes("raw", "RGB")
        qimg = QImage(data, img.width, img.height, img.width * 3, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(qimg)
        scaled = pixmap.scaled(
            self._screenshot_label.size(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation,
        )
        self._screenshot_label.setPixmap(scaled)
        self._screenshot_label.setProperty("hasImage", "true")
        self._screenshot_label.style().unpolish(self._screenshot_label)
        self._screenshot_label.style().polish(self._screenshot_label)

    def _set_status(self, status: str):
        self._current_status = status
        label = self.STATUS_LABELS.get(status, status)
        self._status_badge.setText(label)
        self._status_badge.setProperty("status", status)
        self._status_badge.style().unpolish(self._status_badge)
        self._status_badge.style().polish(self._status_badge)
