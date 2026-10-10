/**
 * apiService.js
 *
 * Production API client connecting the React frontend to the FastAPI backend.
 * Uses real endpoints:
 * - /api/v1/infer-purpose (automatic purpose inference)
 * - /api/v1/generate (real image generation)
 * - /api/v1/history (real generation history)
 * - /api/v1/analytics (real aggregated metrics)
 * - /api/v1/tiers (centralized tier specifications)
 * - /health (service status and local WebUI connectivity)
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';

// ─── Educational Use Cases (Aligned with Purpose Inference Engine) ────────────

export const USE_CASES = [
  {
    value: 'coloring_sheet',
    label: "Children's colouring sheet",
    description: 'Black-and-white bold outlines on pure white background for printing and hand-colouring.',
    recommendedTier: 'eco',
    recommendReason: 'Eco recommended: Simple outlines and black-and-white output do not require maximum rendering effort (0.134 units, 86.6% savings).',
  },
  {
    value: 'classroom_handout',
    label: 'Worksheet / classroom handout',
    description: 'Illustrated curriculum exercises, technical boxes, and instructional activities.',
    recommendedTier: 'eco',
    recommendReason: 'Eco recommended: Classroom handouts are printed in volume where right-sized sampling passes are optimal (0.134 units, 86.6% savings).',
  },
  {
    value: 'flashcard',
    label: 'Educational flashcard',
    description: 'Crisp, centered subject with high contrast for vocabulary and alphabet cards.',
    recommendedTier: 'eco',
    recommendReason: 'Eco recommended: Flashcards prioritize readability over complex textures, conserving compute (0.134 units, 86.6% savings).',
  },
  {
    value: 'icon_thumbnail',
    label: 'Small icon / thumbnail',
    description: 'Compact icon, avatar, favicon, or UI badge with clean, readable shapes.',
    recommendedTier: 'eco',
    recommendReason: 'Eco recommended: Small icons and thumbnails focus on compact subjects requiring minimal sampling passes (0.134 units, 86.6% savings).',
  },
  {
    value: 'educational_infographic',
    label: 'Lesson diagram / educational infographic',
    description: 'Curriculum diagrams, anatomy charts, and structured lesson schematics.',
    recommendedTier: 'standard',
    recommendReason: 'Standard recommended: Lesson diagrams require clear structural composition and moderate detail (0.429 units, 57.1% savings).',
  },
  {
    value: 'presentation_slide',
    label: 'Classroom presentation slide',
    description: 'Engaging, clear visuals designed for digital projector and screen display.',
    recommendedTier: 'standard',
    recommendReason: 'Standard recommended: Screen-projected slides look crisp without high-density print rendering passes (0.429 units, 57.1% savings).',
  },
  {
    value: 'educational_poster',
    label: 'Educational poster',
    description: 'Rich classroom wall infographic and visual teaching aid with vibrant colors.',
    recommendedTier: 'standard',
    recommendReason: 'Standard recommended: Balances vibrant classroom color gamut with moderate resource usage (0.429 units, 57.1% savings).',
  },
  {
    value: 'large_format_banner',
    label: 'Large-format printed banner',
    description: 'High-visibility auditorium banner, science fair display, or hallway exhibition.',
    recommendedTier: 'high',
    recommendReason: 'High recommended: The intended large print use and detail requirements justify greater rendering effort (1.000 unit, 0% savings).',
  },
  {
    value: 'detailed_illustration',
    label: 'Detailed illustration',
    description: 'Intricate visual artwork or publication-grade illustration with fine detail.',
    recommendedTier: 'high',
    recommendReason: 'High recommended: Complex texture synthesis and intricate detail justify maximum supported parameters (1.000 unit, 0% savings).',
  },
];

// ─── Real Quality Tiers (Aligned with Section 5 Specification) ────────────────

export const TIERS = [
  {
    id: 'eco',
    label: 'Eco',
    tagline: '0.134 Units • 86.6% Savings',
    description: 'Right-sized 384x384 at 10 sampling steps. Optimal for colouring sheets, flashcards, and classroom handouts.',
    width: 384,
    height: 384,
    steps: 10,
    relativeUnits: 0.134,
    savingsPercent: 86.6,
    capabilities: [
      '384x384 right-sized resolution',
      '10 sampling steps (Euler a)',
      '1,474,560 compute-work units',
      '86.6% compute-work savings vs High',
      'Best for Colouring Sheets & Handouts',
    ],
    icon: '🌱',
  },
  {
    id: 'standard',
    label: 'Standard',
    tagline: '0.429 Units • 57.1% Savings',
    description: 'Balanced 512x512 at 18 sampling steps. Optimal for classroom posters, lesson diagrams, and presentation slides.',
    width: 512,
    height: 512,
    steps: 18,
    relativeUnits: 0.429,
    savingsPercent: 57.1,
    capabilities: [
      '512x512 balanced resolution',
      '18 sampling steps (Euler a)',
      '4,718,592 compute-work units',
      '57.1% compute-work savings vs High',
      'Best for Educational Posters & Diagrams',
    ],
    icon: '⚡',
  },
  {
    id: 'high',
    label: 'High',
    tagline: '1.000 Unit • Baseline Reference',
    description: 'Maximum supported 512x768 at 28 sampling steps. Reserved for printed exhibition banners and intricate illustrations.',
    width: 512,
    height: 768,
    steps: 28,
    relativeUnits: 1.0,
    savingsPercent: 0,
    capabilities: [
      '512x768 large-format resolution',
      '28 sampling steps (Euler a)',
      '11,010,048 compute-work units',
      'Reference High configuration (0% savings)',
      'Reserved for Large Printed Banners',
    ],
    icon: '✦',
  },
];

// ─── Custom API Error ────────────────────────────────────────────────────────

export class ApiError extends Error {
  constructor({ message, status, title, advice, detail }) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.title = title || 'Generation Error';
    this.advice = advice || null;
    this.detail = detail || message;
  }
}

// ─── Health Check ────────────────────────────────────────────────────────────

export async function fetchHealth() {
  try {
    const res = await fetch(`${API_BASE_URL}/health`);
    if (!res.ok) {
      throw new Error(`Health check returned HTTP ${res.status}`);
    }
    return await res.json();
  } catch (err) {
    return {
      status: 'offline',
      active_provider: 'unavailable',
      webui_reachable: false,
      api_enabled: false,
      error: err.message,
    };
  }
}

// ─── Automatic Purpose Inference ─────────────────────────────────────────────

export async function inferPurposeApi(prompt) {
  if (!prompt || !prompt.trim()) {
    return {
      purpose: "Awaiting prompt description",
      purpose_key: "general_purpose",
      recommended_tier: "standard",
      reason: "Please enter a prompt description to automatically infer purpose and recommend compute effort.",
      confidence: "low",
      is_ambiguous: true,
      default_parameters: { width: 512, height: 512, steps: 18 },
    };
  }

  try {
    const res = await fetch(`${API_BASE_URL}/api/v1/infer-purpose`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ prompt: prompt.trim() }),
    });
    if (!res.ok) {
      throw new Error(`Inference returned HTTP ${res.status}`);
    }
    return await res.json();
  } catch {
    // Graceful fallback to client-side heuristics if backend is momentarily offline
    const p = prompt.toLowerCase();
    if (p.includes('color') || p.includes('colour') || p.includes('outline') || p.includes('worksheet') || p.includes('flashcard')) {
      return {
        purpose: "Children's colouring sheet",
        purpose_key: "coloring_sheet",
        recommended_tier: "eco",
        reason: "Simple outlines and black-and-white output do not require maximum rendering effort.",
        confidence: "moderate",
        is_ambiguous: false,
        default_parameters: { width: 384, height: 384, steps: 10 },
      };
    }
    if (p.includes('icon') || p.includes('thumbnail') || p.includes('avatar') || p.includes('favicon') || p.includes('badge')) {
      if (!p.includes('banner') && !p.includes('print') && !p.includes('high-res') && !p.includes('large')) {
        return {
          purpose: "Small icon / thumbnail",
          purpose_key: "icon_thumbnail",
          recommended_tier: "eco",
          reason: "Small icons and thumbnails focus on compact subjects that do not require high resolution or heavy sampling passes.",
          confidence: "moderate",
          is_ambiguous: false,
          default_parameters: { width: 384, height: 384, steps: 10 },
        };
      }
    }
    if (p.includes('banner') || p.includes('large') || p.includes('detailed')) {
      return {
        purpose: "Large-format printed banner",
        purpose_key: "large_format_banner",
        recommended_tier: "high",
        reason: "The intended print use and detail requirements justify greater rendering effort.",
        confidence: "moderate",
        is_ambiguous: false,
        default_parameters: { width: 512, height: 768, steps: 28 },
      };
    }
    return {
      purpose: "Educational poster",
      purpose_key: "educational_poster",
      recommended_tier: "standard",
      reason: "Balanced composition and moderate detail without automatically using expensive settings.",
      confidence: "moderate",
      is_ambiguous: true,
      default_parameters: { width: 512, height: 512, steps: 18 },
    };
  }
}

// ─── Image Generation Request ─────────────────────────────────────────────────

export async function generateImageApi({
  prompt,
  intended_use,
  quality_tier = 'standard',
  negative_prompt = '',
  color_preference = 'auto',
  mode = 'optimized',
}) {
  const payload = {
    prompt: prompt.trim(),
    intended_use,
    quality_tier,
    negative_prompt: negative_prompt.trim(),
    color_preference,
    mode,
  };

  let response;
  try {
    response = await fetch(`${API_BASE_URL}/api/v1/generate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    });
  } catch (networkErr) {
    throw new ApiError({
      title: 'Backend Unreachable',
      status: 0,
      message: `Could not connect to FastAPI backend at ${API_BASE_URL}.`,
      advice: 'Ensure the backend server is running: .venv\\Scripts\\uvicorn backend.app.main:app --port 8000',
      detail: networkErr.message,
    });
  }

  if (!response.ok) {
    let errorJson = null;
    let rawText = '';
    try {
      errorJson = await response.json();
    } catch {
      rawText = await response.text().catch(() => '');
    }

    const detailMsg = errorJson?.detail || errorJson?.message || rawText || `HTTP ${response.status}`;

    const lowerDetail = typeof detailMsg === 'string' ? detailMsg.toLowerCase() : '';

    if (response.status === 503) {
      let title = 'Local Generator Unavailable (HTTP 503)';
      let advice = 'Ensure AUTOMATIC1111 is running with --api enabled in webui-user.bat.';

      if (lowerDetail.includes('unreachable') || lowerDetail.includes('connection error')) {
        title = 'Local WebUI Offline (HTTP 503)';
        advice = 'AUTOMATIC1111 is stopped or unreachable at http://127.0.0.1:7860. Start it via webui-user.bat.';
      } else if (lowerDetail.includes('api is disabled') || lowerDetail.includes('--api')) {
        title = 'REST API Disabled (HTTP 503)';
        advice = 'AUTOMATIC1111 is running, but --api was missing at startup. Edit webui-user.bat to include --api in COMMANDLINE_ARGS and restart the WebUI.';
      } else if (lowerDetail.includes('checkpoint') || lowerDetail.includes('model')) {
        title = 'Model Checkpoint Not Found (HTTP 503)';
        advice = 'No Stable Diffusion checkpoint (.safetensors) is loaded. Place a model file in models/Stable-diffusion and restart.';
      }

      throw new ApiError({
        title,
        status: 503,
        message: detailMsg,
        advice,
        detail: detailMsg,
      });
    }

    if (response.status === 504) {
      throw new ApiError({
        title: 'Generation Timed Out (HTTP 504)',
        status: 504,
        message: detailMsg,
        advice: 'The generation request exceeded the configured time limit. Try a lower-resource tier (Eco: 384x384, 10 steps) or check system load.',
        detail: detailMsg,
      });
    }

    if (response.status === 502) {
      throw new ApiError({
        title: 'Invalid Provider Image Response (HTTP 502)',
        status: 502,
        message: detailMsg,
        advice: 'The local provider did not return valid image data. Check WebUI console logs.',
        detail: detailMsg,
      });
    }

    if ((response.status === 500 || response.status === 503) && (lowerDetail.includes('memory') || lowerDetail.includes('cuda') || lowerDetail.includes('vram'))) {
      throw new ApiError({
        title: 'GPU Out of Memory (HTTP 500)',
        status: 500,
        message: detailMsg,
        advice:
          'Your RTX 2050 has 4 GB VRAM. Choose Eco (384x384) or Standard (512x512) tier, and ensure --medvram is in webui-user.bat.',
        detail: detailMsg,
      });
    }

    throw new ApiError({
      title: `Generation Error (HTTP ${response.status})`,
      status: response.status,
      message: typeof detailMsg === 'string' ? detailMsg : JSON.stringify(detailMsg),
      advice: 'Check the backend logs for additional troubleshooting information.',
      detail: detailMsg,
    });
  }

  const data = await response.json();

  if (!data.image || !data.image.url) {
    throw new ApiError({
      title: 'Malformed Response',
      status: 500,
      message: 'Backend returned success but image data was missing.',
      advice: 'Verify backend response conforms to ImageGenerationResponse schema.',
    });
  }

  return data;
}

// ─── Real Generation History ─────────────────────────────────────────────────

export async function fetchHistoryApi(limit = 50) {
  try {
    const res = await fetch(`${API_BASE_URL}/api/v1/history?limit=${limit}`);
    if (!res.ok) {
      throw new Error(`Failed to load history (HTTP ${res.status})`);
    }
    return await res.json();
  } catch {
    return [];
  }
}

export async function clearHistoryApi() {
  const res = await fetch(`${API_BASE_URL}/api/v1/history`, { method: 'DELETE' });
  if (!res.ok) {
    throw new Error(`Failed to clear history (HTTP ${res.status})`);
  }
  return await res.json();
}

// ─── Real Analytics ──────────────────────────────────────────────────────────

export async function fetchAnalyticsApi() {
  try {
    const res = await fetch(`${API_BASE_URL}/api/v1/analytics`);
    if (!res.ok) {
      throw new Error(`Failed to load analytics (HTTP ${res.status})`);
    }
    return await res.json();
  } catch {
    return {
      total_generations: 0,
      eco_count: 0,
      standard_count: 0,
      high_count: 0,
      overridden_count: 0,
      total_compute_units: 0.0,
      baseline_units: 0.0,
      units_saved: 0.0,
      overall_savings_percent: 0.0,
      avg_elapsed_seconds: 0.0,
      is_empty: true,
    };
  }
}
