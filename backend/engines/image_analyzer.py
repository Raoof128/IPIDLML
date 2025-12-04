"""
Image Analyzer

Analyzes images for visual features that may indicate prompt injection attacks.
Includes adversarial patch detection, visual embedding analysis, and anomaly scoring.
"""

import base64
import hashlib
from typing import Optional

from backend.utils.logger import get_logger

logger = get_logger(__name__)


class ImageAnalyzer:
    """
    Image analysis engine for visual content security.
    
    Features:
    - Visual embedding extraction (simulated)
    - Adversarial patch detection (mock)
    - Color anomaly detection
    - Steganography likelihood assessment
    - QR code/barcode detection
    """
    
    def __init__(self, use_embeddings: bool = False):
        """
        Initialize the image analyzer.
        
        Args:
            use_embeddings: Whether to use actual visual embeddings (requires torch)
        """
        self.use_embeddings = use_embeddings
        self._model_loaded = False
        
        # Known adversarial patch signatures (simulated)
        self.adversarial_signatures = [
            "high_frequency_noise",
            "unnatural_color_distribution",
            "grid_pattern_artifact",
            "repetitive_texture",
        ]
    
    def analyze(self, image_data: str) -> dict:
        """
        Analyze an image for security-relevant features.
        
        Args:
            image_data: Base64 encoded image data
            
        Returns:
            dict: {
                "visual_embedding": embedding vector or hash,
                "adversarial_score": likelihood of adversarial content (0-1),
                "anomaly_indicators": list of detected anomalies,
                "color_analysis": color distribution analysis,
                "has_text_overlay": whether text was detected,
                "metadata": image metadata
            }
        """
        logger.info("Analyzing image for security features")
        
        # Generate deterministic hash for consistency
        data_hash = hashlib.sha256(image_data[:1000].encode()).hexdigest()
        
        result = {
            "visual_embedding": self._generate_embedding(image_data, data_hash),
            "adversarial_score": self._calculate_adversarial_score(data_hash),
            "anomaly_indicators": self._detect_anomalies(data_hash),
            "color_analysis": self._analyze_colors(data_hash),
            "has_text_overlay": self._detect_text_overlay(data_hash),
            "metadata": self._extract_metadata(image_data),
            "analysis_mode": "simulated"
        }
        
        return result
    
    def _generate_embedding(self, image_data: str, data_hash: str) -> dict:
        """Generate visual embedding for the image."""
        # In production, this would use a vision model like CLIP
        # For now, generate a deterministic pseudo-embedding
        
        embedding_seed = int(data_hash[:8], 16)
        
        # Create a simple embedding representation
        pseudo_embedding = []
        for i in range(128):  # 128-dimensional embedding
            value = ((embedding_seed + i * 7919) % 1000) / 1000.0 - 0.5
            pseudo_embedding.append(round(value, 4))
        
        return {
            "dimensions": 128,
            "vector_hash": data_hash[:16],
            "model": "simulated_clip",
            "note": "Simulated embedding for demonstration"
        }
    
    def _calculate_adversarial_score(self, data_hash: str) -> float:
        """
        Calculate likelihood of adversarial content.
        
        Returns a score between 0 (safe) and 1 (likely adversarial).
        """
        # Deterministic but varied scoring based on hash
        hash_value = int(data_hash[:8], 16)
        
        # Most images should score low
        base_score = (hash_value % 100) / 1000.0  # 0-0.1 base
        
        # Occasionally add some variance for testing
        if hash_value % 20 == 0:
            base_score += 0.3
        
        return min(base_score, 0.5)  # Cap at 0.5 for safety
    
    def _detect_anomalies(self, data_hash: str) -> list[dict]:
        """Detect visual anomalies in the image."""
        anomalies = []
        hash_value = int(data_hash[:8], 16)
        
        # Simulate various anomaly types
        if hash_value % 15 == 0:
            anomalies.append({
                "type": "high_frequency_noise",
                "severity": "low",
                "description": "Detected areas with unusual high-frequency patterns",
                "confidence": 0.6
            })
        
        if hash_value % 23 == 0:
            anomalies.append({
                "type": "color_discontinuity",
                "severity": "low",
                "description": "Sharp color boundaries detected that may indicate overlay",
                "confidence": 0.5
            })
        
        if hash_value % 37 == 0:
            anomalies.append({
                "type": "aspect_ratio_artifact",
                "severity": "low",
                "description": "Image dimensions suggest possible manipulation",
                "confidence": 0.4
            })
        
        return anomalies
    
    def _analyze_colors(self, data_hash: str) -> dict:
        """Analyze color distribution."""
        hash_value = int(data_hash[:12], 16)
        
        return {
            "dominant_colors": [
                {"color": "#3B82F6", "percentage": 25},
                {"color": "#1F2937", "percentage": 35},
                {"color": "#F3F4F6", "percentage": 20},
                {"color": "#10B981", "percentage": 10},
                {"color": "#EF4444", "percentage": 10},
            ],
            "color_entropy": round((hash_value % 100) / 100.0 * 0.8 + 0.2, 3),
            "has_unusual_distribution": (hash_value % 50) == 0,
            "analysis_note": "Simulated color analysis"
        }
    
    def _detect_text_overlay(self, data_hash: str) -> bool:
        """Detect if image contains text overlays."""
        hash_value = int(data_hash[:6], 16)
        return (hash_value % 3) == 0
    
    def _extract_metadata(self, image_data: str) -> dict:
        """Extract image metadata."""
        # Try to decode and get basic info
        try:
            # Check if it's a data URL
            if image_data.startswith('data:image'):
                parts = image_data.split(',')
                mime_type = parts[0].split(':')[1].split(';')[0]
                actual_data = parts[1] if len(parts) > 1 else ""
            else:
                mime_type = "unknown"
                actual_data = image_data
            
            # Calculate size
            data_size = len(actual_data) * 3 // 4  # Approximate decoded size
            
            return {
                "mime_type": mime_type,
                "encoded_size": len(image_data),
                "estimated_decoded_size": data_size,
                "has_exif": False,  # Would check in production
                "format_valid": True
            }
            
        except Exception as e:
            return {
                "error": str(e),
                "format_valid": False
            }
    
    def compare_embeddings(
        self, 
        embedding1: dict, 
        embedding2: dict
    ) -> float:
        """
        Compare two image embeddings for similarity.
        
        Returns cosine similarity score (0-1).
        """
        # Simulated comparison
        hash1 = embedding1.get("vector_hash", "")
        hash2 = embedding2.get("vector_hash", "")
        
        if hash1 == hash2:
            return 1.0
        
        # Compare hashes character by character
        matches = sum(1 for a, b in zip(hash1, hash2) if a == b)
        similarity = matches / max(len(hash1), len(hash2), 1)
        
        return round(similarity, 4)
    
    def detect_adversarial_patches(self, image_data: str) -> dict:
        """
        Detect known adversarial patch patterns.
        
        Adversarial patches are designed to fool ML models.
        This is a mock implementation for demonstration.
        """
        data_hash = hashlib.sha256(image_data[:500].encode()).hexdigest()
        hash_value = int(data_hash[:8], 16)
        
        detected_patches = []
        
        # Simulate detection (rare events)
        if hash_value % 100 < 5:  # 5% chance for demo
            detected_patches.append({
                "patch_type": "adversarial_example",
                "location": {"x": 100, "y": 150, "width": 50, "height": 50},
                "confidence": 0.65,
                "description": "Potential adversarial pattern detected (simulated)"
            })
        
        return {
            "patches_detected": len(detected_patches),
            "patches": detected_patches,
            "analysis_complete": True,
            "note": "Mock adversarial patch detection for demonstration"
        }
    
    def assess_steganography_risk(self, image_data: str) -> dict:
        """
        Assess likelihood of steganographic content.
        
        Steganography hides data within images.
        """
        data_hash = hashlib.sha256(image_data[:500].encode()).hexdigest()
        hash_value = int(data_hash[:8], 16)
        
        # Base risk is low
        risk_score = (hash_value % 30) / 100.0
        
        indicators = []
        if risk_score > 0.15:
            indicators.append("LSB pattern anomaly detected")
        if risk_score > 0.20:
            indicators.append("Unusual bit distribution in color channels")
        
        return {
            "risk_score": round(risk_score, 3),
            "risk_level": "low" if risk_score < 0.2 else "medium",
            "indicators": indicators,
            "note": "Simulated steganography analysis"
        }
