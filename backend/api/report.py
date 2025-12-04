"""
Report API Endpoint

Handles report generation and retrieval for IPI-Shield analysis results.
Supports PDF export, compliance mapping, and governance reporting.
"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from backend.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()


class ComplianceMapping(BaseModel):
    """Compliance framework mapping."""
    framework: str
    controls: list[str]
    status: str
    notes: str


class SafetyReport(BaseModel):
    """Comprehensive safety report."""
    report_id: str
    generated_at: str
    
    # Analysis summary
    analysis_id: str
    content_type: str
    injection_score: float
    risk_category: str
    recommended_action: str
    
    # Highlighted risks
    flagged_segments_count: int
    flagged_segments: list[dict]
    
    # Audit info
    input_hash: str
    output_hash: Optional[str] = None
    
    # Compliance
    compliance_mappings: list[ComplianceMapping]
    
    # Governance
    iso_42001_status: str
    nist_ai_rmf_status: str
    soci_act_status: str


@router.get("/report/{analysis_id}")
async def get_report(
    analysis_id: str,
    request: Request,
    include_compliance: bool = True
) -> SafetyReport:
    """
    Retrieve a detailed safety report for a previous analysis.
    
    Includes:
    - Analysis summary with risk assessment
    - Flagged segments with explanations
    - Input/output hashes for auditing
    - Compliance framework mappings
    """
    logger.info(f"Retrieving report for analysis {analysis_id}")
    
    # Look up analysis in app state
    analysis_reports = getattr(request.app.state, 'analysis_reports', {})
    
    if analysis_id not in analysis_reports:
        # Generate a sample report for demo purposes
        sample_report = _generate_sample_report(analysis_id)
        if sample_report:
            return sample_report
        raise HTTPException(status_code=404, detail=f"Analysis {analysis_id} not found")
    
    analysis = analysis_reports[analysis_id]
    
    # Build compliance mappings
    compliance_mappings = []
    if include_compliance:
        compliance_mappings = _build_compliance_mappings(analysis)
    
    return SafetyReport(
        report_id=f"RPT-{analysis_id[:8]}",
        generated_at=datetime.utcnow().isoformat(),
        analysis_id=analysis_id,
        content_type=analysis.get("extraction_metadata", {}).get("content_type", "unknown"),
        injection_score=analysis.get("injection_score", 0),
        risk_category=analysis.get("risk_category", "Unknown"),
        recommended_action=analysis.get("recommended_action", "REVIEW"),
        flagged_segments_count=len(analysis.get("flagged_segments", [])),
        flagged_segments=analysis.get("flagged_segments", []),
        input_hash=analysis.get("content_hash", "unknown"),
        output_hash=None,
        compliance_mappings=compliance_mappings,
        iso_42001_status=_assess_iso_42001(analysis),
        nist_ai_rmf_status=_assess_nist_ai_rmf(analysis),
        soci_act_status=_assess_soci_act(analysis)
    )


def _generate_sample_report(analysis_id: str) -> Optional[SafetyReport]:
    """Generate a sample report for demonstration."""
    # Return a sample report for any ID starting with 'demo'
    if not analysis_id.startswith("demo"):
        return None
        
    return SafetyReport(
        report_id=f"RPT-{analysis_id[:8]}",
        generated_at=datetime.utcnow().isoformat(),
        analysis_id=analysis_id,
        content_type="text",
        injection_score=25.0,
        risk_category="Low",
        recommended_action="PASS",
        flagged_segments_count=0,
        flagged_segments=[],
        input_hash="abc123def456",
        output_hash=None,
        compliance_mappings=[
            ComplianceMapping(
                framework="ISO/IEC 42001",
                controls=["6.1.4", "7.2.1"],
                status="COMPLIANT",
                notes="AI safety controls properly implemented"
            )
        ],
        iso_42001_status="COMPLIANT",
        nist_ai_rmf_status="ALIGNED",
        soci_act_status="NOT_APPLICABLE"
    )


def _build_compliance_mappings(analysis: dict) -> list[ComplianceMapping]:
    """Build compliance framework mappings based on analysis results."""
    risk_score = analysis.get("injection_score", 0)
    
    mappings = []
    
    # ISO/IEC 42001 - AI Management System
    iso_status = "COMPLIANT" if risk_score < 40 else "REQUIRES_REVIEW"
    mappings.append(ComplianceMapping(
        framework="ISO/IEC 42001",
        controls=["6.1.4 - Risk Treatment", "7.2.1 - Input Validation", "8.3.1 - AI Safety"],
        status=iso_status,
        notes="AI system safety controls for prompt injection mitigation"
    ))
    
    # NIST AI RMF
    nist_status = "ALIGNED" if risk_score < 60 else "REQUIRES_ACTION"
    mappings.append(ComplianceMapping(
        framework="NIST AI RMF",
        controls=["GOVERN 1.2", "MAP 3.1", "MEASURE 2.5", "MANAGE 4.2"],
        status=nist_status,
        notes="Risk measurement and management for AI system inputs"
    ))
    
    # SOCI Act (Australian Critical Infrastructure)
    soci_status = "COMPLIANT" if risk_score < 50 else "REVIEW_REQUIRED"
    mappings.append(ComplianceMapping(
        framework="SOCI Act 2018",
        controls=["Critical Infrastructure Risk Management Program"],
        status=soci_status,
        notes="Applicable for systems classified as critical infrastructure"
    ))
    
    return mappings


def _assess_iso_42001(analysis: dict) -> str:
    """Assess ISO/IEC 42001 compliance status."""
    risk_score = analysis.get("injection_score", 0)
    if risk_score < 30:
        return "FULLY_COMPLIANT"
    elif risk_score < 50:
        return "COMPLIANT_WITH_OBSERVATIONS"
    elif risk_score < 70:
        return "REQUIRES_CORRECTIVE_ACTION"
    else:
        return "NON_COMPLIANT"


def _assess_nist_ai_rmf(analysis: dict) -> str:
    """Assess NIST AI RMF alignment status."""
    risk_score = analysis.get("injection_score", 0)
    if risk_score < 40:
        return "FULLY_ALIGNED"
    elif risk_score < 60:
        return "PARTIALLY_ALIGNED"
    else:
        return "REQUIRES_REMEDIATION"


def _assess_soci_act(analysis: dict) -> str:
    """Assess SOCI Act compliance status (Australian Critical Infrastructure)."""
    risk_score = analysis.get("injection_score", 0)
    if risk_score < 50:
        return "COMPLIANT"
    else:
        return "REQUIRES_REVIEW"


@router.get("/report/{analysis_id}/html", response_class=HTMLResponse)
async def get_report_html(analysis_id: str, request: Request):
    """Generate an HTML version of the safety report."""
    try:
        report = await get_report(analysis_id, request, include_compliance=True)
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>IPI-Shield Safety Report - {report.report_id}</title>
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
                       max-width: 800px; margin: 0 auto; padding: 20px; background: #0f0f1a; color: #e0e0e0; }}
                h1 {{ color: #7c3aed; }}
                h2 {{ color: #a78bfa; border-bottom: 1px solid #333; padding-bottom: 10px; }}
                .badge {{ display: inline-block; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: bold; }}
                .badge-low {{ background: #22c55e33; color: #22c55e; }}
                .badge-medium {{ background: #f59e0b33; color: #f59e0b; }}
                .badge-high {{ background: #ef444433; color: #ef4444; }}
                .badge-critical {{ background: #dc262633; color: #dc2626; }}
                .card {{ background: #1a1a2e; border-radius: 8px; padding: 20px; margin: 15px 0; border: 1px solid #333; }}
                .score {{ font-size: 48px; font-weight: bold; color: #7c3aed; }}
                table {{ width: 100%; border-collapse: collapse; }}
                th, td {{ text-align: left; padding: 10px; border-bottom: 1px solid #333; }}
                th {{ color: #a78bfa; }}
                .footer {{ margin-top: 40px; padding-top: 20px; border-top: 1px solid #333; color: #666; font-size: 12px; }}
            </style>
        </head>
        <body>
            <h1>🛡️ IPI-Shield Safety Report</h1>
            <p><strong>Report ID:</strong> {report.report_id}</p>
            <p><strong>Generated:</strong> {report.generated_at}</p>
            
            <div class="card">
                <h2>Risk Assessment</h2>
                <p class="score">{report.injection_score:.0f}/100</p>
                <p><span class="badge badge-{report.risk_category.lower()}">{report.risk_category}</span></p>
                <p><strong>Recommended Action:</strong> {report.recommended_action}</p>
            </div>
            
            <div class="card">
                <h2>Flagged Segments</h2>
                <p><strong>Count:</strong> {report.flagged_segments_count}</p>
            </div>
            
            <div class="card">
                <h2>Compliance Status</h2>
                <table>
                    <tr><th>Framework</th><th>Status</th></tr>
                    <tr><td>ISO/IEC 42001</td><td>{report.iso_42001_status}</td></tr>
                    <tr><td>NIST AI RMF</td><td>{report.nist_ai_rmf_status}</td></tr>
                    <tr><td>SOCI Act (AU)</td><td>{report.soci_act_status}</td></tr>
                </table>
            </div>
            
            <div class="card">
                <h2>Audit Trail</h2>
                <p><strong>Analysis ID:</strong> {report.analysis_id}</p>
                <p><strong>Input Hash:</strong> {report.input_hash}</p>
            </div>
            
            <div class="footer">
                <p>Generated by IPI-Shield v1.0.0 | For educational and defence purposes only</p>
            </div>
        </body>
        </html>
        """
        return HTMLResponse(content=html_content)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/reports")
async def list_reports(request: Request, limit: int = 20):
    """List all available analysis reports."""
    analysis_reports = getattr(request.app.state, 'analysis_reports', {})
    
    reports = []
    for analysis_id, data in list(analysis_reports.items())[:limit]:
        reports.append({
            "analysis_id": analysis_id,
            "timestamp": data.get("timestamp"),
            "risk_category": data.get("risk_category"),
            "injection_score": data.get("injection_score"),
        })
    
    return {
        "total": len(analysis_reports),
        "limit": limit,
        "reports": reports
    }
