# Resource-Aware Image Generation (Hack Fest — PS 1)

## 1. Problem Statement & Revealed Hints

### The District Scenario
A district education office provides an AI image-generation tool to create visual aids (worksheets, flashcards, posters) across **300 schools**. Within one month, its cloud bill tripled. 

An audit revealed that the tool treated every request identically: simple black-and-white coloring outlines for primary school children were generated using the exact same expensive, high-resource settings (`dall-e-3-hd` large-format at $0.080–$0.120/image) as full-color annual report posters.

### Official Hints
1. **Hint 1:** *“The tool is not doing anything wrong. It simply never asks what the picture is for.”*
2. **Hint 2:** *“A colouring sheet for a seven-year-old does not need the same effort as a printed banner. Who decides how much effort a picture is worth, and does the person asking for it ever see the difference?”*

---

## 2. Core Requirements & Alignment

| Requirement | Implementation Details | Status |
|---|---|---|
| **1. Ask user for purpose** | Compulsory `intended_use` field in API (`coloring_worksheet`, `flashcard`, etc.). | **Implemented** |
| **2. Match computational effort to purpose** | Deterministic Decision Engine automatically selects quality tier, resolution, and prompt constraints. | **Implemented** |
| **3. At least two working quality tiers** | `standard` (1024x1024, fast sampling, 50% lower cost) and `hd` (1024x1792, rich fidelity). | **Implemented** |
| **4. Show resource estimate & savings vs. baseline** | Detailed `resource_metrics` comparing optimized cost to legacy baseline ($0.080) with transparent calculation explanation. | **Implemented** |

---

## 3. Central System Workflow

```text
User Request (Prompt + Intended Purpose)
        │
        ▼
Purpose-Aware Decision Engine
        │
        ▼
Generation Configuration (Tier: Standard vs HD, Resolution, Steps, Prompt Directives)
        │
        ▼
Resource Comparison (Optimized Cost Estimate vs Maximum Baseline)
        │
        ▼
Replaceable Provider Adapter (Dev Mock / Real Provider API)
        │
        ▼
Final Output (Image Data + Human-Readable Rationale + Auditable Cost Savings)
```

---

## 4. Current Status: Implemented vs. Planned

### Implemented Features
- **Deterministic Purpose-Aware Decision Engine (`decision_engine.py`)**: Maps educational intent to appropriate quality tiers and prints clear, non-technical rationales.
- **Two Quality Tiers (`Standard` & `HD`)**: Operating at $0.040 and $0.080 based on official published cloud pricing.
- **Replaceable Provider Architecture (`base.py`, `mock_provider.py`)**: Decoupled interface so real provider adapters (OpenAI / Stability) can be plugged in without changing decision logic.
- **Offline Dev Mock**: Generates dynamic, responsive SVGs styled specifically according to the chosen purpose (line-art outlines for coloring vs full-gradient banners).
- **Transparent Cost & Baseline Calculation**: Compares against unoptimized legacy baseline with zero fabricated energy/carbon claims.
- **Automated Test Suite**: 9 unit and integration tests passing (`pytest`).

### Planned Features
- **React Frontend UI (Member 2)**: Visual form with purpose selector and live resource savings card.
- **Real Provider Integration (Member 3)**: Pending provider API key availability.
- **District 300-School Evaluation (Member 4)**: Simulation charts demonstrating $2,280/year savings.

---

## 5. Master Roadmap & Team Documentation
- **Master Notion Roadmap**: [`docs/NOTION_ROADMAP.md`](file:///d:/HACKFEST_!/docs/NOTION_ROADMAP.md)
- **API Contract Specification**: [`docs/api_contract.md`](file:///d:/HACKFEST_!/docs/api_contract.md)
- **Frontend Workspace Guide**: [`frontend/README.md`](file:///d:/HACKFEST_!/frontend/README.md)
- **Provider Research Template**: [`docs/provider_research_template.md`](file:///d:/HACKFEST_!/docs/provider_research_template.md)
- **Evaluation & Evidence Guide**: [`docs/evaluation_guide.md`](file:///d:/HACKFEST_!/docs/evaluation_guide.md)

---

## 6. Setup and Run Commands

### Prerequisites
- Python 3.12+
- Git

### Backend Setup
1. **Activate virtual environment**:
   ```powershell
   backend\venv\Scripts\Activate.ps1
   ```
2. **Install dependencies**:
   ```powershell
   pip install -r backend/requirements.txt
   ```
3. **Run local development server**:
   ```powershell
   uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
   ```
4. **Run test suite**:
   ```powershell
   backend/venv/Scripts/pytest -v
   ```

---

## 7. Interactive API Documentation
When running locally:
- **Swagger UI**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)
- **Health Check**: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

---

## 8. Team Assignments & Integration
- **Member 1 (Backend, Architecture, Integration & Lead)**: Decision Engine, FastAPI service, schema governance, test suite.
- **Member 2 (React Frontend)**: User interface, purpose selector, baseline vs optimized comparison widget.
- **Member 3 (Provider Research)**: Pricing verification, provider adapter integration.
- **Member 4 (Testing, Evaluation & Evidence)**: District 300-school ROI simulation and benchmark evidence.
