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

class DiagnosisService:
    @staticmethod
    def parse_diagnosis(raw: dict) -> Diagnosis:
        problems = []
        for p in raw.get("problems", []):
            if isinstance(p, dict):
                problems.append(Problem(
                    title=str(p.get("title", "Unknown Issue")),
                    evidence=str(p.get("evidence", "")),
                    cause=str(p.get("cause", "")),
                    confidence=str(p.get("confidence", "low")).lower(),
                    solution_steps=[str(s) for s in p.get("solution_steps", [])],
                    commands=[str(c) for c in p.get("commands", [])],
                    verification=str(p.get("verification", "")),
                ))
        return Diagnosis(
            has_issue=bool(raw.get("has_issue", len(problems) > 0)),
            problems=problems,
            summary=str(raw.get("summary", "")),
        )

    @staticmethod
    def parse_verification(raw: dict) -> VerificationResult:
        resolved_raw = raw.get("resolved")
        resolved = resolved_raw if isinstance(resolved_raw, bool) else (str(resolved_raw).lower() == "true" if resolved_raw in ("true", "false") else None)
        return VerificationResult(
            resolved=resolved,
            evidence=str(raw.get("evidence", "")),
            explanation=str(raw.get("explanation", "")),
            remaining_issues=[str(i) for i in raw.get("remaining_issues", [])],
        )
