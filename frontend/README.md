# Frontend Workspace (Member 2)

This directory is reserved for **Member 2** to implement the React frontend application.

---

## 1. Official Core Requirements to Deliver in UI
1. **Ask what the image is intended for**:
   - Provide an educational purpose selector (`coloring_worksheet`, `flashcard`, `classroom_handout`, `presentation_slide`, `annual_report_poster`, `hallway_banner`).
2. **Match computational effort to purpose**:
   - Allow user to submit, letting the Decision Engine determine appropriate settings automatically.
3. **Reflect Quality Tiers**:
   - Display the applied quality tier (`Standard` vs. `HD`) returned in `applied_configuration.quality_tier`.
4. **Resource Estimate & Savings Comparison**:
   - Prominently display a comparison widget showing:
     - Optimized estimated cost (e.g. `$0.040`)
     - Maximum legacy baseline cost (e.g. `$0.080`)
     - Cost savings percentage (e.g. `50.0% reduction`)
     - Decision rationale reasons (`decision_rationale.reasons`)

---

## 2. Central UI Workflow
```text
User Form (Prompt Input + Purpose Dropdown + Mode Toggle)
  │
  ▼
Submit (POST /api/v1/generate)
  │
  ▼
Comparison View (Generated Image + Rationale Card + Cost Savings Pill)
```

---

## 3. Integration Endpoints
The backend runs locally by default at `http://127.0.0.1:8000`.

- **Health Check**: `GET /health`
  - Verifies backend availability and active provider.
- **Image Generation**: `POST /api/v1/generate`
  - Submits prompt, educational purpose, and optional constraints.
  - Returns generated image data URL (`image.url`), applied configuration, human-readable rationale, and quantified resource savings.

---

## 4. API Contract & Roadmap References
- **Full API Schema**: [`docs/api_contract.md`](file:///d:/HACKFEST_!/docs/api_contract.md)
- **Master Project Roadmap**: [`docs/NOTION_ROADMAP.md`](file:///d:/HACKFEST_!/docs/NOTION_ROADMAP.md)

---

## 5. CORS Configuration
The backend is pre-configured to allow CORS requests from:
- `http://localhost:3000`
- `http://localhost:5173`
