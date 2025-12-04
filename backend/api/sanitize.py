"""
Sanitize API Endpoint

Handles content sanitisation requests to neutralise detected prompt injection payloads.
Supports multiple sanitisation modes: STRICT, BALANCED, PERMISSIVE.
"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.engines.payload_detector import PayloadDetector
from backend.engines.sanitizer import SanitizationMode, Sanitizer
from backend.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()


class SanitizeRequest(BaseModel):
    """Request model for content sanitisation."""

    content: str = Field(..., description="Content to sanitise")
    mode: SanitizationMode = Field(
        default=SanitizationMode.BALANCED,
        description="Sanitisation mode: STRICT, BALANCED, or PERMISSIVE",
    )
    custom_patterns: Optional[list[str]] = Field(
        default=None, description="Additional patterns to sanitise"
    )
    preserve_semantics: bool = Field(
        default=True, description="Attempt to preserve semantic meaning while sanitising"
    )


class SanitizedSegment(BaseModel):
    """Details of a sanitised segment."""

    original: str
    sanitized: str
    start_index: int
    end_index: int
    action_taken: str
    reason: str


class SanitizeResult(BaseModel):
    """Complete sanitisation result."""

    sanitization_id: str
    timestamp: str
    mode: str

    # Input/output
    original_content: str
    sanitized_content: str

    # Changes made
    segments_modified: int
    sanitized_segments: list[SanitizedSegment]

    # Risk assessment
    original_risk_score: float
    post_sanitization_risk_score: float
    risk_reduction: float

    # Actions
    action_taken: str  # BLOCKED, SCRUBBED, WARNED, PASSED
    warnings: list[str]


# Initialize engines
sanitizer = Sanitizer()
payload_detector = PayloadDetector()


@router.post("/sanitize", response_model=SanitizeResult)
async def sanitize_content(body: SanitizeRequest) -> SanitizeResult:
    """
    Sanitise content to neutralise prompt injection payloads.

    Modes:
    - STRICT: Block and log all suspicious content
    - BALANCED: Scrub payloads, pass sanitised content
    - PERMISSIVE: Warn only, pass original content

    Returns:
    - Sanitised content
    - List of modifications made
    - Risk score comparison (before/after)
    """
    import uuid

    sanitization_id = str(uuid.uuid4())
    logger.info(f"Starting sanitisation {sanitization_id} in {body.mode.value} mode")

    try:
        # First detect payloads in original content
        original_detection = payload_detector.detect(body.content)
        original_risk_score = original_detection["injection_score"]

        # Perform sanitisation
        sanitization_result = sanitizer.sanitize(
            content=body.content,
            mode=body.mode,
            custom_patterns=body.custom_patterns,
            preserve_semantics=body.preserve_semantics,
        )

        # Re-analyze sanitised content
        post_detection = payload_detector.detect(sanitization_result["sanitized_content"])
        post_risk_score = post_detection["injection_score"]

        # Calculate risk reduction
        risk_reduction = max(0, original_risk_score - post_risk_score)

        # Determine action taken based on mode and risk
        if body.mode == SanitizationMode.STRICT and original_risk_score >= 40:
            action_taken = "BLOCKED"
        elif body.mode == SanitizationMode.BALANCED:
            action_taken = "SCRUBBED" if sanitization_result["segments_modified"] > 0 else "PASSED"
        elif body.mode == SanitizationMode.PERMISSIVE:
            action_taken = "WARNED" if original_risk_score >= 40 else "PASSED"
        else:
            action_taken = "PASSED"

        # Build sanitised segments
        sanitized_segments = [
            SanitizedSegment(
                original=seg["original"],
                sanitized=seg["sanitized"],
                start_index=seg["start"],
                end_index=seg["end"],
                action_taken=seg["action"],
                reason=seg["reason"],
            )
            for seg in sanitization_result["segments"]
        ]

        result = SanitizeResult(
            sanitization_id=sanitization_id,
            timestamp=datetime.utcnow().isoformat(),
            mode=body.mode.value,
            original_content=body.content[:500] if len(body.content) > 500 else body.content,
            sanitized_content=sanitization_result["sanitized_content"],
            segments_modified=sanitization_result["segments_modified"],
            sanitized_segments=sanitized_segments,
            original_risk_score=original_risk_score,
            post_sanitization_risk_score=post_risk_score,
            risk_reduction=risk_reduction,
            action_taken=action_taken,
            warnings=sanitization_result.get("warnings", []),
        )

        logger.info(
            f"Sanitisation {sanitization_id} complete. "
            f"Action: {action_taken}, Risk: {original_risk_score:.1f} -> {post_risk_score:.1f}"
        )
        return result

    except Exception as e:
        logger.error(f"Sanitisation {sanitization_id} failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Sanitisation failed: {str(e)}")


@router.post("/sanitize/batch")
async def sanitize_batch(contents: list[SanitizeRequest]) -> list[SanitizeResult]:
    """
    Batch sanitisation of multiple content pieces.

    Useful for processing multiple inputs simultaneously.
    """
    results = []
    for content in contents:
        result = await sanitize_content(content)
        results.append(result)
    return results
