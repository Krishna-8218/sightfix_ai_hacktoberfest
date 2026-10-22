import sys
import unittest
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from config import Config
from services.action_service import ActionService

class TestConfig(unittest.TestCase):
    def test_default_config(self):
        self.assertEqual(Config.APP_NAME, "SightFix AI")
        self.assertTrue(Config.API_BASE)

class TestActionServiceSafety(unittest.TestCase):
    def test_safe_allowed_commands(self):
        safe, reason = ActionService.is_safe("pip install requests")
        self.assertTrue(safe)
    def test_blocked_dangerous_commands(self):
        safe, reason = ActionService.is_safe("rm -rf /")
        self.assertFalse(safe)

if __name__ == "__main__":
    unittest.main()
