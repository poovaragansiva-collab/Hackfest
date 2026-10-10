# API Contract Specification

This document defines the HTTP REST contract between the **React Frontend (Member 2)** and the **FastAPI Backend (Member 1)**.

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
Submits a prompt together with educational purpose and optional constraints. The purpose-aware decision engine calculates the optimal generation configuration, explains its rationale, invokes the provider adapter, and returns the result with resource metrics.

### Request Body (`application/json`)
```json
{
  "prompt": "An outline of an elephant in the savanna for young kids to color",
  "intended_use": "coloring_worksheet",
  "color_preference": "black_and_white",
  "detail_level": "low",
  "target_medium": "standard_print",
  "aspect_ratio": "1:1",
  "mode": "optimized"
}
```

#### Field Specifications
| Field | Type | Required | Allowed Values / Description |
|---|---|---|---|
| `prompt` | `string` | **Yes** | 3 to 1000 characters. Descriptive text of the desired image. |
| `intended_use` | `string` | **Yes** | `coloring_worksheet`, `flashcard`, `classroom_handout`, `presentation_slide`, `annual_report_poster`, `hallway_banner` |
| `color_preference` | `string` | No | `black_and_white`, `line_art`, `limited_color`, `full_color`, `auto` (Default: `auto`) |
| `detail_level` | `string` | No | `minimal`, `standard`, `high`, `ultra` (Default: `standard`) |
| `target_medium` | `string` | No | `screen_only`, `standard_print`, `high_resolution_print` (Default: `standard_print`) |
| `aspect_ratio` | `string` | No | `1:1`, `4:3`, `3:4`, `16:9`, `9:16` (Default: `1:1`) |
| `mode` | `string` | No | `optimized` (resource-aware) or `baseline` (naive unoptimized default) (Default: `optimized`) |

---

### Successful Response (`200 OK`)
```json
{
  "job_id": "gen_8f29e1a4",
  "status": "success",
  "image": {
    "url": "data:image/svg+xml;base64,...",
    "format": "svg",
    "width": 1024,
    "height": 1024
  },
  "applied_configuration": {
    "model": "dev-mock-fast",
    "quality_tier": "standard",
    "effective_resolution": "1024x1024",
    "steps": 15,
    "color_mode": "monochrome_line_art",
    "prompt_refinement": "An outline of an elephant in the savanna, clean coloring sheet, thick black vector outlines, zero shading, pure white background"
  },
  "decision_rationale": {
    "summary": "Downscaled quality tier and adjusted prompt for coloring outline.",
    "purpose_identified": "coloring_worksheet",
    "reasons": [
      "Coloring worksheets do not benefit from HD texture diffusion or high sampling steps.",
      "Optimized prompt to strict black outline style, preventing wasted GPU rendering on color saturation and shadows.",
      "Resolution standard 1024x1024 provides crisp print quality without large-model compute cost."
    ]
  },
  "resource_metrics": {
    "estimated_cost_usd": 0.016,
    "baseline_cost_usd": 0.080,
    "cost_reduction_percent": 80.0,
    "pricing_source": "Verified OpenAI DALL-E Standard (1024x1024) vs HD (1024x1792) baseline",
    "latency_seconds": 1.2
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
