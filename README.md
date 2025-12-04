# 🛡️ IPI-Shield: Indirect Prompt Injection Defence Layer

**Enterprise-Grade Multimodal Defence Against Indirect Prompt Injection Attacks**

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 🎯 Overview

IPI-Shield is a comprehensive middleware solution designed to detect, analyze, and neutralize **indirect prompt injection attacks** before they reach your LLM systems. It operates as a security proxy layer, inspecting text, images, PDFs, and HTML content for malicious payloads.

## 🚀 Key Features

### 🧠 Advanced Detection Engine
*   **Hybrid Analysis**: Combines regex pattern matching, statistical anomaly detection, and semantic analysis.
*   **Deep Learning Integration**:
    *   **Payload Detection**: Uses `DistilBERT` (fine-tuned on SST-2) to detect malicious intent and aggressive phrasing.
    *   **Semantic Search**: Uses `SentenceTransformers` (`all-MiniLM-L6-v2`) to identify semantic similarities with known jailbreak vectors.
*   **Robust Architecture**: Implements **Lazy Loading** and **Graceful Degradation**. The system automatically falls back to heuristic engines if ML libraries are missing or incompatible, ensuring high availability.

### 👁️ Multimodal Protection
*   **OCR Analysis**: Extracts text from images using **Tesseract OCR** (with simulation fallback) to detect embedded prompt injections.
*   **Visual Security**: Analyzes images for adversarial patches, steganography, and visual anomalies.
*   **HTML Sanitization**: Strips hidden `<div>` tags, malicious scripts, and CSS-based obfuscation.

### 🛡️ Defense-in-Depth
*   **Sanitization Layer**: Neutralizes detected threats using Strict, Balanced, or Permissive modes.
*   **Trust Scoring**: Calculates a composite safety score (0-100) based on multiple risk signals.
*   **Audit Logging**: Tracks every request, detection, and sanitization action for compliance (ISO 42001, NIST AI RMF).

## 🏗️ Architecture

┌─────────────────────────────────────────────────────────────────┐
│                        USER / APPLICATION                        │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                        IPI-SHIELD PROXY                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │   Input     │  │  Payload    │  │    Sanitisation         │  │
│  │  Extraction │─▶│  Detection  │─▶│       Engine            │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
│         │                │                      │                │
│         ▼                ▼                      ▼                │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │    OCR      │  │   BERT      │  │    Trust & Safety       │  │
│  │   Engine    │  │ Classifier  │  │       Scorer            │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    PROTECTED LLM ENDPOINT                        │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Tesseract OCR (optional, for image processing)

### Installation

```bash
# Clone the repository
git clone https://github.com/your-org/ipi-shield.git
cd ipi-shield

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start the server
python -m uvicorn backend.main:app --reload --port 8000
```

### Quick Test

```bash
# Health check
curl http://localhost:8000/health

# Analyze text
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"content": "Hello, how are you?", "content_type": "text"}'
```

---

## 📡 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/analyze` | POST | Analyze content for prompt injection |
| `/sanitize` | POST | Sanitise detected payloads |
| `/proxy_llm` | POST | Proxy request to LLM with protection |
| `/report/{id}` | GET | Retrieve analysis report |
| `/dashboard` | GET | Access dashboard UI |
| `/health` | GET | Health check endpoint |

---

## 🔧 Configuration

### Sanitisation Modes

| Mode | Behaviour |
|------|-----------|
| `STRICT` | Block and log all suspicious content |
| `BALANCED` | Scrub payloads, pass sanitised content |
| `PERMISSIVE` | Warn only, pass original content |

### Environment Variables

```bash
IPI_SHIELD_MODE=BALANCED
IPI_SHIELD_LOG_LEVEL=INFO
IPI_SHIELD_BERT_MODEL=distilbert-base-uncased
IPI_SHIELD_THRESHOLD=0.7
```

---

## 🔐 Threat Model

See [docs/THREAT_MODEL.md](docs/THREAT_MODEL.md) for comprehensive coverage of:
- Text-based injection patterns
- Image/OCR attack vectors
- HTML payload techniques
- Defence mechanisms

---

## 📊 Compliance Mapping

| Framework | Coverage |
|-----------|----------|
| ISO/IEC 42001 | AI Safety Controls |
| NIST AI RMF | Risk Management |
| SOCI Act (AU) | Critical Infrastructure |

---

## 🧪 Testing

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=backend --cov-report=html
```

---

## 📜 License

MIT License - See [LICENSE](LICENSE) for details.

---

## 🤝 Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) before submitting PRs.

---

## ⚠️ Disclaimer

This tool is designed for **defensive and educational purposes only**. It must not be used to craft, assist, or enable prompt injection attacks. The synthetic examples included are for testing detection capabilities only.
