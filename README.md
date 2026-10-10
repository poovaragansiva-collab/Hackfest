# Hackfest — Sree Sakthi Hack Fest
# Resource-Aware Image Generation (Hack Fest — PS 1)

## Problem Overview
A district education office uses AI image generation for worksheets, flashcards, and posters across 300 schools. The cloud bill surged because simple black-and-white coloring outlines were generated with the same high-resource configurations as full-color posters.

This system introduces a **purpose-aware decision engine** that captures what an image is for, chooses justifiable generation settings based on verified provider pricing models, explains the trade-offs, and reports accurate cost/resource impacts.

## Architecture

```text
React Frontend (Member 2)
        │
        ▼ (HTTP REST / JSON)
FastAPI Backend (Member 1)
        ├── Request Validation (Pydantic)
        ├── Purpose-Aware Decision Engine
        └── Provider Adapter Layer
                ├── Dev Mock Provider (Offline / Testing)
                └── Real Provider Adapter (e.g., OpenAI / Stability - Member 3)
```

## Team Responsibilities
- **Member 1 (Lead & Backend):** Architecture, FastAPI backend, API contracts, Decision Engine, integration, test suite.
- **Member 2 (Frontend):** React frontend, form UX, rationale display, comparison view.
- **Member 3 (Provider Research):** Image generation provider research, actual cost/capability mapping, adapter integration.
- **Member 4 (Testing & Evidence):** Baseline vs. Resource-Aware benchmark testing, cost savings verification, evaluation evidence.

## Directory Structure
- `backend/`: FastAPI application, decision engine, schemas, provider adapters, tests.
- `frontend/`: React application (scaffolded by Member 2).
- `docs/`: API contracts, provider pricing evidence, evaluation rubrics.
