/**
 * resourceEstimation.js
 *
 * Transparent compute-work estimation model for ResourceAware.
 *
 * Model Definition:
 * - Algorithmic proxy for GPU inference load based on pixel dimensions and sampling passes.
 * - Reference High tier: 512 × 768 at 28 steps = 11,010,048 compute-work units (1.000 normalized reference).
 * - Standard tier: 512 × 512 at 18 steps = 4,718,592 compute-work units (0.429 normalized, 57.1% savings).
 * - Eco tier: 384 × 384 at 10 steps = 1,474,560 compute-work units (0.134 normalized, 86.6% savings).
 *
 * Savings Formula:
 * savings_percent = 100 × (1 - (work_units / 11,010,048))
 *
 * Note: Estimated compute-work units are an engineering proxy for GPU workload,
 * not a direct physical measurement of electrical energy consumption (Joules/kWh).
 */

export const HIGH_REFERENCE_WORK_UNITS = 11010048; // 512 × 768 × 28
export const BASELINE_HQ_UNITS = 1.0;

export const TIER_UNITS = {
  eco: 0.1339,
  standard: 0.4286,
  high: 1.0,
  high_quality: 1.0,
  hd: 1.0,
};

export const TIER_SAVINGS = {
  eco: 86.6,
  standard: 57.1,
  high: 0.0,
  high_quality: 0.0,
  hd: 0.0,
};

export const TIER_WORK_UNITS = {
  eco: 1474560, // 384 × 384 × 10
  standard: 4718592, // 512 × 512 × 18
  high: 11010048, // 512 × 768 × 28
};

/**
 * Normalizes tier names to 'eco' | 'standard' | 'high'
 */
export function normalizeTier(tier) {
  if (!tier) return 'standard';
  const t = String(tier).toLowerCase().trim();
  if (t === 'high' || t === 'high_quality' || t === 'hd') return 'high';
  if (t === 'eco') return 'eco';
  return 'standard';
}

/**
 * Returns normalized compute-work units for a given tier.
 */
export function getTierUnits(tier) {
  const norm = normalizeTier(tier);
  return TIER_UNITS[norm] ?? 0.4286;
}

/**
 * Calculates compute-work units: width × height × steps.
 */
export function calculateWorkUnits(width, height, steps) {
  return Number(width) * Number(height) * Number(steps);
}

/**
 * Calculates savings percentage relative to reference High.
 */
export function calculateSavingsPercent(workUnits) {
  if (!workUnits || workUnits <= 0) return 0;
  const savings = 100.0 * (1.0 - (workUnits / HIGH_REFERENCE_WORK_UNITS));
  return Math.max(0, Math.round(savings * 10) / 10);
}

/**
 * Calculates savings percentage from normalized units or raw work units vs baseline.
 */
export function calculateSavingPercent(units, baseline = BASELINE_HQ_UNITS) {
  if (units === undefined || units === null) return 0;
  if (units > 100) {
    return calculateSavingsPercent(units);
  }
  const base = baseline || BASELINE_HQ_UNITS;
  const saved = Math.max(0, (base - units) / base);
  return Math.round(saved * 1000) / 10;
}

/**
 * Returns complete transparent estimate object.
 */
export function estimateResources(tier, measuredTime = null) {
  const norm = normalizeTier(tier);
  const units = getTierUnits(norm);
  const savings = TIER_SAVINGS[norm] ?? 0;
  const isMeasured = measuredTime !== null && measuredTime > 0;
  const time = isMeasured ? Number(measuredTime.toFixed(2)) : null;

  return {
    tier: norm,
    resourceUnits: units,
    baselineUnits: BASELINE_HQ_UNITS,
    savingsPercent: savings,
    unitsSaved: Math.round((BASELINE_HQ_UNITS - units) * 1000) / 1000,
    computeTime: time,
    timingType: isMeasured ? 'measured' : 'unmeasured',
    label: 'Estimated compute-work units',
    formula: `work_units / ${HIGH_REFERENCE_WORK_UNITS.toLocaleString()} (High = 1.0)`,
    assumptions: 'Algorithmic proxy for GPU load (pixels × sampling steps). Not physical electrical energy.',
  };
}

/**
 * Aggregates real session generation metrics from actual records.
 */
export function calculateSessionMetrics(generations = []) {
  if (!generations.length) {
    return {
      totalGenerations: 0,
      ecoCount: 0,
      standardCount: 0,
      highQualityCount: 0,
      totalUnits: 0,
      baselineUnits: 0,
      unitsSaved: 0,
      overallSavingsPercent: 0,
      measuredAvgLatency: '0.00',
    };
  }

  let ecoCount = 0;
  let standardCount = 0;
  let highQualityCount = 0;
  let totalUnits = 0;
  let totalTime = 0;
  let timedRuns = 0;

  generations.forEach((gen) => {
    const tier = normalizeTier(gen.tier || gen.appliedConfiguration?.quality_tier || gen.selected_tier);
    const units = Number(gen.resourceMetrics?.estimated_compute_work_units ?? gen.compute_work_units ?? getTierUnits(tier));
    totalUnits += units;

    if (tier === 'eco') ecoCount++;
    else if (tier === 'standard') standardCount++;
    else highQualityCount++;

    const latency = Number(gen.resourceMetrics?.latency_seconds ?? gen.resourceMetrics?.measured_elapsed_seconds ?? gen.elapsed_seconds);
    if (latency && !isNaN(latency) && latency > 0) {
      totalTime += latency;
      timedRuns++;
    }
  });

  const baselineUnits = generations.length * BASELINE_HQ_UNITS;
  const unitsSaved = Math.max(0, baselineUnits - totalUnits);
  const overallSavingsPercent = baselineUnits > 0
    ? Math.round((unitsSaved / baselineUnits) * 1000) / 10
    : 0;

  return {
    totalGenerations: generations.length,
    ecoCount,
    standardCount,
    highQualityCount,
    totalUnits: Math.round(totalUnits * 1000) / 1000,
    baselineUnits,
    unitsSaved: Math.round(unitsSaved * 1000) / 1000,
    overallSavingsPercent,
    measuredAvgLatency: timedRuns > 0 ? (totalTime / timedRuns).toFixed(2) : '0.00',
  };
}
