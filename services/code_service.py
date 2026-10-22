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
SENSITIVE_PATTERNS = ["*.env*", "*.pem", "*.key", "id_rsa*", "*.git*"]

@dataclass
class CompilerResult:
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
    file_path: str
    affected_line: int
    original_code: str
    replacement_code: str
    explanation: str
    diff: str = ""
    is_valid: bool = False
    validation_error: str = ""
    source_hash: str = ""

class CodeService:
    @staticmethod
    def is_file_safe_to_inspect(path: Path) -> tuple[bool, str]:
        resolved = path.resolve()
        if not resolved.exists():
            return False, f"File does not exist: {resolved}"
        filename = resolved.name.lower()
        for pattern in SENSITIVE_PATTERNS:
            if fnmatch.fnmatch(filename, pattern):
                return False, f"Access blocked: '{filename}' matches sensitive pattern"
        return True, "File is safe to inspect."

    @staticmethod
    def compile_check(file_path: Path | str) -> CompilerResult:
        path = Path(file_path).resolve()
        if path.suffix.lower() != ".py":
            return CompilerResult(exit_code=0, stdout="", stderr="", has_error=False)
        try:
            res = subprocess.run(["python", "-m", "py_compile", str(path)], capture_output=True, text=True, timeout=10)
            if res.returncode == 0:
                return CompilerResult(exit_code=0, stdout=res.stdout, stderr=res.stderr, has_error=False)
            line_no = None
            line_match = re.search(r'line\s+(\d+)', res.stderr, re.IGNORECASE)
            if line_match:
                line_no = int(line_match.group(1))
            return CompilerResult(exit_code=res.returncode, stdout=res.stdout, stderr=res.stderr.strip(), has_error=True, error_line=line_no, error_type="SyntaxError", error_msg=res.stderr.strip())
        except Exception as e:
            return CompilerResult(exit_code=1, stdout="", stderr=str(e), has_error=True, error_msg=str(e))
