/**
 * mockGenerationService.js
 *
 * PURPOSE: Frontend-only mock that simulates the future FastAPI backend.
 * REPLACE: Swap `generateImage()` with a real fetch('/api/generate', ...) call
 *          once the backend API contract is finalised.
 *
 * ⚠  This file contains NO real API keys, NO real provider pricing, and
 *    NO measured energy or compute data. All resource figures are clearly
 *    labelled SIMULATED DEMO ESTIMATE — NOT MEASURED PROVIDER USAGE.
 */

// ─── Use-case catalogue ──────────────────────────────────────────────────────

export const USE_CASES = [
  {
    value: 'colouring_sheet',
    label: "Children's Colouring Sheet",
    description: 'Simple black-and-white outlines for printing and hand-colouring. Minimal detail needed.',
    recommendedTier: 'efficient',
    recommendReason: 'Outlines require no colour processing or fine detail — the efficient tier is well suited.',
  },
  {
    value: 'educational_flashcard',
    label: 'Educational Flashcard',
    description: 'Clear subject with readable text labels for classroom or digital use.',
    recommendedTier: 'efficient',
    recommendReason: 'Flashcards need clarity and legibility, not maximum resolution — efficient is appropriate.',
  },
  {
    value: 'social_media',
    label: 'Social Media Graphic',
    description: 'Eye-catching image for digital platforms. Moderate detail and colour.',
    recommendedTier: 'high_quality',
    recommendReason: 'Social media graphics benefit from richer colour and detail for visual impact.',
  },
  {
    value: 'detailed_poster',
    label: 'Detailed Poster or Printed Banner',
    description: 'Large-format print requiring high resolution, full colour, and fine detail.',
    recommendedTier: 'high_quality',
    recommendReason: 'Large-format print demands full detail and colour fidelity — high quality is required.',
  },
];

// ─── Quality / effort tiers ──────────────────────────────────────────────────

export const TIERS = [
  {
    id: 'efficient',
    label: 'Efficient',
    tagline: 'Match effort to purpose',
    description:
      'Uses generation settings appropriate for tasks that do not require maximum detail. ' +
      'Actual resource use depends on the provider\'s supported configuration options.',
    capabilities: [
      'Suitable for outlines, flashcards and simple graphics',
      'Lower complexity generation settings where supported',
      'Provider behaviour may vary — see estimate notes',
    ],
    icon: '⚡',
  },
  {
    id: 'high_quality',
    label: 'High Quality',
    tagline: 'Maximum detail and fidelity',
    description:
      'Targets the highest available quality settings. Used as the baseline for resource ' +
      'comparisons when provider data supports it.',
    capabilities: [
      'Intended for detailed graphics and print-quality output',
      'Full colour, maximum detail settings',
      'Serves as the maximum-quality comparison baseline',
    ],
    icon: '✦',
  },
];

// ─── Mock image placeholders (SVG data URIs) ─────────────────────────────────
// Stand-ins for real generated images. A real backend returns a URL.

