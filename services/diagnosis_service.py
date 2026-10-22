import logging
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)

@dataclass
class Problem:
    title: str = "Unknown Issue"
    evidence: str = ""
    cause: str = ""
    confidence: str = "low"
    solution_steps: list[str] = field(default_factory=list)
    commands: list[str] = field(default_factory=list)
    verification: str = ""

@dataclass
class Diagnosis:
    has_issue: bool = False
    problems: list[Problem] = field(default_factory=list)
    summary: str = ""
    is_demo: bool = False

@dataclass
class VerificationResult:
    resolved: bool | None = None
    evidence: str = ""
    explanation: str = ""
    remaining_issues: list[str] = field(default_factory=list)
