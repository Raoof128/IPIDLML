# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2024-12-05

### Added
- **Core Engine**:
  - Payload Detector with pattern matching, BERT stub, and embedding similarity.
  - Sanitizer engine with STRICT, BALANCED, and PERMISSIVE modes.
  - OCR Engine using Tesseract with simulated fallback.
  - HTML Extractor for hidden content and script analysis.
  - Image Analyzer for visual anomalies and adversarial patches.
  - Safety Scorer for trust scoring.
- **API**:
  - `/analyze` endpoint for multimodal content analysis.
  - `/sanitize` endpoint for payload neutralization.
  - `/proxy_llm` endpoint for protected LLM interaction.
  - `/report/{id}` endpoint for detailed safety reports.
- **Frontend**:
  - Dark-themed Dashboard for real-time monitoring and testing.
  - Visualizations for risk scores and detection breakdowns.
- **Documentation**:
  - Comprehensive `README.md`.
  - Detailed `THREAT_MODEL.md`.
  - `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md`.
- **DevOps**:
  - `Makefile` for build automation.
  - `pyproject.toml` for dependency management.
  - `Dockerfile` and `docker-compose.yml` for containerization.

### Security
- Implemented ISO 42001 and NIST AI RMF compliance mapping.
- Added audit logging for all proxy requests.
- Integrated input validation and sanitization pipelines.
