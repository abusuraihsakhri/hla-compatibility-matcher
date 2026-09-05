# HLA Compatibility Matcher

> **Domain:** Clinical Decision Support & Biomedical Computing

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB.svg?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688.svg?logo=fastapi&logoColor=white)
![Audit Trail](https://img.shields.io/badge/Audit-HMAC--SHA256_Tamper--Evident-brightgreen.svg)
![Zero-PHI Guard](https://img.shields.io/badge/Guard-Zero--PHI_Outbound-blue.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg?logo=docker&logoColor=white)

</div>

---

## 📖 What It Does

HLA Compatibility Matcher is a clinical decision support tool for transplant pairing. It provides:

- **HLA allele lookup** with token overlap and substring scoring
- **Batch CSV processing** for high-throughput HLA matching
- **Multi-agent consensus system** with specialized workers for quality control, safety escalation, and protocol conformance
- **Zero-PHI outbound guard** protecting against accidental patient data leakage
- **Tamper-evident HMAC-SHA256 audit trail** for all operations
- **FastAPI REST API** for integration with clinical systems

---

## ⚙️ Key Capabilities & Algorithmic Modules

### 🔬 Analytical Functions

- **`lookup(query)`**: Single HLA allele lookup with token overlap + substring scoring. Returns top hits with confidence scores.
- **`process_csv(input, output)`**: Batch process CSV files with HLA matching. Automatically detects query column.
- **`build_parser()`**: CLI argument parser with `single` and `batch` subcommands.

### 🤖 Multi-Agent System

- **`InvariantQCWorker`**: Validates primary metric against reference limits
- **`SafetyEscalationWorker`**: Triggers on critical flags or secondary metric thresholds
- **`ProtocolConformanceWorker`**: Detects discordant status descriptors
- **`SystemSupervisor`**: Orchestrates workers and produces consensus dossiers

---

## 💻 Installation

### Local Development

```bash
# Clone the repository
git clone https://github.com/abusuraihsakhri/hla-compatibility-matcher.git
cd hla-compatibility-matcher

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env
# Edit .env to set your AUDIT_SECRET_KEY
```

---

## 🖥️ CLI Quickstart & Usage

### HLA Lookup Mode
```bash
# Single allele lookup
python hla_matcher.py single "A*02:01"

# Batch CSV processing
python hla_matcher.py batch --input sample.csv --output results.csv
```

### Full Supervisor Mode
```bash
# Run single task evaluation
python cli.py audit --task-id TASK-001 --primary 28.5 --secondary 14.2

# Batch process CSV records
python cli.py batch -i sample.csv -o results.csv

# Verify HMAC audit trail integrity
python cli.py verify-audit

# Launch FastAPI REST server
python cli.py serve --host 127.0.0.1 --port 8000
```

### Environment Configuration

| Variable | Description | Default |
|:---------|:------------|:--------|
| `AUDIT_SECRET_KEY` | HMAC-SHA256 key for audit trail (generate with `python -c "import secrets; print(secrets.token_hex(32))"`) | Auto-generated (ephemeral) |
| `MODEL_PROVIDER` | LLM provider (`mock`, `ollama`, `claude`, `openai`) | `mock` |

---

## 🛡️ Security & Enterprise Architecture

- **Zero-PHI Outbound Interceptor:** Active regex inspection blocking SSNs, MRNs, phone numbers, emails, and patient identifiers
- **Tamper-Evident HMAC-SHA256 Audit Trail:** Chained, cryptographically signed logs for every evaluation
- **Deterministic Mock LLM:** Safe default with no external dependencies
- **Input Validation:** Pydantic models with strict type checking

---

## 🧪 Testing & Verification

```bash
# Run full test suite
pytest -v

# Run with coverage
pytest -v --cov=agents --cov=hla_matcher --cov-report=html

# Execute high-throughput simulation benchmark
python simulator.py 1000
```

---

## 🐳 Container Deployment

```bash
# Build and run with Docker Compose
docker compose up --build

# Or manually
docker build -t hla-compatibility-matcher .
docker run -p 8000:8000 --env-file .env hla-compatibility-matcher
```

---

## 📁 Project Structure

```
hla-compatibility-matcher/
├── agents/                    # Multi-agent system
│   ├── __init__.py
│   ├── api.py                 # FastAPI REST endpoints
│   ├── base.py                # PHI guard, audit trail, security
│   ├── learning.py            # Bayesian calibration engine
│   ├── llm_factory.py         # LLM provider abstraction
│   ├── metrics.py             # Prometheus metrics collector
│   ├── models.py              # Pydantic data models
│   ├── streamer.py            # WebSocket telemetry broadcaster
│   ├── supervisor.py          # Multi-agent orchestrator
│   └── workers.py             # Specialized worker agents
├── tests/                     # Test suite
│   ├── test_hla_compatibility_matcher.py
│   ├── test_hla_matcher.py
│   └── test_enrichment.py
├── cli.py                     # Command-line interface
├── hla_matcher.py             # Core HLA matching engine
├── enrichment.py              # Domain enrichment engines
├── simulator.py               # High-throughput stress tester
├── web/                       # Operations console (static HTML)
├── requirements.txt           # Python dependencies
├── Dockerfile                 # Container definition
├── docker-compose.yml         # Container orchestration
├── .env.example               # Environment template
├── sample.csv                 # Sample input data
└── benchmark_dataset.json     # Golden test cases
```
