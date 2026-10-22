"""
SightFix AI — Diagnosis Service

Validates, enriches, and structures AI model responses into
display-ready diagnosis objects.
"""

import logging
from dataclasses import dataclass, field

from typing import Optional
from services.code_service import CodePatch, FileInspectionResult

logger = logging.getLogger(__name__)


@dataclass
class Problem:
    """A single diagnosed problem."""
    title: str = "Unknown Issue"
    evidence: str = ""
    cause: str = ""
    confidence: str = "low"  # high | medium | low
    solution_steps: list[str] = field(default_factory=list)
    commands: list[str] = field(default_factory=list)
    verification: str = ""


@dataclass
class Diagnosis:
    """Complete diagnosis result from the AI model or compiler inspection."""
    has_issue: bool = False
    problems: list[Problem] = field(default_factory=list)
    summary: str = ""
    is_demo: bool = False  # True when result comes from demo mode
    file_path: Optional[str] = None
    affected_line: Optional[int] = None
    code_patch: Optional[CodePatch] = None
    raw_evidence: str = ""


@dataclass
class VerificationResult:
    """Result of a post-fix verification scan."""
    resolved: bool | None = None  # None means uncertain
    evidence: str = ""
    explanation: str = ""
    remaining_issues: list[str] = field(default_factory=list)


class DiagnosisService:
    """Validates and converts raw AI responses into typed dataclasses."""

    @staticmethod
    def parse_diagnosis(raw: dict) -> Diagnosis:
        """
        Convert a raw dict (from AI or demo) into a Diagnosis.
        Gracefully handles missing or malformed fields.
        """
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
        """Convert a raw verification response into a VerificationResult."""
        resolved_raw = raw.get("resolved")
        if isinstance(resolved_raw, bool):
            resolved = resolved_raw
        elif str(resolved_raw).lower() == "true":
            resolved = True
        elif str(resolved_raw).lower() == "false":
            resolved = False
        else:
            resolved = None  # uncertain

        return VerificationResult(
            resolved=resolved,
            evidence=str(raw.get("evidence", "")),
            explanation=str(raw.get("explanation", "")),
            remaining_issues=[str(i) for i in raw.get("remaining_issues", [])],
        )

    @staticmethod
    def create_file_diagnosis(
        inspection: FileInspectionResult,
        patch: Optional[CodePatch] = None,
        ai_diag_text: str = "",
    ) -> Diagnosis:
        """Construct a diagnosis from real file compiler inspection and code patch."""
        if not inspection.has_error:
            return Diagnosis(
                has_issue=False,
                problems=[],
                summary=f"No errors found in '{inspection.file_path.name}'. Syntax check passed.",
                file_path=str(inspection.file_path),
            )

        cr = inspection.compiler_result
        prob_title = f"{cr.error_type or 'Syntax Error'} in {inspection.file_path.name}"
        if cr.error_line:
            prob_title += f" (Line {cr.error_line})"

        evidence_str = cr.stderr if cr.stderr else cr.error_msg
        if cr.error_snippet:
            evidence_str = f"Line {cr.error_line}: {cr.error_snippet}\n{evidence_str}"

        steps = ["Review the proposed code patch in the 'Proposed Code Fix' panel below."]
        if patch and patch.is_valid:
            steps.append("Click 'Apply Fix' to automatically update the source file and create a backup.")
            steps.append("Verify the file with 'Verify Fix' after applying.")
        else:
            steps.append("Manually inspect and correct the syntax error indicated above.")

        prob = Problem(
            title=prob_title,
            evidence=evidence_str,
            cause=patch.explanation if (patch and patch.explanation) else (ai_diag_text or cr.error_msg),
            confidence="high",
            solution_steps=steps,
            commands=[],  # Code repair is handled by the patch engine, not raw shell execution
            verification="Run python -m py_compile to ensure no syntax errors remain.",
        )

        summary_text = (
            f"Detected syntax error on line {cr.error_line} of {inspection.file_path.name}: {cr.error_msg}"
            if cr.error_line else f"Compiler error in {inspection.file_path.name}: {cr.error_msg}"
        )

        return Diagnosis(
            has_issue=True,
            problems=[prob],
            summary=summary_text,
            file_path=str(inspection.file_path),
            affected_line=cr.error_line,
            code_patch=patch,
            raw_evidence=evidence_str,
        )

    @staticmethod
    def get_demo_diagnosis() -> Diagnosis:
        """Return a realistic demo diagnosis showcasing the calculate_total syntax error and code patch."""
        demo_patch = CodePatch(
            file_path="calculate_total.py",
            affected_line=1,
            original_code="def calculate_total(a, b)",
            replacement_code="def calculate_total(a, b):",
            explanation="In Python, function definitions must terminate with a colon (:).",
            diff=(
                "--- a/calculate_total.py\n"
                "+++ b/calculate_total.py\n"
                "@@ -1,3 +1,3 @@\n"
                "-def calculate_total(a, b)\n"
                "+def calculate_total(a, b):\n"
                "     total = a + b"
            ),
            is_valid=True,
            validation_error="",
        )

        return Diagnosis(
            has_issue=True,
            problems=[
                Problem(
                    title="SyntaxError: expected ':' in calculate_total.py (Line 1)",
                    evidence=(
                        "Line 1: def calculate_total(a, b)\n"
                        "                             ^\n"
                        "SyntaxError: expected ':'"
                    ),
                    cause="The function definition 'def calculate_total(a, b)' is missing the required trailing colon.",
                    confidence="high",
                    solution_steps=[
                        "Add a colon (:) at the end of the function signature on line 1.",
                        "Click 'Apply Fix' below to safely update the file with a backup.",
                        "Click 'Verify Fix' to run python -m py_compile.",
                    ],
                    commands=[],
                    verification="Run 'python -m py_compile calculate_total.py' to confirm clean compilation.",
                ),
            ],
            summary="SyntaxError in calculate_total.py: Missing colon at end of function header on line 1.",
            is_demo=True,
            file_path="calculate_total.py",
            affected_line=1,
            code_patch=demo_patch,
            raw_evidence="SyntaxError: expected ':'",
        )

    @staticmethod
    def get_demo_verification() -> VerificationResult:
        """Return a realistic demo verification result."""
        return VerificationResult(
            resolved=True,
            evidence="The terminal now shows successful script execution with no errors.",
            explanation=(
                "The ModuleNotFoundError is no longer visible. The script appears "
                "to have imported 'requests' successfully and completed execution."
            ),
            remaining_issues=[],
        )