const MOCK_IMAGES = {
  colouring_sheet: `data:image/svg+xml;utf8,${encodeURIComponent(`
    <svg xmlns="http://www.w3.org/2000/svg" width="512" height="512" viewBox="0 0 512 512">
      <rect width="512" height="512" fill="#f8f8f8"/>
      <circle cx="256" cy="195" r="90" fill="none" stroke="#1a1a2e" stroke-width="5"/>
      <ellipse cx="256" cy="340" rx="120" ry="80" fill="none" stroke="#1a1a2e" stroke-width="5"/>
      <line x1="200" y1="418" x2="178" y2="490" stroke="#1a1a2e" stroke-width="5" stroke-linecap="round"/>
      <line x1="312" y1="418" x2="334" y2="490" stroke="#1a1a2e" stroke-width="5" stroke-linecap="round"/>
      <circle cx="228" cy="185" r="10" fill="#1a1a2e"/>
      <circle cx="284" cy="185" r="10" fill="#1a1a2e"/>
      <path d="M228 228 Q256 252 284 228" fill="none" stroke="#1a1a2e" stroke-width="5" stroke-linecap="round"/>
      <text x="256" y="508" font-family="sans-serif" font-size="13" fill="#999" text-anchor="middle">Simulated outline — not AI-generated</text>
    </svg>
  `)}`,
  educational_flashcard: `data:image/svg+xml;utf8,${encodeURIComponent(`
    <svg xmlns="http://www.w3.org/2000/svg" width="512" height="512" viewBox="0 0 512 512">
      <rect width="512" height="512" fill="#0f172a"/>
      <rect x="48" y="48" width="416" height="300" rx="16" fill="#1e293b"/>
      <circle cx="256" cy="198" r="85" fill="#3b82f6" opacity="0.85"/>
      <text x="256" y="206" font-family="sans-serif" font-size="26" fill="white" font-weight="700" text-anchor="middle">Earth</text>
      <rect x="48" y="372" width="416" height="62" rx="10" fill="#1d4ed8"/>
      <text x="256" y="409" font-family="sans-serif" font-size="18" fill="white" text-anchor="middle">Third planet from the Sun</text>
      <text x="256" y="500" font-family="sans-serif" font-size="13" fill="#64748b" text-anchor="middle">Simulated flashcard — not AI-generated</text>
    </svg>
  `)}`,
  social_media: `data:image/svg+xml;utf8,${encodeURIComponent(`
    <svg xmlns="http://www.w3.org/2000/svg" width="512" height="512" viewBox="0 0 512 512">
      <defs>
        <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stop-color="#7c3aed"/>
          <stop offset="100%" stop-color="#06b6d4"/>
        </linearGradient>
      </defs>
      <rect width="512" height="512" fill="url(#bg)"/>
      <rect x="80" y="160" width="352" height="192" rx="20" fill="rgba(255,255,255,0.12)"/>
      <text x="256" y="248" font-family="sans-serif" font-size="32" fill="white" font-weight="800" text-anchor="middle">Smart Imaging</text>
      <text x="256" y="296" font-family="sans-serif" font-size="16" fill="rgba(255,255,255,0.8)" text-anchor="middle">Create Smarter. Generate Responsibly.</text>
      <text x="256" y="500" font-family="sans-serif" font-size="13" fill="rgba(255,255,255,0.4)" text-anchor="middle">Simulated graphic — not AI-generated</text>
    </svg>
  `)}`,
  detailed_poster: `data:image/svg+xml;utf8,${encodeURIComponent(`
    <svg xmlns="http://www.w3.org/2000/svg" width="512" height="512" viewBox="0 0 512 512">
      <defs>
        <linearGradient id="sky2" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stop-color="#0c0d1a"/>
          <stop offset="100%" stop-color="#1e1b4b"/>
        </linearGradient>
      </defs>
      <rect width="512" height="512" fill="url(#sky2)"/>
      <ellipse cx="256" cy="448" rx="310" ry="75" fill="#064e3b" opacity="0.85"/>
      <circle cx="256" cy="175" r="64" fill="#fbbf24" opacity="0.92"/>
      <circle cx="256" cy="175" r="80" fill="none" stroke="#fbbf24" stroke-width="2" opacity="0.35"/>
      <circle cx="256" cy="175" r="100" fill="none" stroke="#fbbf24" stroke-width="1" opacity="0.18"/>
      <polygon points="70,415 138,305 206,392" fill="#065f46"/>
      <polygon points="148,415 232,258 316,390" fill="#047857"/>
      <polygon points="308,415 382,295 456,415" fill="#065f46"/>
      <text x="256" y="507" font-family="sans-serif" font-size="13" fill="rgba(255,255,255,0.35)" text-anchor="middle">Simulated poster — not AI-generated</text>
    </svg>
  `)}`,
};

// ─── Decision explanations ────────────────────────────────────────────────────

