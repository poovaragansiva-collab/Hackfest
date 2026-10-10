import { normalizeTier, getTierUnits, calculateSavingPercent } from '../services/resourceEstimation';
import './CompareModal.css';

/**
 * CompareModal
 * Clean side-by-side modal comparing any 2 generations with detailed specs:
 * prompt, quality tier, diffusion steps, relative resource units, and mathematical savings.
 */
export function CompareModal({ items = [], onClose, onClear }) {
  if (items.length !== 2) return null;

  const [itemA, itemB] = items;

  function renderColumn(item, label) {
    const rawTier = item.tier || item.appliedConfiguration?.quality_tier || 'eco';
    const tier = normalizeTier(rawTier);
    const units = item.resourceMetrics?.relative_resource_units ?? getTierUnits(tier);
    const savings = item.resourceMetrics?.resource_savings_percent ?? calculateSavingPercent(units);
    const steps = item.appliedConfiguration?.steps || (tier === 'eco' ? 10 : (tier === 'standard' ? 18 : 28));
    const res = item.appliedConfiguration?.effective_resolution || (tier === 'eco' ? '384x384' : (tier === 'standard' ? '512x512' : '512x768'));
    const latency = item.resourceMetrics?.latency_seconds !== undefined && item.resourceMetrics?.latency_seconds !== null
      ? `${item.resourceMetrics.latency_seconds}s (measured)`
      : '—';

    const tierTitle = tier === 'eco' ? 'Eco Mode' : (tier === 'standard' ? 'Standard Mode' : 'High Quality');

    return (
      <div className="compare-col">
        <div className="compare-col__badge">{label}</div>

        <div className="compare-col__thumb-wrap">
          <img src={item.image?.url} alt={item.prompt} className="compare-col__thumb" />
          <span className={`compare-col__tier-pill compare-col__tier-pill--${tier}`}>
            {tierTitle}
          </span>
        </div>

        <div className="compare-col__prompt-box">
          <p className="compare-col__prompt">&ldquo;{item.prompt}&rdquo;</p>
        </div>

        <div className="compare-spec-table">
          <div className="compare-spec-row">
            <span className="spec-label">Relative Resources</span>
            <span className="spec-val spec-val--highlight">{units.toFixed(3)} units</span>
          </div>

          <div className="compare-spec-row">
            <span className="spec-label">Savings vs Baseline</span>
            <span className={`spec-val ${savings > 0 ? 'spec-val--green' : ''}`}>
              {savings}%
            </span>
          </div>

          <div className="compare-spec-row">
            <span className="spec-label">Diffusion Passes</span>
            <span className="spec-val">{steps} steps</span>
          </div>

          <div className="compare-spec-row">
            <span className="spec-label">Resolution</span>
            <span className="spec-val">{res}</span>
          </div>

          <div className="compare-spec-row">
            <span className="spec-label">Elapsed Time</span>
            <span className="spec-val">{latency}</span>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="compare-modal-backdrop" onClick={onClose} role="dialog" aria-modal="true" aria-label="Side-by-side generation comparison">
      <div className="compare-modal-box" onClick={e => e.stopPropagation()}>
        <div className="compare-modal-header">
          <div>
            <span className="compare-modal-kicker">RIGHT-SIZING COMPARISON</span>
            <h3 className="compare-modal-title">Side-by-Side Resource Breakdown</h3>
          </div>
          <button type="button" className="compare-close-btn" onClick={onClose} aria-label="Close comparison">
            ✕
          </button>
        </div>

        <div className="compare-columns-grid">
          {renderColumn(itemA, 'Generation A')}
          <div className="compare-vs-divider">VS</div>
          {renderColumn(itemB, 'Generation B')}
        </div>

        <div className="compare-modal-footer">
          <button type="button" className="compare-clear-btn" onClick={onClear}>
            Clear Selection
          </button>
          <button type="button" className="compare-done-btn" onClick={onClose}>
            Done
          </button>
        </div>
      </div>
    </div>
  );
}
