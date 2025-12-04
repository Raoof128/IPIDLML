"""
Tests for Embedding Utility.
"""

from typing import Iterator
from unittest.mock import MagicMock, PropertyMock, patch

import numpy as np
import pytest

from backend.utils.embeddings import EmbeddingEngine


class TestEmbeddingEngine:

    @pytest.fixture
    def engine(self) -> Iterator[EmbeddingEngine]:
        # Reset singleton for each test
        EmbeddingEngine._instance = None
        yield EmbeddingEngine()

    def test_fallback_encoding(self, engine: EmbeddingEngine) -> None:
        """Test that fallback simulation works when ST is missing."""
        with patch(
            "backend.utils.embeddings.EmbeddingEngine.st_available", new_callable=PropertyMock
        ) as mock_avail:
            mock_avail.return_value = False

            emb = engine.encode("test text")
            assert len(emb) == 384
            assert isinstance(emb[0], float)

            # Deterministic check
            emb2 = engine.encode("test text")
            assert emb == emb2

    def test_similarity_calculation(self, engine: EmbeddingEngine) -> None:
        """Test cosine similarity logic."""
        # Use simple vectors for predictable result
        with patch.object(engine, "encode") as mock_encode:
            mock_encode.side_effect = [
                [1.0, 0.0, 0.0],  # Vector A
                [1.0, 0.0, 0.0],  # Vector B (Identical)
            ]
            sim = engine.similarity("a", "b")
            assert sim > 0.99

            mock_encode.side_effect = [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]]  # Orthogonal
            sim = engine.similarity("a", "b")
            assert sim < 0.01

    def test_real_model_loading(self, engine: EmbeddingEngine) -> None:
        """Test that model loading is attempted when available."""
        import sys

        # Mock the module existence
        mock_module = MagicMock()
        with patch.dict(sys.modules, {"sentence_transformers": mock_module}):
            with patch(
                "backend.utils.embeddings.EmbeddingEngine.st_available", new_callable=PropertyMock
            ) as mock_avail:
                mock_avail.return_value = True

                # Now we can patch the class inside the mocked module
                mock_module.SentenceTransformer.return_value.encode.return_value = np.array(
                    [0.1] * 384
                )

                emb = engine.encode("real test")

                mock_module.SentenceTransformer.assert_called_once()
                assert len(emb) == 384
