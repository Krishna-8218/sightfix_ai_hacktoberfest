# SightFix AI 🛠️

SightFix AI is a Python-based desktop application built with PySide6 that uses AI to diagnose and troubleshoot Windows and software development problems.

It combines screenshot analysis using a vision-language model with system diagnostics and source-code inspection to identify potential causes, suggest targeted fixes, and help users verify whether a problem has been resolved.

Unlike a traditional chatbot that only provides instructions, SightFix AI aims to assist users throughout the troubleshooting process—from understanding an error to applying and verifying a repair.


## Features

- **Screenshot Analysis:** Understand Windows errors, terminal output, and application issues using a vision-language model.
- **Code Debugging:** Investigate syntax errors, missing dependencies, and configuration problems.
- **Network Troubleshooting:** Diagnose Wi-Fi connectivity, DNS, and internet access issues.
- **System Diagnostics:** Investigate performance issues, high CPU/RAM usage, and storage problems.
- **AI-Powered Repair Suggestions:** Generate targeted fixes based on diagnostic evidence.
- **User-Controlled Repairs:** Review proposed changes before applying them.
- **Verification:** Re-run relevant checks to determine whether a fix worked.

*Features depend on the diagnostic and repair modules implemented in the current version.*

## How It Works

1. **Observe:** Capture a screenshot or select a relevant file.
2. **Diagnose:** Analyze the problem using AI and diagnostic information.
3. **Investigate:** Inspect source code, logs, or system status to identify the likely cause.
4. **Propose:** Generate a targeted solution for the user to review.
5. **Repair:** Apply the approved change.
6. **Verify:** Run relevant checks and report the result.

## Tech Stack

- **Language:** Python
- **GUI:** PySide6
- **AI Model:** Qwen2.5-VL 3B
- **Model Runtime:** Ollama
- **Screenshot Capture:** MSS
- **Image Processing:** Pillow
- **System Diagnostics:** Python subprocess and file-system utilities

## Installation

### Prerequisites

- Windows 10 or Windows 11
- Python 3.10+
- Git
- [Ollama](https://ollama.com/)

### 1. Clone the repository

```bash
git clone https://github.com/Krishna-8218/SightFix-AI.git
cd SightFix-AI
```

### 2. Create and activate a virtual environment

```bash
python -m venv .venv
.venv\Scripts\activate
```

### 3. Install dependencies

If `requirements.txt` is available:

```bash
pip install -r requirements.txt
```

### 4. Set up the AI model

```bash
ollama pull qwen2.5vl:3b
```

Ensure Ollama is running and the application is configured to use:

- **Model:** `qwen2.5vl:3b`
- **Endpoint:** `http://localhost:11434/v1`

### 5. Run the application

Run the project's Python entry-point file, for example:

```bash
python main.py
```

Replace `main.py` with the actual entry-point filename if different.

## Security

- Review proposed repairs before applying them.
- Restrict file access to the selected project directory.
- Validate diagnostic commands before execution.
- Protect sensitive files, credentials, and environment variables.
- Back up files before modifying them.
- Report a repair as successful only after verification.

## Limitations

AI-generated diagnoses and fixes may be incorrect. Some problems require additional logs, administrator privileges, hardware repairs, or intervention from an internet service provider. Local AI inference does not automatically guarantee that all application data remains local.

## License

See the repository's `LICENSE` file for licensing terms.

---

**SightFix AI — From error detection to verified repair.**

Developed by [Krishna Ransing](https://github.com/Krishna-8218).
