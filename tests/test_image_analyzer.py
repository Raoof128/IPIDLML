"""
Tests for Image Analyzer.
"""

from typing import Iterator

import pytest

from backend.engines.image_analyzer import ImageAnalyzer


class TestImageAnalyzer:
    """Test suite for ImageAnalyzer."""

    @pytest.fixture
    def analyzer(self) -> Iterator[ImageAnalyzer]:
        yield ImageAnalyzer()

    def test_analyze_base64_image(self, analyzer: ImageAnalyzer) -> None:
        """Test analyzing a base64 encoded image."""
        # Simple 1x1 pixel PNG
        valid_b64 = (
            "data:image/png;base64,"
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
        )
        result = analyzer.analyze(valid_b64)

        assert "adversarial_score" in result
        assert "visual_features" in result
        assert "anomaly_flags" in result

    def test_invalid_image_data(self, analyzer: ImageAnalyzer) -> None:
        """Test handling of invalid image data."""
        result = analyzer.analyze("invalid_base64_data")

        assert result["adversarial_score"] >= 0
        assert "error" in result or "simulated" in str(result).lower()

    def test_adversarial_detection(self, analyzer: ImageAnalyzer) -> None:
        """Test adversarial pattern detection."""
        valid_b64 = (
            "data:image/png;base64,"
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
        )
        result = analyzer.analyze(valid_b64)

        assert "adversarial_score" in result
        assert 0 <= result["adversarial_score"] <= 100
