"""
SightFix AI — Qt Stylesheet

Professional dark-theme stylesheet for a developer-tool aesthetic.
"""

STYLESHEET = """
/* ═══════════════════════════════════════════════════════════════════
   SightFix AI — Dark Theme Stylesheet
   ═══════════════════════════════════════════════════════════════════ */

/* ── Global ─────────────────────────────────────────────────────── */
QWidget {
    background-color: #0d1117;
    color: #c9d1d9;
    font-family: "Segoe UI", "Inter", "Roboto", sans-serif;
    font-size: 13px;
}

/* ── Main Window ────────────────────────────────────────────────── */
QMainWindow {
    background-color: #0d1117;
}

/* ── Sidebar ────────────────────────────────────────────────────── */
#sidebar {
    background-color: #010409;
    border-right: 1px solid #21262d;
    min-width: 220px;
    max-width: 220px;
}

#sidebar QPushButton {
    background-color: transparent;
    border: none;
    border-radius: 8px;
    color: #8b949e;
    font-size: 13px;
    font-weight: 500;
    padding: 10px 16px;
    text-align: left;
}

#sidebar QPushButton:hover {
    background-color: #161b22;
    color: #c9d1d9;
}

#sidebar QPushButton:checked,
#sidebar QPushButton[active="true"] {
    background-color: #1f6feb22;
    color: #58a6ff;
    font-weight: 600;
}

#appTitle {
    color: #58a6ff;
    font-size: 18px;
    font-weight: 700;
    padding: 20px 16px 4px 16px;
}

#appSubtitle {
    color: #484f58;
    font-size: 11px;
    padding: 0 16px 16px 16px;
}

#sidebarDivider {
    background-color: #21262d;
    max-height: 1px;
    min-height: 1px;
    margin: 8px 16px;
}

/* ── Status Indicator ───────────────────────────────────────────── */
#statusBadge {
    border-radius: 12px;
    font-size: 11px;
    font-weight: 600;
    padding: 4px 12px;
    margin: 4px 16px;
}

#statusBadge[status="idle"] {
    background-color: #1f6feb22;
    color: #58a6ff;
}
#statusBadge[status="capturing"] {
    background-color: #f0883e22;
    color: #f0883e;
}
#statusBadge[status="analyzing"] {
    background-color: #d2a8ff22;
    color: #d2a8ff;
}
#statusBadge[status="awaiting_approval"] {
    background-color: #f0883e22;
    color: #f0883e;
}
#statusBadge[status="executing"] {
    background-color: #f0883e22;
    color: #f0883e;
}
#statusBadge[status="verified"] {
    background-color: #3fb95022;
    color: #3fb950;
}
#statusBadge[status="failed"] {
    background-color: #f8514922;
    color: #f85149;
}
#statusBadge[status="demo"] {
    background-color: #d2a8ff22;
    color: #d2a8ff;
}

/* ── Cards ──────────────────────────────────────────────────────── */
.card {
    background-color: #161b22;
    border: 1px solid #21262d;
    border-radius: 12px;
    padding: 20px;
}

.card:hover {
    border-color: #30363d;
}

/* ── Buttons ────────────────────────────────────────────────────── */
QPushButton {
    background-color: #21262d;
    border: 1px solid #30363d;
    border-radius: 8px;
    color: #c9d1d9;
    font-weight: 600;
    padding: 8px 20px;
    min-height: 28px;
}

QPushButton:hover {
    background-color: #30363d;
    border-color: #484f58;
}

QPushButton:pressed {
    background-color: #1c2028;
}

QPushButton:disabled {
    background-color: #161b22;
    color: #484f58;
    border-color: #21262d;
}

#btnDiagnose {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #1f6feb, stop:1 #388bfd);
    border: none;
    border-radius: 12px;
    color: #ffffff;
    font-size: 16px;
    font-weight: 700;
    min-height: 52px;
    padding: 14px 32px;
}

#btnDiagnose:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #388bfd, stop:1 #58a6ff);
}

#btnDiagnose:pressed {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #1158c7, stop:1 #1f6feb);
}

#btnDiagnose:disabled {
    background: #21262d;
    color: #484f58;
}

#btnDemo {
    background-color: #1c1c2e;
    border: 1px solid #d2a8ff44;
    border-radius: 10px;
    color: #d2a8ff;
    font-size: 13px;
    font-weight: 600;
    min-height: 40px;
    padding: 10px 24px;
}

#btnDemo:hover {
    background-color: #d2a8ff18;
    border-color: #d2a8ff88;
}

#btnApprove {
    background-color: #238636;
    border: 1px solid #2ea043;
    color: #ffffff;
}
#btnApprove:hover {
    background-color: #2ea043;
}

#btnReject {
    background-color: #da3633;
    border: 1px solid #f85149;
    color: #ffffff;
}
#btnReject:hover {
    background-color: #f85149;
}

#btnVerify {
    background-color: #1f6feb;
    border: 1px solid #388bfd;
    color: #ffffff;
    font-size: 14px;
    font-weight: 600;
    min-height: 40px;
}
#btnVerify:hover {
    background-color: #388bfd;
}

#btnCopy {
    background-color: #21262d;
    border: 1px solid #30363d;
    color: #8b949e;
}
#btnCopy:hover {
    color: #c9d1d9;
    border-color: #484f58;
}

#btnRetake {
    background-color: transparent;
    border: 1px solid #30363d;
    color: #8b949e;
    font-size: 12px;
}
#btnInspectFile {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #238636, stop:1 #2ea043);
    border: none;
    border-radius: 12px;
    color: #ffffff;
    font-size: 15px;
    font-weight: 700;
    min-height: 52px;
    padding: 14px 28px;
}

#btnInspectFile:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #2ea043, stop:1 #3fb950);
}

#btnInspectFile:pressed {
    background: #1b6327;
}

#btnInspectFile:disabled {
    background: #21262d;
    color: #484f58;
}

#btnApplyFix {
    background-color: #238636;
    border: 1px solid #2ea043;
    border-radius: 8px;
    color: #ffffff;
    font-size: 14px;
    font-weight: 700;
    min-height: 40px;
    padding: 8px 24px;
}
#btnApplyFix:hover {
    background-color: #2ea043;
}
#btnApplyFix:disabled {
    background-color: #21262d;
    color: #484f58;
    border-color: #30363d;
}

#btnUndoFix {
    background-color: #30363d;
    border: 1px solid #484f58;
    border-radius: 8px;
    color: #c9d1d9;
    font-weight: 600;
    min-height: 36px;
    padding: 6px 16px;
}
#btnUndoFix:hover {
    background-color: #484f58;
}

#btnRunScript {
    background-color: #1f6feb;
    border: 1px solid #388bfd;
    border-radius: 8px;
    color: #ffffff;
    font-weight: 600;
    min-height: 36px;
    padding: 6px 20px;
}
#btnRunScript:hover {
    background-color: #388bfd;
}

#codeFixCard {
    background-color: #0d1117;
    border: 1px solid #388bfd44;
    border-radius: 12px;
    padding: 18px;
}

#diffViewer {
    background-color: #0d1117;
    border: 1px solid #21262d;
    border-radius: 8px;
    color: #c9d1d9;
    font-family: "Cascadia Code", "Consolas", "Courier New", monospace;
    font-size: 12px;
    padding: 12px;
    line-height: 1.4;
}

#fileSelectionBanner {
    background-color: #161b22;
    border: 1px solid #30363d;
    border-radius: 8px;
    padding: 10px 16px;
}

/* ── Section Headers ────────────────────────────────────────────── */
.sectionTitle {
    color: #f0f6fc;
    font-size: 16px;
    font-weight: 700;
    padding-bottom: 4px;
}

.sectionSubtitle {
    color: #8b949e;
    font-size: 12px;
}

/* ── Labels ─────────────────────────────────────────────────────── */
.heading {
    color: #f0f6fc;
    font-size: 22px;
    font-weight: 700;
}

.subheading {
    color: #8b949e;
    font-size: 13px;
    line-height: 1.5;
}

.badge {
    border-radius: 10px;
    font-size: 11px;
    font-weight: 600;
    padding: 3px 10px;
}

.badgeHigh {
    background-color: #f8514922;
    color: #f85149;
}

.badgeMedium {
    background-color: #f0883e22;
    color: #f0883e;
}

.badgeLow {
    background-color: #3fb95022;
    color: #3fb950;
}

/* ── Screenshot Preview ─────────────────────────────────────────── */
#screenshotPreview {
    background-color: #0d1117;
    border: 2px dashed #21262d;
    border-radius: 12px;
    min-height: 200px;
}

#screenshotPreview[hasImage="true"] {
    border: 1px solid #30363d;
    border-style: solid;
}

/* ── Diagnosis Panels ───────────────────────────────────────────── */
#diagnosisPanel {
    background-color: #161b22;
    border: 1px solid #21262d;
    border-radius: 12px;
    padding: 16px;
}

#problemCard {
    background-color: #0d1117;
    border: 1px solid #21262d;
    border-radius: 10px;
    padding: 16px;
}

#evidenceBox {
    background-color: #0d1117;
    border: 1px solid #21262d;
    border-radius: 8px;
    color: #f0883e;
    font-family: "Cascadia Code", "Consolas", "Courier New", monospace;
    font-size: 12px;
    padding: 12px;
}

#commandBox {
    background-color: #0d1117;
    border: 1px solid #1f6feb44;
    border-radius: 8px;
    color: #58a6ff;
    font-family: "Cascadia Code", "Consolas", "Courier New", monospace;
    font-size: 12px;
    padding: 12px;
}

/* ── Scroll Areas ───────────────────────────────────────────────── */
QScrollArea {
    background-color: transparent;
    border: none;
}

QScrollArea > QWidget > QWidget {
    background-color: transparent;
}

QScrollBar:vertical {
    background-color: #0d1117;
    border: none;
    width: 8px;
    margin: 0;
}

QScrollBar::handle:vertical {
    background-color: #30363d;
    border-radius: 4px;
    min-height: 30px;
}

QScrollBar::handle:vertical:hover {
    background-color: #484f58;
}

QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {
    height: 0;
}

QScrollBar:horizontal {
    height: 0;
}

/* ── Progress indicator ─────────────────────────────────────────── */
QProgressBar {
    background-color: #21262d;
    border: none;
    border-radius: 4px;
    max-height: 4px;
    min-height: 4px;
    text-align: center;
}

QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #1f6feb, stop:0.5 #d2a8ff, stop:1 #1f6feb);
    border-radius: 4px;
}

/* ── Verification Panel ─────────────────────────────────────────── */
#verificationResolved {
    background-color: #3fb95015;
    border: 1px solid #3fb95044;
    border-radius: 10px;
    padding: 16px;
}

#verificationFailed {
    background-color: #f8514915;
    border: 1px solid #f8514944;
    border-radius: 10px;
    padding: 16px;
}

#verificationUncertain {
    background-color: #f0883e15;
    border: 1px solid #f0883e44;
    border-radius: 10px;
    padding: 16px;
}

/* ── Demo Banner ────────────────────────────────────────────────── */
#demoBanner {
    background-color: #d2a8ff15;
    border: 1px solid #d2a8ff44;
    border-radius: 8px;
    color: #d2a8ff;
    font-size: 12px;
    font-weight: 600;
    padding: 8px 16px;
}

/* ── Text Areas ─────────────────────────────────────────────────── */
QTextEdit, QPlainTextEdit {
    background-color: #0d1117;
    border: 1px solid #21262d;
    border-radius: 8px;
    color: #c9d1d9;
    font-family: "Cascadia Code", "Consolas", "Courier New", monospace;
    font-size: 12px;
    padding: 8px;
    selection-background-color: #1f6feb44;
}

/* ── Settings Fields ────────────────────────────────────────────── */
QLineEdit {
    background-color: #0d1117;
    border: 1px solid #21262d;
    border-radius: 8px;
    color: #c9d1d9;
    padding: 8px 12px;
    min-height: 20px;
}

QLineEdit:focus {
    border-color: #1f6feb;
}

QLabel#fieldLabel {
    color: #8b949e;
    font-size: 12px;
    font-weight: 600;
}

/* ── Tooltips ───────────────────────────────────────────────────── */
QToolTip {
    background-color: #1c2028;
    border: 1px solid #30363d;
    border-radius: 6px;
    color: #c9d1d9;
    font-size: 12px;
    padding: 6px 10px;
}

/* ── Message Box ────────────────────────────────────────────────── */
QMessageBox {
    background-color: #161b22;
}

QMessageBox QLabel {
    color: #c9d1d9;
}
"""
