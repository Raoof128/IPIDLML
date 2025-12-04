"""
Analyze API Endpoint

Handles content analysis requests for detecting indirect prompt injection attacks.
Supports text, images (OCR), HTML, and PDF content types.
"""

import hashlib
import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile
from pydantic import BaseModel, Field

from backend.engines.html_extractor import HTMLExtractor
from backend.engines.image_analyzer import ImageAnalyzer
from backend.engines.ocr_engine import OCREngine
from backend.engines.payload_detector import PayloadDetector
from backend.engines.safety_scorer import SafetyScorer
from backend.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()


class ContentType(str, Enum):
    """Supported content types for analysis."""

    TEXT = "text"
    IMAGE = "image"
    HTML = "html"
    PDF = "pdf"


class RiskCategory(str, Enum):
    """Risk categorisation levels."""

    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


class AnalyzeRequest(BaseModel):
    """Request model for content analysis."""

    content: str = Field(..., description="Content to analyze (text, base64 image, or HTML)")
    content_type: ContentType = Field(default=ContentType.TEXT, description="Type of content")
    metadata: Optional[dict] = Field(default=None, description="Additional metadata")


class FlaggedSegment(BaseModel):
    """A flagged segment of content."""

    text: str
    start_index: int
    end_index: int
    reason: str
    confidence: float
    pattern_type: str


class AnalysisResult(BaseModel):
    """Complete analysis result."""

    analysis_id: str
    timestamp: str
    content_hash: str

    # Extraction results
    raw_text: str
    ocr_text: Optional[str] = None
    visual_features: Optional[dict] = None
    extraction_metadata: dict

    # Detection results
    injection_score: float = Field(..., ge=0, le=100)
    flagged_segments: list[FlaggedSegment]
    risk_category: RiskCategory

    # Safety scoring
    safety_score: float = Field(..., ge=0, le=100)
    recommended_action: str

    # Detailed breakdown
    detection_breakdown: dict
    confidence_scores: dict


# Initialize engines
ocr_engine = OCREngine()
html_extractor = HTMLExtractor()
image_analyzer = ImageAnalyzer()
payload_detector = PayloadDetector()
safety_scorer = SafetyScorer()


def _extract_content(content: str, content_type: ContentType) -> tuple[str, Optional[str], Optional[dict], dict]:
    """Extract text and features based on content type."""
    raw_text = ""
    ocr_text = None
    visual_features = None
    extraction_metadata = {"content_type": content_type.value}

    if content_type == ContentType.TEXT:
        raw_text = content
        extraction_metadata["char_count"] = len(raw_text)

    elif content_type == ContentType.IMAGE:
        # OCR extraction for images
        ocr_result = ocr_engine.extract_text(content)
        raw_text = ocr_result["text"]
        ocr_text = ocr_result["text"]
        visual_features = image_analyzer.analyze(content)
        extraction_metadata.update(
            {
                "ocr_confidence": ocr_result["confidence"],
                "has_hidden_text": ocr_result.get("has_hidden_text", False),
            }
        )

    elif content_type == ContentType.HTML:
        # HTML extraction
        html_result = html_extractor.extract(content)
        raw_text = html_result["visible_text"]
        extraction_metadata.update(
            {
                "has_hidden_divs": html_result.get("has_hidden_divs", False),
                "has_suspicious_scripts": html_result.get("has_suspicious_scripts", False),
                "alt_texts": html_result.get("alt_texts", []),
            }
        )

    elif content_type == ContentType.PDF:
        # PDF extraction (simulated)
        raw_text = content  # In real impl, would parse PDF
        extraction_metadata["simulated"] = True
        
    return raw_text, ocr_text, visual_features, extraction_metadata


