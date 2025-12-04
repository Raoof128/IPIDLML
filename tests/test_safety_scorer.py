"""
Tests for Safety Scorer.
"""

from typing import Iterator

import pytest

from backend.engines.safety_scorer import SafetyScorer


class TestSafetyScorer:
    """Test suite for SafetyScorer."""

    @pytest.fixture
    def scorer(self) -> Iterator[SafetyScorer]:
        yield SafetyScorer()

    def test_high_safety_score(self, scorer: SafetyScorer) -> None:
        """Test calculation with safe content."""
        extraction_quality = {"has_hidden_text": False, "has_hidden_divs": False}
        detection_result = {"injection_score": 5, "breakdown": {"embedding_score": 5}}

        result = scorer.calculate(extraction_quality, detection_result)

        assert result["safety_score"] >= 80
        assert result["recommended_action"] == "PASS"

    def test_medium_safety_score(self, scorer: SafetyScorer) -> None:
        """Test calculation with moderate risk."""
        extraction_quality = {"has_hidden_text": True}
        detection_result = {"injection_score": 50, "breakdown": {"embedding_score": 30}}

        result = scorer.calculate(extraction_quality, detection_result)

        assert 50 <= result["safety_score"] < 80
        assert result["recommended_action"] == "PASS_WITH_WARNINGS"

    def test_low_safety_score(self, scorer: SafetyScorer) -> None:
        """Test calculation with high risk."""
        extraction_quality = {
            "has_hidden_text": True,
            "has_hidden_divs": True,
            "has_suspicious_scripts": True,
        }
        detection_result = {"injection_score": 90, "breakdown": {"embedding_score": 80}}

        result = scorer.calculate(extraction_quality, detection_result)

        assert result["safety_score"] < 50
        assert result["recommended_action"] == "BLOCK"

    def test_metadata_scoring(self, scorer: SafetyScorer) -> None:
        """Test metadata risk scoring."""
        extraction_quality = {}
        detection_result = {"injection_score": 10, "breakdown": {"embedding_score": 5}}
        content_metadata = {"source": "unknown", "user_reputation": 30}

        result = scorer.calculate(extraction_quality, detection_result, content_metadata)

        assert "component_scores" in result
        assert "metadata_risk" in result["component_scores"]

    def test_none_metadata(self, scorer: SafetyScorer) -> None:
        """Test with None metadata."""
        extraction_quality = {}
        detection_result = {"injection_score": 10, "breakdown": {"embedding_score": 5}}

        result = scorer.calculate(extraction_quality, detection_result, None)

        assert result["component_scores"]["metadata_risk"] == 80.0
