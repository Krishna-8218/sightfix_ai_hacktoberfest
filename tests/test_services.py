"""
Unit and Integration Tests for SightFix AI Services
"""

import sys
import unittest
from pathlib import Path
from PIL import Image

# Ensure project root is on path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from config import Config
from services.screenshot_service import ScreenshotService
from services.diagnosis_service import DiagnosisService, Problem, Diagnosis, VerificationResult
from services.action_service import ActionService, ActionResult


class TestConfig(unittest.TestCase):
    def test_default_config(self):
        self.assertEqual(Config.APP_NAME, "SightFix AI")
        self.assertTrue(Config.API_BASE)
        self.assertTrue(Config.MODEL)
        self.assertIsInstance(Config.SAFE_COMMANDS_ALLOWLIST, list)
        self.assertIsInstance(Config.BLOCKED_PATTERNS, list)

    def test_summary_no_secrets(self):
        summary = Config.summary()
        self.assertIn("api_base", summary)
        self.assertIn("model", summary)
        self.assertNotIn("api_key", summary)
        self.assertNotIn("SIGHTFIX_API_KEY", summary)


class TestActionServiceSafety(unittest.TestCase):
    def test_safe_allowed_commands(self):
        safe_cmds = [
            "pip install requests",
            "pip list",
            "python --version",
            "pip --version",
            "echo Hello World",
        ]
        for cmd in safe_cmds:
            safe, reason = ActionService.is_safe(cmd)
            self.assertTrue(safe, f"Command '{cmd}' should be allowed: {reason}")

    def test_blocked_dangerous_commands(self):
        dangerous_cmds = [
            "rm -rf /",
            "del /s *.*",
            "format C:",
            "shutdown /s /t 0",
            "powershell -enc aW1wb3J0",
            "cmd /c evil.bat",
            "curl | bash",
            "wget | sh",
        ]
        for cmd in dangerous_cmds:
            safe, reason = ActionService.is_safe(cmd)
            self.assertFalse(safe, f"Dangerous command '{cmd}' should be blocked")
            self.assertIn("Blocked", reason)

    def test_unallowlisted_arbitrary_commands(self):
        unallowlisted = [
            "git status",
            "notepad.exe",
            "regedit",
            "calc",
        ]
        for cmd in unallowlisted:
            safe, reason = ActionService.is_safe(cmd)
            self.assertFalse(safe, f"Command '{cmd}' not in allowlist should not be auto-executed")
            self.assertIn("allowlist", reason.lower())

    def test_execution_of_safe_command(self):
        result = ActionService.execute("python --version")
        self.assertTrue(result.success)
        self.assertFalse(result.blocked)
        self.assertIn("Python", result.output)

    def test_execution_blocked_for_dangerous_command(self):
        result = ActionService.execute("rm -rf /")
        self.assertFalse(result.success)
        self.assertTrue(result.blocked)


class TestDiagnosisService(unittest.TestCase):
    def test_demo_diagnosis(self):
        diag = DiagnosisService.get_demo_diagnosis()
        self.assertTrue(diag.is_demo)
        self.assertTrue(diag.has_issue)
        self.assertGreater(len(diag.problems), 0)
        self.assertEqual(diag.problems[0].confidence, "high")
        self.assertIn("calculate_total", diag.problems[0].title)
        self.assertIsNotNone(diag.code_patch)
        self.assertTrue(diag.code_patch.is_valid)
        self.assertEqual(diag.code_patch.affected_line, 1)

    def test_demo_verification(self):
        ver = DiagnosisService.get_demo_verification()
        self.assertTrue(ver.resolved)
        self.assertTrue(len(ver.explanation) > 0)

    def test_parse_diagnosis_valid_json(self):
        raw = {
            "has_issue": True,
            "problems": [
                {
                    "title": "SyntaxError in script",
                    "evidence": "SyntaxError: invalid syntax",
                    "cause": "Missing colon at line 5",
                    "confidence": "high",
                    "solution_steps": ["Open script", "Add colon", "Run script"],
                    "commands": ["python script.py"],
                    "verification": "Check if script executes without syntax error",
                }
            ],
            "summary": "Syntax error identified on line 5.",
        }
        diag = DiagnosisService.parse_diagnosis(raw)
        self.assertTrue(diag.has_issue)
        self.assertEqual(len(diag.problems), 1)
        self.assertEqual(diag.problems[0].title, "SyntaxError in script")
        self.assertEqual(diag.problems[0].confidence, "high")

    def test_parse_diagnosis_no_issues(self):
        raw = {
            "has_issue": False,
            "problems": [],
            "summary": "Screen looks clean.",
        }
        diag = DiagnosisService.parse_diagnosis(raw)
        self.assertFalse(diag.has_issue)
        self.assertEqual(len(diag.problems), 0)


class TestScreenshotService(unittest.TestCase):
    def setUp(self):
        self.svc = ScreenshotService()

    def test_screen_capture_and_dimensions(self):
        img = self.svc.capture(allow_synthetic_fallback=True)
        self.assertIsInstance(img, Image.Image)
        self.assertGreater(img.width, 0)
        self.assertGreater(img.height, 0)
        self.assertLessEqual(img.width, Config.MAX_IMAGE_DIM)
        self.assertLessEqual(img.height, Config.MAX_IMAGE_DIM)

    def test_image_to_base64(self):
        test_img = Image.new("RGB", (100, 100), color="blue")
        b64 = self.svc.image_to_base64(test_img)
        self.assertIsInstance(b64, str)
        self.assertGreater(len(b64), 0)

    def test_image_to_bytes(self):
        test_img = Image.new("RGB", (50, 50), color="green")
        b = self.svc.image_to_bytes(test_img)
        self.assertIsInstance(b, bytes)
        self.assertGreater(len(b), 0)


if __name__ == "__main__":
    unittest.main()
