"""
SightFix AI — Action Service

Executes user-approved commands with strict safety controls.
Only allowlisted, non-destructive commands are permitted.
"""

import subprocess
import logging
import shlex

from config import Config

logger = logging.getLogger(__name__)


class ActionResult:
    """Outcome of an executed action."""

    def __init__(self, success: bool, output: str, command: str, blocked: bool = False):
        self.success = success
        self.output = output
        self.command = command
        self.blocked = blocked


class ActionService:
    """Validates and executes approved troubleshooting commands."""

    @staticmethod
    def is_safe(command: str) -> tuple[bool, str]:
        """
        Check a command against the blocklist and allowlist.

        Returns (is_safe, reason).
        """
        cmd_lower = command.lower().strip()

        # ── Block dangerous patterns first ────────────────────────────
        for pattern in Config.BLOCKED_PATTERNS:
            if pattern.lower() in cmd_lower:
                return False, f"Blocked: command contains dangerous pattern '{pattern}'"

        # ── Check allowlist ───────────────────────────────────────────
        allowed = False
        for prefix in Config.SAFE_COMMANDS_ALLOWLIST:
            if cmd_lower.startswith(prefix.lower()):
                allowed = True
                break

        if not allowed:
            return False, (
                "This command is not in the safe allowlist.\n"
                "For security, only pre-approved diagnostic and install commands "
                "can be executed automatically.\n"
                "Please run this command manually in your terminal."
            )

        return True, "Command is safe to execute."

    @staticmethod
    def execute(command: str) -> ActionResult:
        """
        Execute a pre-validated command.

        IMPORTANT: Call is_safe() first. This method trusts the caller
        to have obtained explicit user approval.
        """
        safe, reason = ActionService.is_safe(command)
        if not safe:
            logger.warning("Blocked command execution: %s — %s", command, reason)
            return ActionResult(
                success=False,
                output=reason,
                command=command,
                blocked=True,
            )

        logger.info("Executing approved command: %s", command)

        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=60,
                cwd=None,  # Use current directory
            )

            output = result.stdout
            if result.stderr:
                output += "\n" + result.stderr

            return ActionResult(
                success=result.returncode == 0,
                output=output.strip() if output.strip() else "(No output)",
                command=command,
            )

        except subprocess.TimeoutExpired:
            return ActionResult(
                success=False,
                output="Command timed out after 60 seconds.",
                command=command,
            )
        except Exception as exc:
            logger.exception("Command execution failed")
            return ActionResult(
                success=False,
                output=f"Execution error: {exc}",
                command=command,
            )

    @staticmethod
    def get_manual_instructions(command: str) -> str:
        """
        Return formatted instructions for manually running a command
        that cannot be safely automated.
        """
        return (
            f"⚠️  This command cannot be executed automatically for safety reasons.\n\n"
            f"Please run the following command manually in your terminal:\n\n"
            f"    {command}\n\n"
            f"After running it, click 'Verify Fix' to check the result."
        )
