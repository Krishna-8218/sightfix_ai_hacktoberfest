# Contributing to SightFix AI

Thank you for your interest in contributing to **SightFix AI**! This project was built for the Open Source AI Hackathon.

## 🌟 Hacktoberfest Guidelines

We welcome contributions from developers of all skill levels! Here is how you can help:

### Areas of Contribution
1. **New Diagnostic Rules**: Expand compiler checks and heuristics in `services/code_service.py`.
2. **Support for Additional Languages**: Help add compiler/linter support for Rust (`cargo check`), Go (`go build`), TypeScript (`tsc`), or C++.
3. **UI/UX Polish**: Improve themes, animations, or keyboard shortcuts in `ui/main_window.py` and `ui/styles.py`.
4. **Model Integrations**: Test and document compatibility with other open-weight vision models (e.g. MiniCPM-V, LLaVA, DeepSeek-VL).
5. **Documentation & Tutorials**: Improve setup guides, troubleshooting steps, and video demonstrations.

### Development Setup
1. Clone the repository:
   ```bash
   git clone https://github.com/Krishna-8218/sightfix_ai_hacktoberfest.git
   cd sightfix_ai_hacktoberfest
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the test suite:
   ```bash
   python -m unittest discover -s tests -p "test_*.py"
   ```

### Code Style & Safety Guidelines
- Every automated code patch must be validated before applying.
- Preserve explicit user approval gates before executing shell commands or modifying files.
- Ensure all new features have accompanying unit tests in `tests/`.
