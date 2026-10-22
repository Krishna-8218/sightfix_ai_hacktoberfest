# 🔍 SightFix AI — Desktop Troubleshooter & Automated Code Repair

**SightFix AI** is an open-source AI desktop application that diagnoses technical problems and automatically repairs source code syntax errors.

## ✨ Features
| Feature | Description |
|---|---|
| 📂 **Inspect Current File** | Select a source file to read from disk and diagnose with `python -m py_compile` |
| 🛠️ **Real Code Repair** | Generates concrete, validated source-code replacement patches with unified diffs |
| 🔒 **Safe Patch Application** | Explicit approval required; creates automatic `.bak` backups with instant **Undo Fix** |
| 🛡️ **Stale Diagnosis Prevention** | Every scan runs with fresh state; tokenized scan IDs prevent race conditions or stale overwrites |

## 🏗️ Architecture
```
sightfix_ai/
├── main.py                          # Application entry point
├── config.py                        # Configuration
├── ui/                              # PySide6 desktop GUI
├── services/                        # Code, Vision, Action services
└── tests/                           # Test suites
```

## 🔄 Two Troubleshooting Workflows
1. **Source Code Inspection & Repair Workflow**
2. **Desktop Screenshot Diagnosis Workflow**
