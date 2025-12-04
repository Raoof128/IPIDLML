"""
IPI-Shield Main Application

FastAPI-based middleware for Indirect Prompt Injection detection and sanitisation.
Serves as a security proxy layer between users and LLM endpoints.
"""

import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from typing import AsyncGenerator, Callable

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, Response

from backend.api import analyze, proxy, report, sanitize
from backend.config import settings
from backend.utils.logger import get_logger

logger = get_logger(__name__)


# In-memory storage for reports (production would use a database)
analysis_reports: dict = {}


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler for startup/shutdown."""
    logger.info(f"🛡️ {settings.APP_NAME} v{settings.APP_VERSION} starting up...")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info("Loading detection models...")

    # Initialize engines (lazy loading in production)
    app.state.analysis_reports = analysis_reports
    app.state.startup_time = datetime.utcnow()

    logger.info("✅ IPI-Shield ready to protect!")
    yield

    logger.info("🛑 IPI-Shield shutting down...")


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    description="Indirect Prompt Injection Defence Layer - Multimodal Security Middleware",
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
    debug=settings.DEBUG,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(analyze.router, tags=["Analysis"])
app.include_router(sanitize.router, tags=["Sanitisation"])
app.include_router(proxy.router, tags=["LLM Proxy"])
app.include_router(report.router, tags=["Reports"])


@app.get("/", response_class=HTMLResponse)
async def root():
    """Root endpoint - redirects to dashboard."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>IPI-Shield</title>
        <meta http-equiv="refresh" content="0; url=/dashboard" />
    </head>
    <body>
        <p>Redirecting to <a href="/dashboard">Dashboard</a>...</p>
    </body>
    </html>
    """


@app.get("/health")
async def health_check(request: Request):
    """Health check endpoint for monitoring."""
    uptime = None
    if hasattr(request.app.state, "startup_time"):
        uptime = (datetime.utcnow() - request.app.state.startup_time).total_seconds()

    return JSONResponse(
        {
            "status": "healthy",
            "service": "IPI-Shield",
            "version": "1.0.0",
            "uptime_seconds": uptime,
            "timestamp": datetime.utcnow().isoformat(),
            "components": {
                "ocr_engine": "operational",
                "payload_detector": "operational",
                "sanitizer": "operational",
                "safety_scorer": "operational",
            },
        }
    )


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    """Serve the main dashboard UI."""
    try:
        with open("frontend/index.html", "r") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(
            content="""
            <!DOCTYPE html>
            <html>
            <head><title>IPI-Shield Dashboard</title></head>
            <body>
                <h1>🛡️ IPI-Shield Dashboard</h1>
                <p>Dashboard files not found. Please ensure frontend files are in place.</p>
                <p><a href="/docs">API Documentation</a></p>
            </body>
            </html>
            """,
            status_code=200,
        )


@app.middleware("http")
async def add_request_id(request: Request, call_next: Callable) -> Response:
    """Add unique request ID to each request for tracing."""
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id

    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id

    return response


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=settings.HOST, port=settings.PORT)
