"""
LLM Proxy API Endpoint

Middleware gateway that intercepts LLM requests, analyzes them for prompt injection,
sanitises if necessary, and proxies to a (simulated) LLM endpoint.
"""

import uuid
import hashlib
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from backend.engines.payload_detector import PayloadDetector
from backend.engines.sanitizer import Sanitizer, SanitizationMode
from backend.engines.safety_scorer import SafetyScorer
from backend.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()


class LLMRequest(BaseModel):
    """Request model for LLM proxy."""
    prompt: str = Field(..., description="User prompt to send to LLM")
    system_message: Optional[str] = Field(
        default=None,
        description="System message for the LLM"
    )
    model: str = Field(default="gpt-4-simulated", description="Target LLM model")
    max_tokens: int = Field(default=1000, description="Maximum tokens in response")
    temperature: float = Field(default=0.7, ge=0, le=2)
    sanitization_mode: SanitizationMode = Field(
        default=SanitizationMode.BALANCED,
        description="Sanitisation mode for detected threats"
    )


class ProxyAuditLog(BaseModel):
    """Audit log entry for proxy request."""
    original_prompt: str
    sanitized_prompt: str
    was_modified: bool
    injection_score: float
    risk_category: str
    action_taken: str
    input_hash: str
    output_hash: str


class LLMProxyResult(BaseModel):
    """Complete proxy result including analysis and response."""
    request_id: str
    timestamp: str
    
    # Analysis results
    injection_detected: bool
    injection_score: float
    risk_category: str
    flagged_patterns: list[str]
    
    # Sanitisation
    was_sanitized: bool
    sanitization_action: str
    original_prompt: str
    sanitized_prompt: str
    
    # LLM Response (simulated)
    llm_response: str
    model_used: str
    
    # Audit
    audit_log: ProxyAuditLog
    compliance_tags: list[str]


# Initialize engines
payload_detector = PayloadDetector()
sanitizer = Sanitizer()
safety_scorer = SafetyScorer()


def mock_llm(prompt: str, system_message: Optional[str] = None, model: str = "gpt-4") -> str:
    """
    Simulated LLM response for testing.
    
    In production, this would call the actual LLM API.
    Returns deterministic safe responses.
    """
    # Deterministic responses based on prompt characteristics
    prompt_lower = prompt.lower()
    
    if "hello" in prompt_lower or "hi" in prompt_lower:
        return "Hello! I'm a simulated LLM assistant. How can I help you today?"
    
    elif "explain" in prompt_lower:
        return (
            "I'd be happy to help explain that concept. Based on my understanding, "
            "this topic involves several key aspects that are worth exploring. "
            "Would you like me to elaborate on any specific area?"
        )
    
    elif "write" in prompt_lower or "create" in prompt_lower:
        return (
            "Here's a draft based on your request:\n\n"
            "[Simulated content would appear here]\n\n"
            "This is a safe, simulated response from the IPI-Shield mock LLM. "
            "In production, this would be replaced with actual LLM output."
        )
    
    elif "code" in prompt_lower or "function" in prompt_lower:
        return (
            "```python\n"
            "def example_function():\n"
            "    '''Simulated code response'''\n"
            "    return 'This is a mock response'\n"
            "```\n\n"
            "This is a simulated code response from IPI-Shield."
        )
    
    else:
        return (
            f"Thank you for your query. I've processed your request safely.\n\n"
            f"[Simulated LLM Response]\n"
            f"Model: {model}\n"
            f"Status: Request processed through IPI-Shield protection layer.\n\n"
            f"This response demonstrates the proxy functionality. "
            f"Your input was analyzed for prompt injection before reaching the LLM."
        )


