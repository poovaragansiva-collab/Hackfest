# Frontend Workspace (Member 2)

This directory is reserved for **Member 2** to implement the React frontend application.

---

## Workspace Guidelines
- Member 2 should scaffold the React application in this directory (e.g. using Vite + React).
- Do not modify or overwrite backend files in `backend/` directly; integrate via the agreed HTTP REST endpoints below.

---

## Integration Endpoints
The backend runs locally by default at `http://127.0.0.1:8000`.

- **Health Check**: `GET /health`
  - Verifies backend availability and active provider.
- **Image Generation**: `POST /api/v1/generate`
  - Submits prompt, educational purpose, and optional style constraints.
  - Returns generated image data URL, applied configuration, human-readable rationale, and quantified resource savings.

---

## API Contract Reference
Please refer to the complete request/response schema specification, enum definitions, and example payloads in:
- [`docs/api_contract.md`](file:///d:/HACKFEST_!/docs/api_contract.md)

---

## CORS Configuration
The backend is pre-configured to allow CORS requests from:
- `http://localhost:3000`
- `http://localhost:5173`
