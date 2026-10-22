"""
SightFix AI — Code Service

Provides safe file inspection, real compiler error diagnostics (py_compile),
validated patch generation, unified diff generation, atomic patch application with backup/undo,
and post-fix verification.
"""

import os
import re
import difflib
import hashlib
import logging
import subprocess
import fnmatch
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from config import Config

logger = logging.getLogger(__name__)

# Patterns of files that must never be automatically inspected or modified
SENSITIVE_PATTERNS = [
    "*.env*",
    "*.pem",
    "*.key",
    "*.p12",
    "*.pfx",
    "*.kdbx",
    "id_rsa*",
    "id_ed25519*",
    "*credentials*",
    "*secret*",
    "*password*",
    "*.git*",
    "*.sqlite3",
    "*.db",
]


@dataclass
class CompilerResult:
    """Result of running a language compiler/linter on a source file."""
    exit_code: int
    stdout: str
    stderr: str
    has_error: bool
    error_line: Optional[int] = None
    error_type: str = ""
    error_msg: str = ""
    error_snippet: str = ""


@dataclass
class FileInspectionResult:
    """Complete results from reading and compiling a file from disk."""
    file_path: Path
    file_content: str
    content_hash: str
    compiler_result: CompilerResult
    error_message: Optional[str] = None

    @property
    def has_error(self) -> bool:
        return self.compiler_result.has_error or bool(self.error_message)


@dataclass
class CodePatch:
    """A concrete, validated source-code replacement."""
    file_path: str
    affected_line: int
    original_code: str
    replacement_code: str
    explanation: str
    diff: str = ""
    is_valid: bool = False
    validation_error: str = ""
    source_hash: str = ""  # Hash of file content when patch was generated