@router.post("/proxy_llm", response_model=LLMProxyResult)
async def proxy_llm_request(
    request: Request,
    body: LLMRequest
) -> LLMProxyResult:
    """
    Proxy an LLM request through the IPI-Shield protection layer.
    
    Pipeline:
    1. Analyze prompt for injection attacks
    2. Sanitise if threats detected
    3. Forward to LLM (simulated)
    4. Log and audit the transaction
    5. Return response with analysis metadata
    """
    request_id = str(uuid.uuid4())
    logger.info(f"Proxy request {request_id}: Analyzing prompt for injection attacks")
    
    try:
        # Step 1: Detect payloads in the prompt
        detection_result = payload_detector.detect(body.prompt)
        injection_score = detection_result["injection_score"]
        
        # Determine risk category
        if injection_score >= 80:
            risk_category = "Critical"
        elif injection_score >= 60:
            risk_category = "High"
        elif injection_score >= 40:
            risk_category = "Medium"
        else:
            risk_category = "Low"
        
        injection_detected = injection_score >= 30
        flagged_patterns = [seg["pattern_type"] for seg in detection_result["flagged_segments"]]
        
        # Step 2: Sanitise if necessary
        sanitized_prompt = body.prompt
        was_sanitized = False
        sanitization_action = "NONE"
        
        if injection_detected:
            sanitization_result = sanitizer.sanitize(
                content=body.prompt,
                mode=body.sanitization_mode,
                preserve_semantics=True
            )
            
            if sanitization_result["segments_modified"] > 0:
                sanitized_prompt = sanitization_result["sanitized_content"]
                was_sanitized = True
                
                if body.sanitization_mode == SanitizationMode.STRICT:
                    sanitization_action = "BLOCKED"
                else:
                    sanitization_action = "SCRUBBED"
            else:
                sanitization_action = "PASSED_WITH_WARNING"
        else:
            sanitization_action = "PASSED"
        
        # Step 3: Call LLM (simulated) - only if not blocked
        if sanitization_action == "BLOCKED":
            llm_response = (
                "[REQUEST BLOCKED]\n"
                "This request was blocked by IPI-Shield due to detected prompt injection patterns.\n"
                f"Risk Score: {injection_score}/100\n"
                f"Risk Category: {risk_category}\n"
                "Please review your input and remove any suspicious content."
            )
        else:
            llm_response = mock_llm(
                prompt=sanitized_prompt,
                system_message=body.system_message,
                model=body.model
            )
        
        # Step 4: Create audit log
        input_hash = hashlib.sha256(body.prompt.encode()).hexdigest()[:16]
        output_hash = hashlib.sha256(llm_response.encode()).hexdigest()[:16]
        
        audit_log = ProxyAuditLog(
            original_prompt=body.prompt[:200] + "..." if len(body.prompt) > 200 else body.prompt,
            sanitized_prompt=sanitized_prompt[:200] + "..." if len(sanitized_prompt) > 200 else sanitized_prompt,
            was_modified=was_sanitized,
            injection_score=injection_score,
            risk_category=risk_category,
            action_taken=sanitization_action,
            input_hash=input_hash,
            output_hash=output_hash
        )
        
        # Step 5: Compliance tagging
        compliance_tags = []
        if injection_score < 30:
            compliance_tags.append("ISO42001_COMPLIANT")
        if was_sanitized:
            compliance_tags.append("NIST_AI_RMF_SANITIZED")
        if sanitization_action != "BLOCKED":
            compliance_tags.append("SOCI_PASS")
        compliance_tags.append("AUDIT_TRAIL_COMPLETE")
        
        result = LLMProxyResult(
            request_id=request_id,
            timestamp=datetime.utcnow().isoformat(),
            injection_detected=injection_detected,
            injection_score=injection_score,
            risk_category=risk_category,
            flagged_patterns=list(set(flagged_patterns)),
            was_sanitized=was_sanitized,
            sanitization_action=sanitization_action,
            original_prompt=body.prompt[:500] if len(body.prompt) > 500 else body.prompt,
            sanitized_prompt=sanitized_prompt[:500] if len(sanitized_prompt) > 500 else sanitized_prompt,
            llm_response=llm_response,
            model_used=body.model,
            audit_log=audit_log,
            compliance_tags=compliance_tags
        )
        
        logger.info(
            f"Proxy request {request_id} complete. "
            f"Injection: {injection_detected}, Action: {sanitization_action}"
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Proxy request {request_id} failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Proxy request failed: {str(e)}")


@router.get("/proxy/stats")
async def get_proxy_stats():
    """Get statistics about proxy usage and threats detected."""
    return {
        "total_requests": 0,  # Would be tracked in production
        "threats_detected": 0,
        "requests_blocked": 0,
        "requests_sanitized": 0,
        "requests_passed": 0,
        "average_injection_score": 0.0,
        "last_updated": datetime.utcnow().isoformat()
    }