@router.post("/analyze", response_model=AnalysisResult)
async def analyze_content(request: Request, body: AnalyzeRequest) -> AnalysisResult:
    """
    Analyze content for indirect prompt injection attacks.

    Supports:
    - Raw text analysis
    - Image OCR extraction and analysis
    - HTML content extraction and hidden payload detection
    - PDF text extraction (simulated)

    Returns comprehensive analysis with:
    - Injection score (0-100)
    - Flagged segments with explanations
    - Risk categorisation
    - Safety score and recommended action
    """
    analysis_id = str(uuid.uuid4())
    logger.info(f"Starting analysis {analysis_id} for content type: {body.content_type}")

    try:
        # Step 1: Extract text based on content type
        raw_text, ocr_text, visual_features, extraction_metadata = _extract_content(
            body.content, body.content_type
        )

        # Step 2: Detect payloads
        detection_result = payload_detector.detect(
            raw_text, ocr_text=ocr_text, visual_features=visual_features
        )

        # Step 3: Calculate safety score
        safety_result = safety_scorer.calculate(
            extraction_quality=extraction_metadata,
            detection_result=detection_result,
            content_metadata=body.metadata,
        )

        # Step 4: Generate content hash for auditing
        content_hash = hashlib.sha256(body.content.encode()).hexdigest()[:16]

        # Build flagged segments
        flagged_segments = [
            FlaggedSegment(
                text=seg["text"],
                start_index=seg["start"],
                end_index=seg["end"],
                reason=seg["reason"],
                confidence=seg["confidence"],
                pattern_type=seg["pattern_type"],
            )
            for seg in detection_result["flagged_segments"]
        ]

        # Determine risk category
        injection_score = detection_result["injection_score"]
        if injection_score >= 80:
            risk_category = RiskCategory.CRITICAL
        elif injection_score >= 60:
            risk_category = RiskCategory.HIGH
        elif injection_score >= 40:
            risk_category = RiskCategory.MEDIUM
        else:
            risk_category = RiskCategory.LOW

        # Build result
        result = AnalysisResult(
            analysis_id=analysis_id,
            timestamp=datetime.utcnow().isoformat(),
            content_hash=content_hash,
            raw_text=raw_text[:1000] if len(raw_text) > 1000 else raw_text,
            ocr_text=ocr_text[:500] if ocr_text and len(ocr_text) > 500 else ocr_text,
            visual_features=visual_features,
            extraction_metadata=extraction_metadata,
            injection_score=injection_score,
            flagged_segments=flagged_segments,
            risk_category=risk_category,
            safety_score=safety_result["safety_score"],
            recommended_action=safety_result["recommended_action"],
            detection_breakdown=detection_result["breakdown"],
            confidence_scores=detection_result["confidence_scores"],
        )

        # Store in app state for later retrieval
        if hasattr(request.app.state, "analysis_reports"):
            request.app.state.analysis_reports[analysis_id] = result.model_dump()

        logger.info(
            f"Analysis {analysis_id} complete. Risk: {risk_category}, Score: {injection_score}"
        )
        return result

    except Exception as e:
        logger.error(f"Analysis {analysis_id} failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.post("/analyze/file")
async def analyze_file(
    request: Request,
    file: UploadFile = File(...),
    content_type: ContentType = Form(default=ContentType.IMAGE),
):
    """
    Analyze an uploaded file for prompt injection attacks.

    Supports:
    - Image files (PNG, JPEG, GIF)
    - PDF documents
    - HTML files
    - Text files
    """
    logger.info(f"Received file upload: {file.filename}, type: {content_type}")

    try:
        content = await file.read()

        # For images, use base64
        if content_type == ContentType.IMAGE:
            import base64

            content_str = base64.b64encode(content).decode("utf-8")
        else:
            content_str = content.decode("utf-8", errors="ignore")

        # Reuse the main analyze endpoint logic
        body = AnalyzeRequest(content=content_str, content_type=content_type)
        return await analyze_content(request, body)

    except Exception as e:
        logger.error(f"File analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"File analysis failed: {str(e)}")
