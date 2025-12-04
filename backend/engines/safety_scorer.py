"""
Safety Scorer - Combines multiple signals to produce trust and safety scores.
"""

from typing import Optional

from backend.utils.logger import get_logger

logger = get_logger(__name__)


class SafetyScorer:
    """Trust and safety scoring engine."""

    def __init__(self):
        self.weights = {
            "extraction_quality": 0.15,
            "detection_signal": 0.45,
            "embedding_drift": 0.20,
            "metadata_risk": 0.20,
        }

    def calculate(
        self,
        extraction_quality: dict,
        detection_result: dict,
        content_metadata: Optional[dict] = None,
    ) -> dict:
        logger.info("Calculating safety score")

        extraction_score = self._score_extraction(extraction_quality)
        detection_score = 100 - detection_result.get("injection_score", 0)
        drift_score = self._calculate_drift_score(detection_result)
        metadata_score = self._score_metadata(content_metadata)

        weighted = (
            extraction_score * self.weights["extraction_quality"]
            + detection_score * self.weights["detection_signal"]
            + drift_score * self.weights["embedding_drift"]
            + metadata_score * self.weights["metadata_risk"]
        )

        safety_score = max(0, min(100, weighted))

        if safety_score >= 80:
            action = "PASS"
        elif safety_score >= 50:
            action = "PASS_WITH_WARNINGS"
        else:
            action = "BLOCK"

        return {
            "safety_score": round(safety_score, 2),
            "recommended_action": action,
            "component_scores": {
                "extraction_quality": round(extraction_score, 2),
                "detection_safety": round(detection_score, 2),
                "embedding_drift": round(drift_score, 2),
                "metadata_risk": round(metadata_score, 2),
            },
            "confidence": 0.85,
        }

    def _score_extraction(self, quality: dict) -> float:
        score = 90.0
        if quality.get("has_hidden_text"):
            score -= 20
        if quality.get("has_hidden_divs"):
            score -= 15
        if quality.get("has_suspicious_scripts"):
            score -= 25
        return max(0, score)

    def _calculate_drift_score(self, detection_result: dict) -> float:
        breakdown = detection_result.get("breakdown", {})
        embedding_score = breakdown.get("embedding_score", 0)
        return max(0, 100 - embedding_score)

    def _score_metadata(self, metadata: Optional[dict]) -> float:
        if not metadata:
            return 80.0
        score = 90.0
        if metadata.get("source") == "unknown":
            score -= 20
        if metadata.get("user_reputation", 100) < 50:
            score -= 15
        return max(0, score)
