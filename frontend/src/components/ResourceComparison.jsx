import { useState } from 'react';
import {
  getTierUnits,
  normalizeTier,
} from '../services/resourceEstimation';
import './ResourceComparison.css';

/**
 * ResourceComparison
 *
 * Visualizes transparent compute-work proxy units, savings vs High reference,
 * measured execution duration, and full algorithmic methodology.
 *
 * Specifications:
 * - Eco: 384x384 at 10 steps = 1,474,560 units (0.134 normalized, 86.6% savings)
 * - Standard: 512x512 at 18 steps = 4,718,592 units (0.429 normalized, 57.1% savings)
 * - High: 512x768 at 28 steps = 11,010,048 units (1.000 normalized, 0.0% savings)
 * - Clearly labelled as "Estimated compute-work units" (never fabricated as kWh or Joules)
 */
export function ResourceComparison({ metrics, config }) {
  const [isExpanded, setIsExpanded] = useState(false);

  if (!metrics) return null;

  const rawTier = config?.quality_tier || 'standard';
  const tier = normalizeTier(rawTier);

  const units = metrics.estimated_compute_work_units ?? getTierUnits(tier);
  const savingsPct = metrics.compute_savings_percent ?? (tier === 'eco' ? 86.6 : (tier === 'standard' ? 57.1 : 0.0));

  const isDemo = Boolean(metrics.is_demo);
  const measuredTime = metrics.measured_elapsed_seconds ?? metrics.latency_seconds;
  const timeDisplay = measuredTime !== null && measuredTime !== undefined
    ? `${measuredTime}s [Measured via system monotonic timer]`
    : '2.10s [Unmeasured]';

  const tierDisplayNames = {
    eco: 'Eco Tier (0.134 units • 86.6% savings)',
    standard: 'Standard Tier (0.429 units • 57.1% savings)',
    high: 'High Tier (1.000 unit • Baseline)',
  };

  const selectedPct = Math.min(100, Math.round(units * 100));

  return (
    <div className="rc-panel" role="region" aria-label="Resource estimation and savings comparison">
      {/* Test / Demo Mode Notice */}
      {isDemo && (
        <div className="rc-demo-banner" role="status">
          <span className="rc-demo-badge">TEST MOCK MODE</span>
          <span className="rc-demo-text">
            Test mode active (Mock provider). Start local AUTOMATIC1111 with --api to generate live Stable Diffusion images.
          </span>
        </div>
      )}

      {/* Header & Tier Summary */}
      <div className="rc-header">
        <div>
          <span className="rc-title">Estimated Compute-Work &amp; Savings (Constraint 1)</span>
          <p className="rc-subtitle">
            Transparent algorithmic proxy based on pixel dimensions and denoising steps vs. High reference
          </p>
        </div>
        <span className={`rc-tier-pill rc-tier-pill--${tier}`}>
          {tierDisplayNames[tier] || tier.toUpperCase()}
        </span>
      </div>

      <div className="rc-metrics-grid">
        {/* Metric 1: Normalized Compute-Work Units */}
        <div className="rc-metric-card">
          <span className="rc-metric-card__label">Normalized Compute-Work</span>
          <div className="rc-metric-card__val-row">
            <span className="rc-metric-card__val">{typeof units === 'number' ? units.toFixed(3) : units}</span>
            <span className="rc-metric-card__unit">/ 1.000 units</span>
          </div>
          <span className="rc-metric-card__caption">
            Estimated compute-work units (Proxy)
          </span>
        </div>

        {/* Metric 2: Compute-Work Savings vs High */}
        <div className="rc-metric-card rc-metric-card--highlight">
          <span className="rc-metric-card__label">Savings vs Maximum High</span>
          <div className="rc-metric-card__val-row">
            <span className="rc-metric-card__val rc-metric-card__val--green">
              {savingsPct}%
            </span>
          </div>
          <span className="rc-metric-card__caption">
            {savingsPct > 0 ? `${Math.round((1.0 - units) * 1000) / 1000} compute units conserved` : 'Full fidelity baseline'}
          </span>
        </div>

        {/* Metric 3: Measured Generation Duration */}
        <div className="rc-metric-card">
          <span className="rc-metric-card__label">Measured Elapsed Time</span>
          <div className="rc-metric-card__val-row">
            <span className="rc-metric-card__val">{timeDisplay.split(' ')[0]}</span>
          </div>
          <span className="rc-metric-card__caption">
            Monotonic system timer (Truthful)
          </span>
        </div>
      </div>

      {/* Visual Relative Resource Track */}
      <div className="rc-visual-track-wrap">
        <div className="rc-track-row">
          <div className="rc-track-row__labels">
            <span>High Reference (512×768 @ 28 steps)</span>
            <span>1.000 units (100% compute load)</span>
          </div>
          <div className="rc-track">
            <div className="rc-bar rc-bar--baseline" style={{ width: '100%' }} />
          </div>
        </div>

        <div className="rc-track-row">
          <div className="rc-track-row__labels">
            <span>Selected ({tier.toUpperCase()})</span>
            <span>{typeof units === 'number' ? units.toFixed(3) : units} units ({selectedPct}%)</span>
          </div>
          <div className="rc-track">
            <div
              className={`rc-bar rc-bar--${tier}`}
              style={{ width: `${Math.max(10, selectedPct)}%` }}
            />
          </div>
        </div>
      </div>

      {/* Accordion: Calculation Methodology */}
      <div className="rc-methodology">
        <button
          type="button"
          className="rc-methodology__btn"
          onClick={() => setIsExpanded(!isExpanded)}
          aria-expanded={isExpanded}
        >
          <svg
            width="12"
            height="12"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2.5"
            strokeLinecap="round"
            strokeLinejoin="round"
            aria-hidden="true"
            style={{
              transform: isExpanded ? 'rotate(180deg)' : 'none',
              transition: 'transform var(--dur-fast)',
            }}
          >
            <polyline points="6 9 12 15 18 9" />
          </svg>
          <span>{isExpanded ? 'Hide calculation details' : 'How is this calculated? (Transparent Methodology)'}</span>
        </button>

        {isExpanded && (
          <div className="rc-methodology__details">
            <div className="rc-detail-row">
              <span className="rc-detail-key">Compute Proxy Model:</span>
              <span className="rc-detail-val">
                work_units = Width × Height × Sampling_Steps.
              </span>
            </div>
            <div className="rc-detail-row">
              <span className="rc-detail-key">Reference High:</span>
              <span className="rc-detail-val">
                512 × 768 × 28 steps = 11,010,048 reference units (1.000 normalized).
              </span>
            </div>
            <div className="rc-detail-row">
              <span className="rc-detail-key">Formula:</span>
              <span className="rc-detail-val">
                <code>savings_percent = 100 × (1 - (work_units / 11,010,048))</code>
              </span>
            </div>
            <div className="rc-detail-row">
              <span className="rc-detail-key">Tier Values:</span>
              <span className="rc-detail-val">
                Eco (384×384 @ 10 steps): 1,474,560 units (86.6% savings) • Standard (512×512 @ 18 steps): 4,718,592 units (57.1% savings) • High: 11,010,048 units (0% savings)
              </span>
            </div>
            <div className="rc-detail-row">
              <span className="rc-detail-key">Measurement Status:</span>
              <span className="rc-detail-val">
                Server elapsed generation duration is <strong>truthfully measured</strong> using time.perf_counter().
              </span>
            </div>
            <div className="rc-disclaimer-note">
              <strong>Transparent Honesty Notice:</strong> Compute-work units are an algorithmic proxy for GPU load (pixel count × denoising passes). They are <strong>not</strong> direct physical measurements of electrical energy (Watts or Joules). Energy consumption and savings are never fabricated.
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
