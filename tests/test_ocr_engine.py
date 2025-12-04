"""
Tests for OCR Engine.
"""

import pytest
from unittest.mock import MagicMock, patch
from backend.engines.ocr_engine import OCREngine


class TestOCREngine:
    
    def test_fallback_simulation(self):
        """Test fallback to simulation when Tesseract is unavailable."""
        # Mock check_tesseract to return False
        with patch.object(OCREngine, '_check_tesseract', return_value=False):
            engine = OCREngine(use_tesseract=True)
            result = engine.extract_text("fake_base64_data")
            
            assert result["engine"] == "simulated"
            assert "text" in result
            assert result["confidence"] > 0

    def test_tesseract_execution(self):
        """Test that Tesseract path is taken when available."""
        import sys
        
        # Mock modules
        mock_pytesseract = MagicMock()
        mock_pil = MagicMock()
        
        with patch.dict(sys.modules, {'pytesseract': mock_pytesseract, 'PIL': mock_pil}):
            # Mock Tesseract availability and execution
            with patch.object(OCREngine, '_check_tesseract', return_value=True):
                # Setup mock return values
                mock_pytesseract.image_to_data.return_value = {
                    'text': ['', 'Hello', '', 'World'],
                    'conf': [0, 90, 0, 95]
                }
                mock_pytesseract.Output.DICT = 'dict'
                
                engine = OCREngine(use_tesseract=True)
                # Use a valid base64 string to pass decoding
                valid_b64 = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
                
                result = engine.extract_text(valid_b64)
                
                assert result["engine"] == "tesseract"
                assert result["text"] == "Hello World"
                assert result["confidence"] == 0.925  # (0.9 + 0.95) / 2
