# Hackfest — Sree Sakthi Hack Fest
# Resource-Aware Image Generation (Hack Fest — PS 1)

## 1. Project Purpose & Problem Context
A district education office provides an AI image-generation tool to create classroom materials (worksheets, flashcards, posters) across **300 schools**. Within one month, its cloud bill tripled. 

An audit revealed that the tool treated every request identically: simple black-and-white coloring outlines for primary school children were generated using the exact same expensive, high-resource settings (`dall-e-3-hd` large-format at $0.080–$0.120/image) as full-color annual report posters.

**Core Insight:** 
> “The tool is not doing anything wrong. It simply never asks what the picture is for. A colouring sheet for a seven-year-old does not need the same effort as a printed banner.”

This system introduces a **Purpose-Aware Decision Engine** that captures educational intent, selects right-sized generation configurations backed by defensible provider pricing, explains the trade-offs in plain language, and reports auditable cost savings against an unoptimized baseline.

---

## 2. Current Project Status
- **Phase**: Backend Foundation with Development Mock.
- **Decision Engine**: Fully implemented and tested with deterministic purpose-to-resource mapping.
- **Provider Layer**: Abstract `BaseImageProvider` with offline `DevMockProvider` generating purpose-labeled responsive SVG previews without fake claims or phantom cloud charges.
- **Test Suite**: Automated `pytest` suite passing with 100% success rate across validation, purpose engine arithmetic, and endpoint integration.

---

## 3. Architecture Overview

```text
React Frontend (Member 2)
        │
        ▼ (HTTP REST / JSON)
FastAPI Backend (Member 1)
        ├── Request Validation (Pydantic models)
        ├── Purpose-Aware Decision Engine
        │       ├── Purpose profiles (worksheet, flashcard, poster, etc.)
        │       ├── Generation tiers (Standard vs. HD)
        │       └── Rationale generator & cost metrics
        └── Provider Adapter Layer
                ├── Dev Mock Provider (Offline testing)
                └── Real Provider Adapter (OpenAI / Stability - Member 3)
```

---

## 4. Project Directory Structure

```text
Hackfest/
├── .gitignore                          # Excludes secrets, venvs, node_modules, caches
├── .env.example                        # Template for environment configuration
├── README.md                           # Master project documentation
├── pytest.ini                          # Pytest configuration with root pythonpath
├── backend/
│   ├── requirements.txt                # Pinned backend dependencies
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                     # FastAPI application entry point
│   │   ├── config.py                   # Pydantic Settings & CORS configuration
│   │   ├── schemas/                    # Pydantic request/response schemas
│   │   │   ├── __init__.py
│   │   │   ├── request.py
│   │   │   └── response.py
│   │   ├── services/                   # Business logic
│   │   │   ├── __init__.py
│   │   │   └── decision_engine.py      # Purpose-aware decision logic & pricing model
│   │   └── providers/                  # Adapter interface & implementations
│   │       ├── __init__.py             # Provider factory
│   │       ├── base.py                 # Abstract BaseImageProvider
│   │       └── mock_provider.py        # Development mock provider (labeled SVGs)
│   └── tests/                          # Automated test suite
│       ├── test_health.py              # Health check endpoint test
│       ├── test_validation.py          # Input validation & error handling tests
│       ├── test_decision_engine.py     # Decision logic & pricing tests
│       └── test_generate_api.py        # Full endpoint integration tests
├── frontend/
│   └── README.md                       # Instructions and contract for Member 2
└── docs/
    ├── api_contract.md                 # REST API schema contract for frontend
    ├── provider_research_template.md   # Provider capabilities checklist for Member 3
    └── evaluation_guide.md             # Baseline vs. optimized evidence for Member 4
```

---

## 5. Setup and Run Commands

### Prerequisites
- Python 3.12+ installed.
- Git.

### Backend Setup
1. **Navigate to project root**:
   ```powershell
   cd D:\HACKFEST_!
   ```
2. **Create and activate virtual environment**:
   ```powershell
   python -m venv backend/venv
   # Windows PowerShell:
   backend\venv\Scripts\Activate.ps1
   ```
3. **Install dependencies**:
   ```powershell
   pip install -r backend/requirements.txt
   ```
4. **Configure environment**:
   ```powershell
   cp .env.example .env
   ```
5. **Run local development server**:
   ```powershell
   uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
   ```

---

## 6. API Documentation URLs
When the backend server is running locally:
- **Interactive Swagger UI**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc Documentation**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)
- **OpenAPI Schema**: [http://127.0.0.1:8000/openapi.json](http://127.0.0.1:8000/openapi.json)
- **Health Check Endpoint**: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

---

## 7. How to Run Tests
From the project root:
```powershell
backend/venv/Scripts/pytest -v
```

---

## 8. Team Responsibilities
- **Member 1 (Backend, Architecture, Integration & Lead)**:
  - Architecture governance, API contracts, FastAPI backend, Decision Engine, test suite, repository coordination.
- **Member 2 (React Frontend)**:
  - React user interface (`frontend/`), prompt submission, purpose selection, visual side-by-side comparison.
- **Member 3 (Provider Research & Adapter)**:
  - Research provider capabilities, pricing tables, rate limits, and implement real provider adapters.
- **Member 4 (Testing, Evaluation & Evidence)**:
  - Benchmark simulation across 300 schools, cost reduction verification, and evaluation documentation.