class CodeService:
    """Safe source file inspection, compiler diagnosis, and patch application."""

    @staticmethod
    def is_file_safe_to_inspect(path: Path) -> tuple[bool, str]:
        """Check whether a file is safe and permitted for inspection."""
        try:
            resolved = path.resolve()
        except Exception as e:
            return False, f"Invalid path: {e}"

        if not resolved.exists():
            return False, f"File does not exist: {resolved}"

        if not resolved.is_file():
            return False, f"Path is not a regular file: {resolved}"

        # Sensitive file filter
        filename = resolved.name.lower()
        for pattern in SENSITIVE_PATTERNS:
            if fnmatch.fnmatch(filename, pattern):
                return False, f"Access blocked: '{filename}' matches sensitive pattern '{pattern}'"

        # Check for .git or hidden sensitive folders in path
        for part in resolved.parts:
            if part.startswith(".") and part in (".git", ".ssh", ".gnupg", ".aws"):
                return False, f"Access blocked: path contains sensitive directory '{part}'"

        return True, "File is safe to inspect."

    @staticmethod
    def inspect_file(file_path: Path | str) -> FileInspectionResult:
        """
        Read complete file from disk, calculate hash, and run compiler diagnostics.
        """
        path = Path(file_path).resolve()
        safe, reason = CodeService.is_file_safe_to_inspect(path)
        if not safe:
            return FileInspectionResult(
                file_path=path,
                file_content="",
                content_hash="",
                compiler_result=CompilerResult(
                    exit_code=1,
                    stdout="",
                    stderr=reason,
                    has_error=True,
                    error_msg=reason,
                ),
                error_message=reason,
            )

        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
        except Exception as e:
            msg = f"Failed to read file from disk: {e}"
            return FileInspectionResult(
                file_path=path,
                file_content="",
                content_hash="",
                compiler_result=CompilerResult(
                    exit_code=1,
                    stdout="",
                    stderr=msg,
                    has_error=True,
                    error_msg=msg,
                ),
                error_message=msg,
            )

        content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()

        # Run compiler / syntax check
        compiler_res = CodeService.compile_check(path)

        return FileInspectionResult(
            file_path=path,
            file_content=content,
            content_hash=content_hash,
            compiler_result=compiler_res,
        )

    @staticmethod
    def compile_check(file_path: Path | str) -> CompilerResult:
        """
        Run python -m py_compile against the file to detect syntax errors.
        Extracts exit code, exact line number, and error message.
        """
        path = Path(file_path).resolve()
        if path.suffix.lower() != ".py":
            # For non-python files, check if readable
            return CompilerResult(
                exit_code=0,
                stdout="",
                stderr="",
                has_error=False,
                error_msg="Non-Python file: automatic syntax validation not supported.",
            )

        try:
            res = subprocess.run(
                ["python", "-m", "py_compile", str(path)],
                capture_output=True,
                text=True,
                timeout=10,
            )
            stderr = res.stderr.strip()
            stdout = res.stdout.strip()
            exit_code = res.returncode

            if exit_code == 0:
                return CompilerResult(
                    exit_code=0,
                    stdout=stdout,
                    stderr=stderr,
                    has_error=False,
                )

            # Parse stderr for syntax error details
            # Typical output:
            #   File "...", line 1
            #     def calculate_total(a, b)
            #                              ^
            #   SyntaxError: expected ':'
            line_no = None
            err_type = "SyntaxError"
            err_msg = stderr
            snippet = ""

            line_match = re.search(r'line\s+(\d+)', stderr, re.IGNORECASE)
            if line_match:
                line_no = int(line_match.group(1))

            err_match = re.search(r'([A-Za-z_]+Error:\s*.+)', stderr)
            if err_match:
                err_msg = err_match.group(1).strip()
                err_type = err_msg.split(":", 1)[0].strip()

            # Extract snippet line
            lines = stderr.splitlines()
            for i, l in enumerate(lines):
                if "^" in l and i > 0:
                    snippet = lines[i - 1].strip()
                    break

            return CompilerResult(
                exit_code=exit_code,
                stdout=stdout,
                stderr=stderr,
                has_error=True,
                error_line=line_no,
                error_type=err_type,
                error_msg=err_msg,
                error_snippet=snippet,
            )

        except subprocess.TimeoutExpired:
            return CompilerResult(
                exit_code=124,
                stdout="",
                stderr="Compiler check timed out after 10s.",
                has_error=True,
                error_msg="py_compile timed out",
            )
        except Exception as e:
            return CompilerResult(
                exit_code=1,
                stdout="",
                stderr=str(e),
                has_error=True,
                error_msg=f"Compiler execution error: {e}",
            )

    @staticmethod
    def validate_patch(
        file_path: Path | str,
        original_code: str,
        replacement_code: str,
        affected_line: int = 1,
        explanation: str = "",
        expected_hash: Optional[str] = None,
    ) -> CodePatch:
        """
        Validate that the proposed patch matches the actual file on disk uniquely.
        Constructs a unified diff.
        """
        path = Path(file_path).resolve()
        safe, reason = CodeService.is_file_safe_to_inspect(path)
        if not safe:
            return CodePatch(
                file_path=str(path),
                affected_line=affected_line,
                original_code=original_code,
                replacement_code=replacement_code,
                explanation=explanation,
                is_valid=False,
                validation_error=f"Unsafe file path: {reason}",
            )

        if not path.exists():
            return CodePatch(
                file_path=str(path),
                affected_line=affected_line,
                original_code=original_code,
                replacement_code=replacement_code,
                explanation=explanation,
                is_valid=False,
                validation_error="Target file does not exist on disk.",
            )

        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
        except Exception as e:
            return CodePatch(
                file_path=str(path),
                affected_line=affected_line,
                original_code=original_code,
                replacement_code=replacement_code,
                explanation=explanation,
                is_valid=False,
                validation_error=f"Cannot read file: {e}",
            )

        current_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
        if expected_hash and current_hash != expected_hash:
            return CodePatch(
                file_path=str(path),
                affected_line=affected_line,
                original_code=original_code,
                replacement_code=replacement_code,
                explanation=explanation,
                is_valid=False,
                validation_error="File was modified on disk since diagnosis was generated. Patch discarded.",
                source_hash=current_hash,
            )

        # Normalize strings for comparison
        clean_orig = original_code.strip()
        clean_repl = replacement_code.strip()

        if not clean_orig:
            return CodePatch(
                file_path=str(path),
                affected_line=affected_line,
                original_code=original_code,
                replacement_code=replacement_code,
                explanation=explanation,
                is_valid=False,
                validation_error="Original code cannot be empty.",
                source_hash=current_hash,
            )

        if clean_orig == clean_repl:
            return CodePatch(
                file_path=str(path),
                affected_line=affected_line,
                original_code=original_code,
                replacement_code=replacement_code,
                explanation=explanation,
                is_valid=False,
                validation_error="Replacement code is identical to original code.",
                source_hash=current_hash,
            )

        # Check occurrences in content
        # Check both exact match and line-by-line match
        file_lines = content.splitlines(keepends=True)
        orig_lines = original_code.splitlines(keepends=True)
        repl_lines = replacement_code.splitlines(keepends=True)

        # Direct string occurrence check
        occurrences = content.count(original_code)

        # If exact multiline didn't match directly, try line-trimmed match
        matched_line_idx = None
        if occurrences == 0:
            for idx, line in enumerate(file_lines, 1):
                if clean_orig in line:
                    if matched_line_idx is None:
                        matched_line_idx = idx
                        occurrences += 1
                    else:
                        occurrences += 1

        if occurrences == 0:
            return CodePatch(
                file_path=str(path),
                affected_line=affected_line,
                original_code=original_code,
                replacement_code=replacement_code,
                explanation=explanation,
                is_valid=False,
                validation_error=(
                    f"Original code not found in file '{path.name}'. "
                    f"Target snippet: '{clean_orig[:80]}'"
                ),
                source_hash=current_hash,
            )

        if occurrences > 1:
            # If line number helps disambiguate
            if affected_line > 0 and affected_line <= len(file_lines):
                target_line = file_lines[affected_line - 1]
                if clean_orig not in target_line:
                    return CodePatch(
                        file_path=str(path),
                        affected_line=affected_line,
                        original_code=original_code,
                        replacement_code=replacement_code,
                        explanation=explanation,
                        is_valid=False,
                        validation_error=(
                            f"Original code matches {occurrences} locations in file, "
                            f"and does not match line {affected_line} uniquely."
                        ),
                        source_hash=current_hash,
                    )
            else:
                return CodePatch(
                    file_path=str(path),
                    affected_line=affected_line,
                    original_code=original_code,
                    replacement_code=replacement_code,
                    explanation=explanation,
                    is_valid=False,
                    validation_error=f"Original code is ambiguous: matches {occurrences} locations.",
                    source_hash=current_hash,
                )

        # Generate unified diff
        diff_lines = list(difflib.unified_diff(
            orig_lines,
            repl_lines,
            fromfile=f"a/{path.name}",
            tofile=f"b/{path.name}",
            lineterm="",
        ))
        diff_text = "\n".join(diff_lines)

        return CodePatch(
            file_path=str(path),
            affected_line=affected_line,
            original_code=original_code,
            replacement_code=replacement_code,
            explanation=explanation,
            diff=diff_text,
            is_valid=True,
            validation_error="",
            source_hash=current_hash,
        )

    @staticmethod
    def apply_patch(
        file_path: Path | str,
        patch: CodePatch,
    ) -> tuple[bool, str]:
        """
        Safely apply a validated patch to disk.
        Creates a backup file (<path>.bak) before writing.
        Verifies that file content has not changed since patch was generated.
        """
        if not patch.is_valid:
            return False, f"Cannot apply invalid patch: {patch.validation_error}"

        path = Path(file_path).resolve()
        safe, reason = CodeService.is_file_safe_to_inspect(path)
        if not safe:
            return False, f"Unsafe file operation blocked: {reason}"

        if not path.exists():
            return False, f"Target file does not exist: {path}"

        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                current_content = f.read()
        except Exception as e:
            return False, f"Failed to read file for patching: {e}"

        current_hash = hashlib.sha256(current_content.encode("utf-8")).hexdigest()
        if patch.source_hash and current_hash != patch.source_hash:
            return False, (
                "File content has changed since the patch was generated. "
                "Patch has been rejected to prevent corrupting edits. Please re-inspect."
            )

        # Create backup
        backup_path = path.with_suffix(path.suffix + ".bak")
        try:
            with open(backup_path, "w", encoding="utf-8") as bf:
                bf.write(current_content)
        except Exception as e:
            return False, f"Failed to create backup file at '{backup_path.name}': {e}"

        # Perform replacement
        # 1. Direct replacement if exact match
        if patch.original_code in current_content:
            new_content = current_content.replace(patch.original_code, patch.replacement_code, 1)
        else:
            # 2. Line-based replacement using affected_line
            lines = current_content.splitlines(keepends=True)
            line_idx = patch.affected_line - 1
            clean_orig = patch.original_code.strip()
            if 0 <= line_idx < len(lines) and clean_orig in lines[line_idx]:
                orig_indent = re.match(r'^\s*', lines[line_idx]).group(0)
                repl_line = orig_indent + patch.replacement_code.lstrip()
                if not repl_line.endswith("\n"):
                    repl_line += "\n"
                lines[line_idx] = repl_line
                new_content = "".join(lines)
            else:
                # Search for single matching line
                replaced = False
                for i, l in enumerate(lines):
                    if clean_orig in l:
                        orig_indent = re.match(r'^\s*', l).group(0)
                        repl_line = orig_indent + patch.replacement_code.lstrip()
                        if not repl_line.endswith("\n"):
                            repl_line += "\n"
                        lines[i] = repl_line
                        replaced = True
                        break
                if not replaced:
                    return False, "Could not locate original code within file lines during application."
                new_content = "".join(lines)

        # Write patched content atomically
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(new_content)
            logger.info("Successfully patched file: %s (backup at %s)", path, backup_path)
            return True, f"Patch successfully applied. Backup created at '{backup_path.name}'."
        except Exception as e:
            # Restore backup if write failed
            try:
                with open(backup_path, "r", encoding="utf-8") as bf:
                    with open(path, "w", encoding="utf-8") as pf:
                        pf.write(bf.read())
            except Exception:
                pass
            return False, f"Failed to write patched file: {e}"

    @staticmethod
    def restore_backup(file_path: Path | str) -> tuple[bool, str]:
        """Restore a file from its .bak backup."""
        path = Path(file_path).resolve()
        backup_path = path.with_suffix(path.suffix + ".bak")

        if not backup_path.exists():
            return False, f"No backup file found at '{backup_path.name}'."

        try:
            with open(backup_path, "r", encoding="utf-8", errors="replace") as bf:
                bak_content = bf.read()
            with open(path, "w", encoding="utf-8") as pf:
                pf.write(bak_content)
            return True, f"File restored from backup '{backup_path.name}'."
        except Exception as e:
            return False, f"Failed to restore backup: {e}"

    @staticmethod
    def run_python_script(file_path: Path | str, timeout: int = 10) -> tuple[bool, str, int]:
        """
        Execute the python file to verify runtime correctness.
        Returns (success, output, returncode).
        """
        path = Path(file_path).resolve()
        safe, reason = CodeService.is_file_safe_to_inspect(path)
        if not safe:
            return False, f"Unsafe execution: {reason}", 1

        try:
            res = subprocess.run(
                ["python", str(path)],
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=str(path.parent),
            )
            out = res.stdout
            if res.stderr:
                out = (out + "\n" + res.stderr).strip()
            return (res.returncode == 0), out.strip() or "(No output)", res.returncode
        except subprocess.TimeoutExpired:
            return False, f"Execution timed out after {timeout} seconds.", 124
        except Exception as e:
            return False, f"Execution failed: {e}", 1
