# SightFix AI 🛠️

### An AI-powered Windows troubleshooting assistant

SightFix AI is an open-source desktop application designed to help users diagnose and resolve common Windows and software development problems using AI-powered analysis and system diagnostics.

Instead of simply suggesting solutions, SightFix aims to bridge the gap between identifying a problem and verifying a fix. It combines screenshot understanding, diagnostic tools, and source-code inspection to investigate errors, propose solutions, and help users apply repairs with their approval.

> **Our goal:** Observe the problem, identify its cause, propose a repair, and verify the result.

## 🚀 Key Features

- **Screenshot-Based Diagnosis:** Analyze screenshots of Windows errors, terminal output, and application problems using a vision-language model.
- **Code Error Detection:** Inspect source files to identify issues such as Python syntax errors, missing dependencies, and configuration problems.
- **Network Troubleshooting:** Diagnose common connectivity issues using network commands and system diagnostic information.
- **System Diagnostics:** Investigate common performance, storage, and application issues using relevant diagnostic tools.
- **AI-Generated Fixes:** Generate targeted repair suggestions and proposed code changes based on available evidence.
- **Human-in-the-Loop Repairs:** Allow users to review and approve proposed changes before they are applied.
- **Fix Verification:** Re-run relevant checks to determine whether a proposed repair resolved the issue.

*Feature availability depends on the implementation status of each module. See the roadmap for planned improvements.*

## 💡 Problems SightFix AI Aims to Solve

| Category | Example problems |
|---|---|
| Software Development | Syntax errors, missing Python packages, compilation failures |
| Network Connectivity | Wi-Fi connection failures, DNS issues, no internet access |
| System Performance | High CPU or RAM usage, unresponsive applications |
| Storage and Files | Low disk space, missing files, permission errors |
| Application Issues | Startup crashes, dependency errors, installation failures |
| Devices and Peripherals | Bluetooth connectivity, audio, webcam and USB issues |
| Windows Configuration | Environment variables, service errors, update problems |

SightFix focuses on gathering diagnostic evidence before recommending a solution. Not every issue can be repaired automatically, and some problems may require manual intervention.

## ⚙️ How It Works

SightFix follows a diagnostic workflow:

1. **Observe:** Capture a screenshot or select a relevant source file.
2. **Diagnose:** Use AI to interpret the visible error and identify possible causes.
3. **Investigate:** Inspect source code, logs, or system diagnostic output to validate the diagnosis.
4. **Propose:** Generate a targeted repair and explain why it may work.
5. **Approve:** Let the user review the proposed change before applying it.
6. **Verify:** Run relevant checks again and report the actual result.

```text
User Reports a Problem
          ↓
Screenshot / File / Diagnostics
          ↓
AI Analysis + Evidence Collection
          ↓
Identify Likely Root Cause
          ↓
Generate Proposed Repair
          ↓
User Reviews and Approves
          ↓
Apply Repair
          ↓
Run Verification Checks
          ↓
Report the Result
```

## 🧰 Tech Stack

| Technology | Purpose |
|---|---|
| Python | Core application logic and diagnostic workflows |
| PySide6 | Desktop graphical user interface |
| Qwen2.5-VL 3B | Local vision-language model for screenshot understanding |
| Ollama | Runs the AI model locally |
| MSS | Screenshot capture |
| Pillow | Image processing |
| `pathlib` and file I/O | Source-file inspection |
| `subprocess` | Running controlled diagnostic commands and verification checks |
| Git and GitHub | Version control and open-source collaboration |

### Why a local AI model?

SightFix uses Qwen2.5-VL through Ollama to support local inference without requiring a hosted AI API key for model inference. Actual privacy depends on the application's other integrations and network behavior.

## 🖥️ Getting Started

### Prerequisites

- Windows 10 or Windows 11
- Python 3.10 or later
- Git
- Ollama
- Sufficient RAM and storage for the selected AI model

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/SightFix-AI.git
cd SightFix-AI
```

Replace `YOUR_USERNAME` with your GitHub username and adjust the repository name if necessary.

### 2. Create a virtual environment

```bash
python -m venv .venv
```

Activate it on Windows:

```powershell
.venv\Scripts\Activate.ps1
```

If you use Command Prompt instead:

```bat
.venv\Scripts\activate.bat
```

### 3. Install dependencies

If the repository contains a `requirements.txt` file:

```bash
pip install -r requirements.txt
```

Otherwise, install the dependencies listed in the project's setup instructions. A typical initial dependency set may include:

```bash
pip install PySide6 mss Pillow openai
```

### 4. Install and start Ollama

Install Ollama from [ollama.com](https://ollama.com/), then download the model:

```bash
ollama pull qwen2.5vl:3b
```

Confirm that the model is available:

```bash
ollama list
```

### 5. Configure the application

Configure the model name and Ollama endpoint in the application's settings or configuration file, according to the current implementation.

Typical values are:

```text
Model: qwen2.5vl:3b
Endpoint: http://localhost:11434/v1
```

Ensure Ollama is running before launching the application.

### 6. Launch SightFix AI

Run the application's actual entry-point file. For example, if it is named `main.py`:

```bash
python main.py
```

If your entry-point file has a different name, use that filename instead.

## 🔒 Security and Privacy

SightFix is designed around user-controlled troubleshooting.

- **User approval:** Proposed repairs should be reviewed before application.
- **Restricted access:** File inspection should remain within the selected project directory.
- **Command validation:** Diagnostic commands should use a controlled allowlist rather than unrestricted AI-generated shell commands.
- **Sensitive files:** Exclude credentials, API keys, `.env` files, and other sensitive data from inspection.
- **Backups and recovery:** Preserve original files before applying code changes.
- **Verification:** Report success only when the relevant check actually passes.

Local model inference does not, by itself, guarantee that all application data stays local. Users should review any external integrations and data handling before using the application with sensitive information.

## 🗺️ Roadmap

- [x] Desktop application foundation
- [x] Local Qwen2.5-VL model setup through Ollama
- [x] Initial screenshot-based error analysis
- [ ] Reliable source-file selection and inspection
- [ ] Structured patch generation and diff preview
- [ ] Safe patch application, backup, and undo
- [ ] Automated syntax and runtime verification
- [ ] Wi-Fi and network diagnostic module
- [ ] CPU, memory, and storage diagnostics
- [ ] Expanded Windows application and device troubleshooting
- [ ] Comprehensive automated tests and documentation

The roadmap reflects intended development work; completed items should be updated to match the current code and verified behavior.

## 🤝 Contributing

Contributions are welcome!

1. Fork this repository.
2. Create a feature branch.
3. Implement your change and add relevant tests.
4. Run the available tests and verify the feature.
5. Submit a pull request describing the change and its results.

Potential contribution areas include new diagnostic modules, improved error analysis, safer repair workflows, UI improvements, documentation, and automated tests.

## 📌 Current Limitations

- AI-generated diagnoses and repairs may be incorrect.
- Screenshot analysis alone may not reveal the underlying cause.
- Some problems require logs, source files, system access, or administrator privileges.
- Network, driver, and hardware issues may not be fixable by software.
- Automatic repair capabilities depend on the diagnostic and verification modules implemented.

Always review proposed changes before applying them.

## 📄 License

This project is intended to be open source. Add a `LICENSE` file to the repository and select a license, such as the MIT License, before publishing it for reuse and contributions.

## 👨‍💻 Project

**SightFix AI — From error detection to verified repair.**

Built with Python, local AI, and a focus on making technical troubleshooting easier for everyone.
