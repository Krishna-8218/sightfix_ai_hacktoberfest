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
