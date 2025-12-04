"""
Embeddings Utility - Sentence embeddings for similarity comparison.
"""

import hashlib
from typing import List

from backend.utils.logger import get_logger

logger = get_logger(__name__)


class EmbeddingEngine:
    """
    Embedding generation and comparison engine.
    Uses SentenceTransformers if available, otherwise falls back to deterministic simulation.
    """

    _instance = None
    _model = None
    _st_available = None  # Tri-state: None, True, False

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(EmbeddingEngine, cls).__new__(cls)
        return cls._instance

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        if not hasattr(self, "initialized"):
            self.model_name = model_name
            self.initialized = True

    @property
    def st_available(self) -> bool:
        """Checks if sentence-transformers is available."""
        if self._st_available is not None:
            return self._st_available

        try:
            import importlib.util

            spec = importlib.util.find_spec("sentence_transformers")
            self._st_available = spec is not None
        except Exception:
            self._st_available = False
        return self._st_available

    def _load_model(self):
        """Lazy loads the SentenceTransformer model."""
        if self._model is not None:
            return

        if not self.st_available:
            return

        try:
            logger.info(f"Loading embedding model: {self.model_name}")
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(self.model_name)
            logger.info("Embedding model loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            self._model = None
            self._st_available = False

    def encode(self, text: str) -> List[float]:
        """Generate embedding for text."""
        if not text:
            return [0.0] * 384

        # Try to load model if available
        if self.st_available:
            self._load_model()

        if self._model:
            try:
                embedding = self._model.encode(text)
                return embedding.tolist()
            except Exception as e:
                logger.error(f"Encoding failed: {e}")
                # Fall through to simulation

        return self._simulated_encode(text)

    def _simulated_encode(self, text: str) -> List[float]:
        """Fallback: Generate deterministic simulated embedding."""
        text_hash = hashlib.sha256(text.encode()).hexdigest()
        embedding = []
        for i in range(384):
            # Generate pseudo-random float between -0.5 and 0.5
            value = ((int(text_hash[i % 64], 16) + i) % 100) / 100 - 0.5
            embedding.append(round(value, 4))
        return embedding

    def similarity(self, text1: str, text2: str) -> float:
        """Calculate cosine similarity between two texts."""
        emb1 = self.encode(text1)
        emb2 = self.encode(text2)

        # Use numpy if available for faster calculation
        try:
            import numpy as np

            v1 = np.array(emb1)
            v2 = np.array(emb2)
            norm1 = np.linalg.norm(v1)
            norm2 = np.linalg.norm(v2)

            if norm1 == 0 or norm2 == 0:
                return 0.0
            return float(np.dot(v1, v2) / (norm1 * norm2))
        except ImportError:
            # Manual calculation
            dot = sum(a * b for a, b in zip(emb1, emb2))
            norm1 = sum(a * a for a in emb1) ** 0.5
            norm2 = sum(b * b for b in emb2) ** 0.5

            if norm1 == 0 or norm2 == 0:
                return 0.0
            return round(dot / (norm1 * norm2), 4)
