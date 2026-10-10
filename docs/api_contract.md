# API Contract Specification

This document defines the HTTP REST contract between the **React Frontend (Member 2)** and the **FastAPI Backend (Member 1)**.

---

## Central Workflow
The API implements the required resource-aware lifecycle:
```text
User Request (Prompt + Purpose)
  │
  ▼
Purpose-Aware Decision Engine
  │
  ▼
Generation Configuration (Tier: Standard vs. HD, Resolution, Steps, Prompt Directives)
  │
  ▼
Resource Comparison (Optimized Cost Estimate vs. Maximum Baseline)
  │
  ▼
Replaceable Provider Adapter (Dev Mock / Real Provider)
  │
  ▼
Final Output (Image Data + Human-Readable Rationale + Auditable Cost Metrics)
```

---

## Base URL
`/api/v1`

---

## 1. Health Check

### `GET /health`
Verifies backend service availability and active provider configuration.

**Response `200 OK`**:
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "active_provider": "mock",
  "timestamp": "2026-10-10T09:15:00Z"
}
```

---

## 2. Image Generation

### `POST /api/v1/generate`
Submits a prompt together with educational purpose and optional constraints. The purpose-aware decision engine calculates the optimal generation configuration, explains its rationale, invokes the provider adapter, and returns the result with resource comparison metrics.

### Request Body (`application/json`)
```json
{
  "prompt": "An outline of an elephant in the savanna for young kids to color",
  "intended_use": "coloring_worksheet",
  "color_preference": "black_and_white",
  "detail_level": "minimal",
  "target_medium": "standard_print",
  "aspect_ratio": "1:1",
  "mode": "optimized"
}
```

#### Field Specifications
| Field | Type | Required | Allowed Values / Description |
|---|---|---|---|
| `prompt` | `string` | **Yes** | 3 to 1000 characters. Descriptive text of the desired image. |
| `intended_use` | `string` | **Yes** | `coloring_worksheet`, `flashcard`, `classroom_handout`, `presentation_slide`, `annual_report_poster`, `hallway_banner`. *(Enforces: "Ask the user what the image is intended for")* |
| `color_preference` | `string` | No | `black_and_white`, `line_art`, `limited_color`, `full_color`, `auto` (Default: `auto`) |
| `detail_level` | `string` | No | `minimal`, `standard`, `high`, `ultra` (Default: `standard`) |
| `target_medium` | `string` | No | `screen_only`, `standard_print`, `high_resolution_print` (Default: `standard_print`) |
| `aspect_ratio` | `string` | No | `1:1`, `4:3`, `3:4`, `16:9`, `9:16` (Default: `1:1`) |
| `mode` | `string` | No | `optimized` (resource-aware) or `baseline` (legacy unoptimized default) (Default: `optimized`) |

---

### Successful Response (`200 OK`)
```json
{
  "job_id": "gen_8f29e1a4",
  "status": "success",
  "image": {
    "url": "data:image/svg+xml;utf8,...",
    "format": "svg",
    "width": 1024,
    "height": 1024
  },
  "applied_configuration": {
    "model": "dall-e-3-standard",
    "quality_tier": "standard",
    "effective_resolution": "1024x1024",
    "steps": null,
    "color_mode": "monochrome_line_art",
    "prompt_refinement": "An outline of an elephant in the savanna for young kids to color, black and white coloring page style, clean bold line art, crisp outlines, zero shading, pure white background, no complex gradients"
  },
  "decision_rationale": {
    "summary": "Optimized configuration for coloring_worksheet (STANDARD, 1024x1024).",
    "purpose_identified": "coloring_worksheet",
    "reasons": [
      "Coloring worksheets require clear outline contours; HD micro-texture synthesis is unnecessary.",
      "Standard quality tier selected, reducing generation cost by 50% compared to baseline.",
      "Appended outline-specific directives to ensure printer-friendly black and white output."
    ]
  },
  "resource_metrics": {
    "estimated_cost_usd": 0.040,
    "baseline_cost_usd": 0.080,
    "cost_reduction_percent": 50.0,
    "unit": "USD",
    "provenance": "mock_illustrative",
    "pricing_basis": "OpenAI DALL-E 3 reference pricing tiers ($0.040 Standard 1024x1024 vs $0.080 HD 1024x1792)",
    "pricing_source": "OpenAI API Official Pricing Documentation (Reference Benchmark)",
    "is_live_billed": false,
    "calculation_explanation": "Illustrative reference calculation: STANDARD tier ($0.040/image) vs. Baseline HD tier ($0.080/image). Illustrative savings: $0.040/image (50.0% reduction). Pricing basis is derived from published OpenAI DALL-E 3 tiers. Active provider is 'mock' (no live financial billing).",
    "latency_seconds": 0.024
  }
}
```

---

### Error Responses

#### `422 Unprocessable Entity` (Validation Error)
```json
{
  "detail": [
    {
      "loc": ["body", "prompt"],
      "msg": "Prompt must be at least 3 characters long",
      "type": "value_error"
    }
  ]
}
```

#### `503 Service Unavailable` (Provider Failure / Missing Key)
```json
{
  "error_code": "PROVIDER_UNAVAILABLE",
  "message": "The upstream image generation provider is currently unreachable or credentials are not configured.",
  "fallback_available": true
}
```
