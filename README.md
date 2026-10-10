# ResourceAware — Resource-Aware Image Generation

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg?logo=fastapi)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-19.2+-61DAFB.svg?logo=react)](https://react.dev)
[![Stable%20Diffusion](https://img.shields.io/badge/Stable%20Diffusion-AUTOMATIC1111-brightgreen.svg)](https://github.com/AUTOMATIC1111/stable-diffusion-webui)
[![Tests](https://img.shields.io/badge/Tests-93%20Passed-success.svg)](backend/tests)

**ResourceAware** transforms generative AI image workflows for educational institutions by matching inference compute effort directly to the intended purpose of each image.

---

## 1. Hackathon Scenario & Problem Statement

### The 300-School District Challenge
A district education office provides AI image generation to teachers across **300 schools** to create visual classroom materials (coloring sheets, flashcards, lesson diagrams, posters). Within a month, compute consumption tripled because the legacy generator treated every request identically: simple black-and-white outlines for 7-year-olds were generated with the exact same maximum compute settings as large auditorium banners.

### Core Hackathon Constraints
1. **Constraint 1 — Resource Transparency:**
   - Every generation displays its **actual elapsed duration** measured with a system monotonic timer (`time.perf_counter()`).
   - Resource estimates and relative savings are calculated against a declared **maximum High quality tier**.
   - The exact formula and parameters are visible to the user.
   - Measured metrics are strictly distinguished from algorithmic estimates.
   - Zero fabricated energy readings (no fake kWh, Joules, or invented wattage).
2. **Constraint 2 — Automatic Purpose Inference:**
   - The intended educational purpose and recommended quality tier are inferred automatically from the user's natural-language prompt.
   - A non-technical explanation is provided for the recommendation.
   - The user can inspect and manually override the tier before generation.
   - The final selected tier controls real image dimensions and sampling passes on the local generator.

---

## 2. System Architecture

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                       ResourceAware Web Application                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  React 19 Frontend (Vite, http://127.0.0.1:5173)                           │
│  ├── Live Purpose Inference & Tier Recommendation Hook                      │
│  ├── Quality Tier Selector (Eco / Standard / High) with Override Badge      │
│  ├── Transparent Parameter Preview Strip                                    │
│  ├── Real-time Generation Preview, Download & Side-by-Side Comparison       │
│  └── Telemetry Dashboard & 300 Schools District Simulation                  │
│                                      │                                      │
│                                HTTP POST/GET                                │
│                                      ▼                                      │
│  FastAPI Backend (Python 3.12, http://127.0.0.1:8000)                       │
│  ├── /api/v1/infer-purpose  : Deterministic rule-based purpose classifier   │
│  ├── /api/v1/tiers          : Centralized tier parameter specifications     │
│  ├── /api/v1/generate       : Concurrency-guarded image generation route    │
│  ├── /api/v1/outputs/{file} : Secure image file serving (traversal guarded) │
│  ├── /api/v1/history        : Real generation history (SQLite persistence)  │
│  ├── /api/v1/analytics      : Aggregated metrics & genuine empty states     │
│  └── Concurrency Guard      : asyncio.Lock() preventing GPU VRAM exhaustion │
│                                      │                                      │
│                                HTTP POST                                    │
│                                      ▼                                      │
│  Local Generator: AUTOMATIC1111 Stable Diffusion WebUI (Port 7860)           │
│  ├── Endpoint: POST /sdapi/v1/txt2img                                       │
│  ├── Model: Checkpoint (e.g. v1-5-pruned-emaonly.safetensors)               │
│  └── Hardware: NVIDIA RTX 2050 (4 GB VRAM) with --medvram                   │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Real Quality Tiers & Parameter Specifications

To prevent Out-Of-Memory (OOM) failures on 4 GB GPUs while ensuring noticeable quality differentiation, parameters are managed centrally:

| Tier | Width | Height | Sampling Steps | Batch Size | Compute-Work Units | Normalized Units | Savings vs High | Optimal Educational Use Case |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| **Eco** | 384 px | 384 px | 10 | 1 | 1,474,560 | **0.1339** | **86.6%** | Colouring sheets, flashcards, simple worksheets |
| **Standard** | 512 px | 512 px | 18 | 1 | 4,718,592 | **0.4286** | **57.1%** | Lesson diagrams, classroom posters, slides |
| **High** | 512 px | 768 px | 28 | 1 | 11,010,048 | **1.0000** | **0.0%** *(Reference)* | Large printed banners, auditorium displays |

*Note: All tiers use `Euler a` sampler and the active local SD checkpoint.*

---

## 4. Resource Estimation Methodology

### Transparent Compute-Work Proxy Formula
Because Stable Diffusion inference workload scales with pixel resolution and denoising passes, ResourceAware defines a transparent, reproducible algorithmic proxy:

$$\text{work\_units} = \text{width} \times \text{height} \times \text{sampling\_steps}$$

Against the declared reference High configuration ($512 \times 768 \times 28 = 11,010,048\text{ units}$):

$$\text{normalized\_resource\_units} = \frac{\text{work\_units}}{\text{reference\_high\_units}}$$

$$\text{savings\_percent} = 100 \times \left(1 - \frac{\text{work\_units}}{\text{reference\_high\_units}}\right)$$

### Strict Integrity Disclosure
- **Proxy Metric vs. Direct Energy:** These numbers represent **Estimated compute-work units**, not physical energy (Joules or kWh). Stable Diffusion inference does not scale perfectly linearly with pixels $\times$ steps, so this value is presented as an engineering proxy.
- **Measured Elapsed Time:** Displayed separately based on a monotonic system clock (`time.perf_counter()`).
- **No Mock Data:** Historical dashboards and session metrics reflect real executed generations stored in the local SQLite database (`backend/data/generations.db`). When no records exist, the UI shows a genuine empty state.

---

## 5. Automatic Purpose Inference Engine

The backend evaluates natural-language prompts using deterministic pattern-matching rules and confidence scoring without external API dependencies:

| Category | Typical Triggers | Inferred Purpose | Tier | Rationale |
|---|---|---|---|---|
| **Colouring Sheets** | `colouring sheet`, `coloring book`, `outline`, `black and white`, `line art`, `for 7-year-old` | Children's colouring sheet | **Eco** | Simple outlines and black-and-white output do not require maximum rendering effort. |
| **Worksheets** | `worksheet`, `handout`, `activity sheet`, `kindergarten activity` | Classroom worksheet | **Eco** | Classroom worksheets prioritize clear subject identification over fine detail. |
| **Flashcards** | `flashcard`, `vocabulary card`, `picture card` | Educational flashcard | **Eco** | Flashcard visual prompts need clean iconography rather than high-density rendering. |
| **Lesson Diagrams** | `diagram`, `infographic`, `flowchart`, `anatomy diagram` | Lesson diagram | **Standard** | Diagrams require balanced resolution and step count for legible structures. |
| **Posters** | `educational poster`, `wall chart`, `classroom poster`, `water cycle` | Educational poster | **Standard** | Posters need readable composition and moderate detail without maximum expensive settings. |
| **Printed Banners** | `banner`, `large print`, `school exhibition`, `auditorium backdrop`, `billboard` | Large-format printed banner | **High** | Large physical print formats justify high resolution and maximum sampling passes. |
| **Detailed Illustrations** | `highly detailed`, `intricate artwork`, `oil painting`, `masterpiece` | Detailed illustration | **High** | Fine artistic textures require deeper denoising steps. |
| **Ambiguous Prompts** | General text without educational context | General educational graphic | **Standard** | Conservative default ensuring acceptable quality without wasting resources. |

---

## 6. Local Setup & Execution Guide (Windows)

### Prerequisites
- Windows 10/11 64-bit
- NVIDIA GPU (RTX 2050 4 GB VRAM or higher) with CUDA drivers
- Python 3.12+ (installed in virtual environment `.venv`)
- Node.js 18+ and npm
- Local AUTOMATIC1111 Stable Diffusion WebUI

---

### Step 1: Launch Local AUTOMATIC1111 WebUI with `--api`
The WebUI must be launched with the `--api` flag so that ResourceAware can communicate with `POST /sdapi/v1/txt2img`.

1. Open your WebUI installation folder (e.g. `D:\stable-diffusion-webui-master`).
2. Open `webui-user.bat` in a text editor.
3. Update the `COMMANDLINE_ARGS` line:
   ```bat
   set COMMANDLINE_ARGS=--api --medvram --xformers
   ```
   *(Note: `--medvram` is critical for 4 GB GPUs like the RTX 2050 to prevent CUDA out-of-memory errors).*
4. Run `webui-user.bat`.
5. Verify in browser:
   - Root UI: [http://127.0.0.1:7860](http://127.0.0.1:7860)
   - API Docs: [http://127.0.0.1:7860/docs](http://127.0.0.1:7860/docs)
6. Keep this terminal window open.

---

### Step 2: Configure Environment
Copy `.env.example` to `.env` in the project root:

```ini
APP_ENV=development
APP_HOST=127.0.0.1
APP_PORT=8000
CORS_ORIGINS=http://localhost:3000,http://localhost:5173,http://127.0.0.1:5173

ACTIVE_PROVIDER=automatic1111
SD_WEBUI_URL=http://127.0.0.1:7860
SD_TIMEOUT_SECONDS=180
SD_DEFAULT_SAMPLER="Euler a"

DATABASE_PATH=backend/data/generations.db
```

---

### Step 3: Start FastAPI Backend
In a PowerShell terminal:
```powershell
d:\HACKFEST_!\.venv\Scripts\uvicorn.exe backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```
Verify health:
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/health"
```
Output:
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "active_provider": "automatic1111",
  "webui_reachable": true,
  "api_enabled": true,
  "loaded_model": "v1-5-pruned-emaonly.safetensors"
}
```

---

### Step 4: Start React Frontend
In a second PowerShell terminal:
```powershell
cd d:\HACKFEST_!\frontend
npm run dev
```
Open [http://127.0.0.1:5173](http://127.0.0.1:5173) in your browser.

---

## 7. Automated Test Suite

Run the full pytest suite:
```powershell
d:\HACKFEST_!\.venv\Scripts\pytest.exe -v
```

### Verified Test Areas
- **Purpose Inference (`test_purpose_inference.py`):** 9 acceptance tests verifying coloring sheets, flashcards, worksheets, diagrams, posters, banners, and ambiguity handling.
- **Phase 2 & Phase 3 Constraints (`test_phase2_phase3_constraints.py`):** 8 tests validating cost/compute display alongside savings vs High reference, calculation explanation disclosure, natural-language tier proposing, non-technical reasoning, and manual user override persistence.
- **Tier Configuration (`test_tier_configuration.py`):** Asserts Eco ($384\times384, 10$), Standard ($512\times512, 18$), and High ($512\times768, 28$) produce distinct API payloads.
- **Resource Estimation (`test_estimation.py`):** Verifies reference High normalization ($1.0$), High savings ($0\%$), Eco savings ($86.6\%$), and formula reproducibility.
- **AUTOMATIC1111 Provider Adapter (`test_automatic1111_provider.py` & `test_generate_api.py`):** Tests success response parsing, connection timeout handling, WebUI missing `--api` error detection, loopback SSRF guards, CUDA OOM recovery, and offline 503 error responses (zero silent fallback to mock data).
- **Controlled Output Artifacts & Storage (`test_storage.py`):** Verifies controlled output saving (`/api/v1/outputs/{job_id}.png`), secure file serving, path traversal protection, genuine SQLite persistence, and authentic empty states.
- **End-to-End Integration Flow (`test_integration_flow.py`):** Full pipeline test from prompt to API payload, response schema, and database persistence.

**Result: 93 passed, 1 skipped (live local WebUI smoke test safely skipped when WebUI is offline or started without `--api`).**

---

## 8. Hackathon Demonstration Scenario

Follow this 6-step walkthrough for a complete live demonstration:

1. **Test Prompt 1 (Colouring Sheet — Eco Recommendation):**
   - Enter prompt: `"Make a simple black-and-white colouring sheet of a butterfly for a seven-year-old."`
   - Observe live inference: Inferred Purpose = **Children's colouring sheet**, Recommended Tier = **Eco (0.134 units)**.
   - Click **Generate Image**.
   - Review results: Generated image displayed, actual elapsed time measured, compute-work units = **0.134 units** (saving **86.6%** vs High).
2. **User Override Demonstration:**
   - In the tier selector, manually click **High**.
   - Notice the visible **User Override** alert badge.
   - Parameter preview updates to $512 \times 768$, 28 steps (1.000 unit).
   - Generate again to show that user choice dictates real parameters.
3. **Test Prompt 2 (Educational Poster — Standard Recommendation):**
   - Enter prompt: `"Create an illustrated educational poster about the water cycle."`
   - Observe live inference: Inferred Purpose = **Educational poster**, Recommended Tier = **Standard (0.429 units, 57.1% savings)**.
   - Generate and verify $512 \times 512$ at 18 steps.
4. **Test Prompt 3 (Exhibition Banner — High Recommendation):**
   - Enter prompt: `"Create a highly detailed illustration for a large printed school exhibition banner."`
   - Observe live inference: Inferred Purpose = **Large-format printed banner**, Recommended Tier = **High (1.000 unit)**.
   - Rationale explains: *"The intended print use and detail requirements justify greater rendering effort."*
5. **Compare Real Measured Latency vs. Transparent Proxy Units:**
   - Open the **Expandable Formula & Assumptions** panel on the result card.
   - Review exact math: $\text{Width} \times \text{Height} \times \text{Steps} / 11,010,048$.
   - Note the strict distinction between measured seconds and calculated proxy units.
6. **Telemetry & District 300 Schools Projection:**
   - Click the **Resource Telemetry** navigation tab.
   - View genuine session metrics (counts, total units saved, average measured duration).
   - Inspect the interactive **300 Schools District Simulation**: by defaulting simple classroom requests to Eco (0.134) instead of naive High (1.000), 300 schools save over **70% of GPU compute load** every month.

---

## 9. Hardware Constraints & Troubleshooting

### Hardware Constraints (RTX 2050 4 GB VRAM)
- **Concurrency Serialization:** An asynchronous lock (`asyncio.Lock()`) in the backend provider queues concurrent requests to avoid GPU memory crashes.
- **Resolution Ceilings:** High tier is set to $512 \times 768$ at 28 steps. Higher resolutions like $1024 \times 1024$ without tiling cause CUDA Out-of-Memory on 4 GB cards.

### Troubleshooting Quick Reference

| Symptom | Cause | Solution |
|---|---|---|
| **HTTP 503: Connection Refused** | WebUI is not running on `127.0.0.1:7860`. | Run `webui-user.bat` and keep the terminal open. |
| **HTTP 503: WebUI is running without `--api`** | WebUI was started without the `--api` flag (returns 404 on `/sdapi/v1/*`). | Add `set COMMANDLINE_ARGS=--api --medvram` to `webui-user.bat` and restart WebUI. |
| **HTTP 500: CUDA Out of Memory** | GPU VRAM exhausted. | Ensure `--medvram` or `--lowvram` is in `COMMANDLINE_ARGS`, and select Eco or Standard tier. |
| **Frontend shows "Offline" badge** | FastAPI backend is not running on port 8000. | Run `uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload`. |
