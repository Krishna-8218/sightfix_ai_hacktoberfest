"""
SightFix AI — Verification Service

Orchestrates the post-fix verification workflow:
capture a new screenshot → ask the AI to compare → return a typed result.
"""

import logging

from PIL import Image

from services.screenshot_service import ScreenshotService
from services.ai_service import AIService
from services.diagnosis_service import DiagnosisService, VerificationResult

logger = logging.getLogger(__name__)


class VerificationService:
    """Coordinates screenshot capture and AI comparison for fix verification."""

    def __init__(self):
        self._screenshot_svc = ScreenshotService()
        self._ai_svc = AIService()

    def verify(self, image: Image.Image, original_problem_text: str) -> VerificationResult:
        """
        Analyse a new screenshot against the original problem.

        Args:
            image: New screenshot to verify.
            original_problem_text: Description of the original problem.

        Returns:
            VerificationResult with resolved status.
        """
        raw = self._ai_svc.verify(image, original_problem_text)
        return DiagnosisService.parse_verification(raw)
