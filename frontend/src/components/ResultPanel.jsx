import { useState } from 'react';
import { STATUS } from '../hooks/useGeneration';
import { ResourceComparison } from './ResourceComparison';
import './ResultPanel.css';

/**
 * ResultPanel
 * Displays real generated images and transparent compute-work telemetry:
 * - Header: IMAGE PREVIEW, Inferred Purpose & Tier Badges (plus User Override indicator)
 * - Image viewport (rendered with real base64/data URI)
 * - Transparent Resource Estimation & Savings Comparison (Constraint 1)
 * - Quick Tier Switcher for side-by-side comparison
 * - Action buttons: Copy Prompt, Download Generated Image
 */
export function ResultPanel({ status, result, error, errorDetails, onReset, onSwitchTier }) {
  const [copied, setCopied] = useState(false);

  if (status === STATUS.LOADING) {
    return (
      <div className="studio-card studio-preview-card studio-preview-card--loading">
        <div className="preview-loading-spinner" aria-hidden="true" />
        <p className="preview-loading-title">Generating Local Stable Diffusion Image…</p>
        <p className="preview-loading-sub">
          Applying right-sized resolution and sampling passes to the local AUTOMATIC1111 engine.
        </p>
      </div>
    );
  }

  if (status === STATUS.ERROR) {
    return (
      <div className="studio-card studio-preview-card studio-preview-card--error" role="alert">
        <div className="preview-error-header">
          <span className="preview-error-icon" aria-hidden="true">⚠️</span>
          <h4>{errorDetails?.title || 'Generation Unsuccessful'}</h4>
        </div>
        <p className="preview-error-msg">{error}</p>
        {errorDetails?.advice && (
          <p className="preview-error-advice">
            <strong>Action required:</strong> {errorDetails.advice}
          </p>
        )}
        <button type="button" className="preview-retry-btn" onClick={onReset}>
          Try Again
        </button>
      </div>
    );
  }

  if (!result || !result.image) {
    return (
      <div className="studio-card studio-preview-card studio-preview-card--empty">
        <div className="preview-empty-icon" aria-hidden="true">🖼️</div>
        <p className="preview-empty-title">Ready for Local Image Generation</p>
        <p className="preview-empty-sub">
          Enter an educational prompt on the left. The engine will infer the purpose,
          recommend a right-sized quality tier, and display transparent compute metrics.
        </p>
      </div>
    );
  }

  const { image, applied_configuration: config, decision_rationale: rationale, resource_metrics: metrics } = result;

  const rawTier = config?.quality_tier || 'standard';
  const tier = String(rawTier).toLowerCase();
  const tierLabel = tier === 'eco' ? 'Eco Mode' : (tier === 'high' || tier === 'hd' || tier === 'high_quality' ? 'High Tier' : 'Standard Tier');
  const purposeName = rationale?.purpose_identified || result.request_params?.intended_use || 'Educational Illustration';

  const promptText = result.request_params?.prompt || config?.prompt_refinement || 'Educational image prompt';



  function handleCopyPrompt() {
    navigator.clipboard?.writeText(promptText);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  const displayImageUrl = image.artifact_url || image.url;

  function handleDownload() {
    if (!displayImageUrl) return;
    const link = document.createElement('a');
    link.href = displayImageUrl;
    link.download = `resourceaware-${tier}-${Date.now()}.${image.format || 'png'}`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }

  return (
    <div className="studio-card studio-preview-card" aria-label="Generated image preview">
      {/* ── 1. Header with Inferred Purpose & Selected Tier Badges ── */}
      <div className="preview-header">
        <span className="preview-header__label">LOCAL GENERATION PREVIEW</span>

        <div className="preview-badges-row">
          <span className="preview-badge preview-badge--purpose" title="Inferred educational purpose">
            {purposeName}
          </span>
          <span className={`preview-badge preview-badge--${tier === 'high' || tier === 'hd' ? 'high' : tier}`}>
            {tierLabel}
          </span>
          {rationale?.tier_overridden && (
            <span
              className="preview-badge preview-badge--override"
              title={`User manual override: System proposed ${rationale?.recommended_tier?.toUpperCase()}, but ${tier.toUpperCase()} was selected.`}
            >
              ⚡ User Override ({rationale?.recommended_tier?.toUpperCase()} &rarr; {tier.toUpperCase()})
            </span>
          )}
        </div>
      </div>

      {/* ── 2. Image Viewport (Real Generated Image) ───── */}
      <div className="preview-viewport">
        <img
          src={displayImageUrl}
          alt={promptText}
          className="preview-image"
          loading="eager"
        />

        {metrics?.is_demo && (
          <div className="preview-demo-tag" role="status">
            <span>⚠️ Test preview mode (Mock provider)</span>
          </div>
        )}
      </div>

      {/* ── 3. Prompt Box Below Image ──────────────────── */}
      <div className="preview-prompt-box">
        <p className="preview-prompt-content">
          <strong>Prompt:</strong> &ldquo;{promptText}&rdquo;
        </p>
      </div>

      {/* ── 4. Resource Estimation, Savings & Transparent Methodology (Constraint 1) ── */}
      <ResourceComparison metrics={metrics} config={config} />

      {/* ── 5. Quick Tier Switcher to Test & Compare ── */}
      {onSwitchTier && (
        <div className="preview-tier-switcher-row">
          <span className="tier-switcher-label">Compare Other Tiers:</span>
          <div className="tier-switcher-pills">
            {['eco', 'standard', 'high'].map(t => (
              <button
                key={t}
                type="button"
                className={`tier-switch-btn ${tier === t ? 'tier-switch-btn--active' : ''}`}
                onClick={() => onSwitchTier(t)}
                title={`Regenerate with ${t.toUpperCase()} tier to compare resources`}
              >
                {t === 'high' ? 'High (Baseline)' : `${t.toUpperCase()} (${t === 'eco' ? '86.6%' : '57.1%'} saved)`}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* ── 6. Action & Meta Bar ───────────────────────── */}
      <div className="preview-footer">
        <span className="preview-meta-stats">
          Model: {config?.model || 'stable-diffusion-v1-5'} • Sampler: {config?.sampler_name || 'Euler a'}
        </span>

        <div className="preview-actions">
          <button
            type="button"
            className="preview-action-btn"
            onClick={handleCopyPrompt}
            title="Copy prompt text"
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
              <rect x="9" y="9" width="13" height="13" rx="2" ry="2" />
              <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" />
            </svg>
            <span>{copied ? 'Copied!' : 'Copy Prompt'}</span>
          </button>

          <button
            type="button"
            className="preview-action-btn preview-action-btn--primary"
            onClick={handleDownload}
            title="Download image file"
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
              <polyline points="7 10 12 15 17 10" />
              <line x1="12" y1="15" x2="12" y2="3" />
            </svg>
            <span>Download Image</span>
          </button>
        </div>
      </div>
    </div>
  );
}
