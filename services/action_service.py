import subprocess
import logging
from config import Config

logger = logging.getLogger(__name__)

class ActionResult:
    def __init__(self, success: bool, output: str, command: str, blocked: bool = False):
        self.success = success
        self.output = output
        self.command = command
        self.blocked = blocked

class ActionService:
    @staticmethod
    def is_safe(command: str) -> tuple[bool, str]:
        cmd_lower = command.lower().strip()
        for pattern in Config.BLOCKED_PATTERNS:
            if pattern.lower() in cmd_lower:
                return False, f"Blocked: command contains dangerous pattern '{pattern}'"
        allowed = any(cmd_lower.startswith(prefix.lower()) for prefix in Config.SAFE_COMMANDS_ALLOWLIST)
        if not allowed:
            return False, "This command is not in the safe allowlist."
        return True, "Command is safe to execute."