const TIER_REASONS = {
  colouring_sheet: {
    efficient:    'Colouring sheets use line art only — colour rendering is not required. The efficient tier avoids unnecessary compute.',
    high_quality: 'High quality selected manually. For outlines, this likely uses more resources than the task requires.',
  },
  educational_flashcard: {
    efficient:    'Flashcards need readable text and a clear subject — not maximum resolution. Efficient is the appropriate choice.',
    high_quality: 'High quality selected manually. Useful if the flashcard will be printed at large scale.',
  },
  social_media: {
    efficient:    'Efficient selected manually. May be appropriate for low-resolution or thumbnail use cases.',
    high_quality: 'Social media graphics benefit from colour depth and sharpness — high quality is recommended for visual impact.',
  },
  detailed_poster: {
    efficient:    'Efficient selected manually. Large-format print typically requires more detail than this tier provides.',
    high_quality: 'Large-format print requires full detail and colour fidelity. High quality is the appropriate choice.',
  },
};

// ─── Resource estimate structure ──────────────────────────────────────────────
//
// All values below are SIMULATED DEMO ESTIMATES.
// They do NOT represent measured energy, measured compute time, or any provider's
// published pricing or capability data. They exist only to demonstrate the UI.
//
// Unit: arbitrary "compute units" (CU) — a placeholder label until the team
// agrees on and documents a real estimation method with the provider.

const RESOURCE_ESTIMATES = {
  efficient: {
    estimateValue: 12,        // Simulated demo value — not measured
    unit: 'compute units',
    provenance: 'simulated_demo',
    provenanceLabel: 'SIMULATED DEMO ESTIMATE — NOT MEASURED PROVIDER USAGE',
    basis: 'Placeholder value used for UI demonstration. Replace with provider-reported or team-verified data.',
  },
  high_quality: {
    estimateValue: 42,        // Simulated demo value — not measured
    unit: 'compute units',
    provenance: 'simulated_demo',
    provenanceLabel: 'SIMULATED DEMO ESTIMATE — NOT MEASURED PROVIDER USAGE',
    basis: 'Placeholder value used for UI demonstration. Replace with provider-reported or team-verified data.',
  },
};

// ─── Public API ───────────────────────────────────────────────────────────────

/**
 * generateImage(params) → Promise<GenerationResult>
 *
 * MOCK — replace this function body with a real fetch('/api/generate', {...})
 * once the FastAPI backend contract is agreed.
 *
 * @param {{ prompt: string, useCase: string, tier: string }} params
 */
export async function generateImage({ prompt, useCase, tier }) {
  await delay(1800 + Math.random() * 700);

  // ~10% simulated error rate for UX testing
  if (Math.random() < 0.10) {
    throw new MockGenerationError(
      'Simulated provider timeout. This is a demo error — press "Try again" to continue.'
    );
  }

  const useCaseMeta  = USE_CASES.find(u => u.value === useCase);
  const tierMeta     = TIERS.find(t => t.id === tier);
  const selectedEst  = RESOURCE_ESTIMATES[tier];
  const baselineEst  = RESOURCE_ESTIMATES['high_quality'];
  const isBaseline   = tier === 'high_quality';

  // Savings: only calculated when both values share the same unit and both are valid numbers
  const savingsValue  = (!isBaseline && selectedEst.unit === baselineEst.unit)
    ? baselineEst.estimateValue - selectedEst.estimateValue
    : null;
  const savingsPct    = (savingsValue !== null && baselineEst.estimateValue > 0)
    ? Math.round((savingsValue / baselineEst.estimateValue) * 100)
    : null;

  return {
    imageUrl:         MOCK_IMAGES[useCase],
    prompt,
    useCase,
    useCaseLabel:     useCaseMeta?.label ?? useCase,
    tier,
    tierLabel:        tierMeta?.label ?? tier,
    tierReason:       TIER_REASONS[useCase]?.[tier] ?? '',
    isSimulated:      true,
    resourceEstimate: {
      selected:  selectedEst,
      baseline:  baselineEst,
      savings:   savingsValue !== null ? { value: savingsValue, pct: savingsPct, unit: selectedEst.unit } : null,
    },
  };
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

function delay(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

export class MockGenerationError extends Error {
  constructor(message) {
    super(message);
    this.name = 'MockGenerationError';
  }
}
