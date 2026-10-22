# 🔍 SightFix AI — Desktop Troubleshooter & Automated Code Repair

**SightFix AI** is an open-source AI desktop application that diagnoses technical problems and automatically repairs source code. It combines **desktop visual troubleshooting** with **direct source-code compiler analysis (`py_compile`)**, generating concrete, validated diff patches, safely applying them with automatic backups, and verifying results.

> **Built for the Open Source AI Hackathon**

![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-blue)
![License: MIT](https://img.shields.io/badge/License-MIT-green)
![PySide6](https://img.shields.io/badge/GUI-PySide6-orange)
![Qwen2.5-VL](https://img.shields.io/badge/Model-Qwen2.5--VL-purple)

---

## ✨ Features

| Feature | Description |
|---|---|
| 📂 **Inspect Current File** | Select a source file to read from disk and diagnose with `python -m py_compile` |
| 🛠️ **Real Code Repair** | Generates concrete, validated source-code replacement patches with unified diffs |
| 🔒 **Safe Patch Application** | Explicit approval required; creates automatic `.bak` backups with instant **Undo Fix** |
| 🛡️ **Stale Diagnosis Prevention** | Every scan runs with fresh state; tokenized scan IDs prevent race conditions or stale overwrites |
| 🖥️ **Screen Capture & Vision** | One-click desktop screenshot diagnosis for UI, terminal, or system errors |
| ✅ **Compiler & Runtime Verification** | Re-runs `py_compile` to confirm syntax resolution, with optional script execution |
| 🎮 **Demo Mode** | Built-in simulation of `calculate_total.py` syntax repair without an API key |
| ⚙️ **Configurable AI Engine** | Pre-configured for local Ollama (`qwen2.5vl:3b` / `qwen2.5-vl:7b`) and OpenAI-compatible endpoints |

---

## 🏗️ Architecture

```
sightfix_ai/
├── main.py                          # Application entry point with foreground window activation
├── config.py                        # Configuration (env vars, safety rules, sensitive file filters)
├── run.bat                          # Desktop double-click launcher
├── ui/
│   ├── __init__.py
│   ├── main_window.py               # PySide6 GUI (dashboard, code fix panel, diff viewer, workers)
│   └── styles.py                    # Dark-theme Qt developer stylesheet
├── services/
│   ├── __init__.py
│   ├── code_service.py              # File inspection, py_compile, patch validation, diffs, backup/undo
│   ├── screenshot_service.py        # mss screen capture with ImageGrab/headless fallback
│   ├── ai_service.py                # Vision diagnosis & structured code repair prompt integration
│   ├── diagnosis_service.py         # Typed dataclasses (Diagnosis, CodePatch, Problem, Verification)
│   ├── action_service.py            # Safe shell command allowlist & execution
│   └── verification_service.py      # Screenshot-based verification orchestrator
├── tests/
│   ├── __init__.py
│   ├── test_repair_workflow.py      # End-to-end tests for scenarios A through F
│   ├── test_services.py             # 14 unit tests for services and safety controls
│   └── test_gui.py                  # Headless offscreen Qt GUI integration tests
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

---

## 🔄 Two Troubleshooting Workflows

### 1. Source Code Inspection & Repair Workflow

```
[Select Source File] ──▶ [Read from Disk & py_compile]
                                    │
                                    ▼
                          [Compiler Error Detected]
                                    │
                                    ▼
                         [AI Proposes Minimal Patch]
                                    │
                                    ▼
                         [Local Patch Validation]
                       (Unique match, hash check)
                                    │
                                    ▼
                      [Review Diff in UI & Approve]
                                    │
                                    ▼
                    [Apply Patch + Create .bak Backup]
                                    │
                                    ▼
                     [Verify with py_compile (Exit 0)]
                                    │
                                    ▼
                   [Optional: Execute Script (Runtime Test)]
```

### 2. Desktop Screenshot Diagnosis Workflow

```
[Diagnose My Screen] ──▶ [Capture Screenshot] ──▶ [Analyze with Vision AI]
                                                           │
                                                           ▼
                                                [Diagnose Visible Error]
                                                           │
                                                           ▼
                                                [Propose Solution & Verify]
```

---

## 🔒 Safety & Permissions

- **Explicit User Confirmation**: No source file is ever edited and no command is executed without explicit user button clicks (`Apply Fix` or `Approve & Execute`).
- **Automatic Backups**: Before any source code modification, an exact copy is written to `<filename>.bak`. Clicking **Undo Fix** restores the original file immediately.
- **Atomic Modification & Hash Verification**: The patch engine computes the SHA-256 hash of the file when diagnosed and verifies it before applying. If the file was modified on disk in the background, the stale patch is discarded.
- **Sensitive File Exclusion**: Inspection and editing are blocked for files matching sensitive patterns (`.env`, `.git`, SSH keys, certificates, credentials).
- **Separation of Concerns**: Code editing is handled through the dedicated patch engine; shell execution remains strictly governed by the command allowlist (`pip install`, `python --version`, etc.). Rerunning a script is never treated as a code repair.

---

## 🚀 Quick Start

### 1. Prerequisites
- **Python 3.11 or later**
- (Optional) [Ollama](https://ollama.com) running locally with `qwen2.5vl:3b` or `qwen2.5-vl:7b`

### 2. Install Dependencies

```bash
cd sightfix_ai
pip install -r requirements.txt
```

### 3. Launch the Application

Double-click `run.bat` or run:

```bash
python main.py
```

### 4. Running the Complete Test Suite

All 20 tests (including Scenarios A through F) can be run via:

```bash
# Run the complete test suite
python -m unittest discover -s tests -p "test_*.py"

# Run specifically the Code Repair end-to-end tests (Tests A-F)
python tests/test_repair_workflow.py

# Run the GUI component test
python tests/test_gui.py
```

---

## 🧪 Verified Test Scenarios (Tests A – F)

| Scenario | Description | Status |
|---|---|---|
| **Test A** | **Current-file syntax repair**: `calculate_total.py` missing colon detected on line 1, patch generated and applied, `py_compile` passes with exit code 0. | ✅ PASSED |
| **Test B** | **Previous-error isolation**: `student_management.py` (error line 15) scanned first, then `calculate_total.py` scanned. Confirmed second scan contains zero previous error artifacts. | ✅ PASSED |
| **Test C** | **Repeated scans & race conditions**: Scan ID token invalidation prevents older async worker responses from overwriting newer scans. | ✅ PASSED |
| **Test D** | **Rejected patch**: When user clicks `Reject`, file remains bit-for-bit identical on disk. | ✅ PASSED |
| **Test E** | **Failed verification**: If a patch does not resolve the syntax error, `py_compile` failure is accurately reported, never claiming false success. | ✅ PASSED |
| **Test F** | **Successful runtime**: After applying fix, running `calculate_total.py` prints `Total: 30` with return code 0. | ✅ PASSED |

---

## 🤖 Model Configuration

SightFix AI connects to any OpenAI-compatible API endpoint:

```env
# Local Ollama (Default)
SIGHTFIX_API_BASE=http://localhost:11434/v1
SIGHTFIX_API_KEY=ollama
SIGHTFIX_MODEL=qwen2.5vl:3b

# Hosted Provider Example (OpenRouter)
# SIGHTFIX_API_BASE=https://openrouter.ai/api/v1
# SIGHTFIX_API_KEY=sk-or-v1-...
# SIGHTFIX_MODEL=qwen/qwen2.5-vl-7b-instruct
```

You can also adjust and test connection settings live in the **⚙️ Settings** tab.

---

## 📄 License

MIT License — see [LICENSE](LICENSE).

Third-party libraries:
- `PySide6-Essentials` (LGPL v3)
- `mss` (MIT)
- `Pillow` (HPND)
- `openai` Python SDK (Apache 2.0)
- `python-dotenv` (BSD-3-Clause)
- Model: `Qwen2.5-VL` by Alibaba Cloud (Apache 2.0)
