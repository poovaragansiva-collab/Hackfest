import { useState } from 'react';
import { normalizeTier, getTierUnits, calculateSavingPercent } from '../services/resourceEstimation';
import './GenerationHistory.css';

/**
 * GenerationHistory
 *
 * Displays full session generation history with prompt, selected tier,
 * estimated relative resource units, and savings vs High Quality baseline.
 * Supports side-by-side comparison between any two generations (e.g. Eco Elephant vs HQ Poster).
 */
export function GenerationHistory({ history = [], onSelectForView, onClearHistory }) {
  const [selectedForCompare, setSelectedForCompare] = useState([]);

  function toggleCompare(item) {
    if (selectedForCompare.some(c => c.id === item.id)) {
      setSelectedForCompare(selectedForCompare.filter(c => c.id !== item.id));
    } else {
      if (selectedForCompare.length >= 2) {
        // Replace second item if 2 are already selected
        setSelectedForCompare([selectedForCompare[0], item]);
      } else {
        setSelectedForCompare([...selectedForCompare, item]);
      }
    }
  }

  const isComparing = selectedForCompare.length === 2;

  if (!history.length) {
    return (
      <div className="history-empty panel">
        <div className="history-empty__icon">🕒</div>
        <h3>No Generation History Yet</h3>
        <p>
          Generations created in this session will appear here with prompt details,
          selected quality tier, relative resource units, and savings metrics.
        </p>
      </div>
    );
  }

  return (
    <div className="history-container">
      {/* Top Controls Bar */}
      <div className="history-header">
        <div>
          <h2>Generation History &amp; Comparison</h2>
          <p className="history-subtitle">
            {history.length} generation{history.length === 1 ? '' : 's'} recorded this session. Select any 2 to compare side-by-side.
          </p>
        </div>

        <div className="history-actions">
          {selectedForCompare.length > 0 && (
            <button
              type="button"
              className="btn-history-secondary"
              onClick={() => setSelectedForCompare([])}
            >
              Clear Comparison ({selectedForCompare.length}/2)
            </button>
          )}
          <button
            type="button"
            className="btn-history-danger"
            onClick={onClearHistory}
            title="Clear current session history"
          >
            Clear History
          </button>
        </div>
      </div>

      {/* Side-by-Side Comparison Modal / Box */}
      {isComparing && (
        <div className="compare-box panel" role="region" aria-label="Side-by-side generation comparison">
          <div className="compare-header">
            <div className="compare-header__title">
              <span className="compare-badge">SIDE-BY-SIDE COMPARISON</span>
              <h3>Right-Sizing Efficiency Comparison</h3>
            </div>
            <button
              type="button"
              className="compare-close-btn"
              onClick={() => setSelectedForCompare([])}
              aria-label="Close comparison view"
            >
              ✕
            </button>
          </div>

          <div className="compare-grid">
            {selectedForCompare.map((item, idx) => {
              const tier = normalizeTier(item.appliedConfiguration?.quality_tier || item.tier);
              const units = item.resourceMetrics?.relative_resource_units ?? getTierUnits(tier);
              const savings = item.resourceMetrics?.resource_savings_percent ?? calculateSavingPercent(units);
              const isDemo = Boolean(item.resourceMetrics?.is_demo);

              return (
                <div key={item.id} className={`compare-card compare-card--${tier}`}>
                  <div className="compare-card__tag">
                    Generation {idx + 1}: {tier.toUpperCase()} TIER
                  </div>

                  <div className="compare-card__image-wrap">
                    <img
                      src={item.image?.artifact_url || item.image?.url}
                      alt={item.prompt}
                      className="compare-card__image"
                    />
                    {isDemo && (
                      <span className="compare-demo-pill">Demo preview</span>
                    )}
                  </div>

                  <div className="compare-card__body">
                    <p className="compare-card__prompt">&ldquo;{item.prompt}&rdquo;</p>
                    <div className="compare-card__purpose">
                      <strong>Purpose:</strong> {item.intended_use || item.decisionRationale?.purpose_identified}
                    </div>

                    <div className="compare-stats-grid">
                      <div className="compare-stat">
                        <span className="stat-label">Relative Resources</span>
                        <span className="stat-val stat-val--mono">{units} unit{units === 1 ? '' : 's'}</span>
                      </div>
                      <div className="compare-stat">
                        <span className="stat-label">Savings vs HQ</span>
                        <span className={`stat-val ${savings > 0 ? 'stat-val--green' : ''}`}>{savings}%</span>
                      </div>
                      <div className="compare-stat">
                        <span className="stat-label">Resolution</span>
                        <span className="stat-val stat-val--mono">{item.appliedConfiguration?.effective_resolution || '—'}</span>
                      </div>
                      <div className="compare-stat">
                        <span className="stat-label">Inference Steps</span>
                        <span className="stat-val stat-val--mono">
                          {item.appliedConfiguration?.steps ? `${item.appliedConfiguration.steps} steps` : 'Default'}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Efficiency Takeaway Footer */}
          <div className="compare-footer">
            <div className="compare-takeaway">
              <span className="takeaway-icon">💡</span>
              <div>
                <strong>Curriculum Efficiency Impact:</strong>{' '}
                {(() => {
                  const t1 = normalizeTier(selectedForCompare[0].appliedConfiguration?.quality_tier);
                  const t2 = normalizeTier(selectedForCompare[1].appliedConfiguration?.quality_tier);
                  const u1 = selectedForCompare[0].resourceMetrics?.relative_resource_units ?? getTierUnits(t1);
                  const u2 = selectedForCompare[1].resourceMetrics?.relative_resource_units ?? getTierUnits(t2);
                  const diff = Math.abs(u1 - u2);
                  if (diff > 0) {
                    const lowerItem = u1 < u2 ? selectedForCompare[0] : selectedForCompare[1];
                    const higherItem = u1 < u2 ? selectedForCompare[1] : selectedForCompare[0];
                    const lowerTier = normalizeTier(lowerItem.appliedConfiguration?.quality_tier);
                    const higherTier = normalizeTier(higherItem.appliedConfiguration?.quality_tier);
                    return `Selecting ${lowerTier.toUpperCase()} instead of ${higherTier.toUpperCase()} consumes ${diff} fewer relative resource units (${calculateSavingPercent(Math.min(u1, u2), Math.max(u1, u2))}% reduction). For simple outlines and worksheets, this prevents massive wasted GPU compute across hundreds of schools.`;
                  }
                  return 'Both generations use identical quality tiers with equal resource utilization.';
                })()}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* History Items Grid */}
      <div className="history-grid">
        {history.map((item) => {
          const tier = normalizeTier(item.appliedConfiguration?.quality_tier || item.tier);
          const units = item.resourceMetrics?.relative_resource_units ?? getTierUnits(tier);
          const savings = item.resourceMetrics?.resource_savings_percent ?? calculateSavingPercent(units);
          const isSelected = selectedForCompare.some(c => c.id === item.id);
          const isDemo = Boolean(item.resourceMetrics?.is_demo);
          const timingLabel = item.resourceMetrics?.generation_time_label === 'measured' ? 'measured' : 'estimate';
          const latency = item.resourceMetrics?.latency_seconds;

          return (
            <div
              key={item.id}
              className={`history-card panel ${isSelected ? 'history-card--selected-compare' : ''}`}
            >
              <div className="history-card__media">
                <img
                  src={item.image?.artifact_url || item.image?.url}
                  alt={item.prompt}
                  className="history-card__thumb"
                  loading="lazy"
                />
                <span className={`history-tier-badge history-tier-badge--${tier}`}>
                  {tier.toUpperCase()} ({units} unit{units === 1 ? '' : 's'})
                </span>
                {isDemo && (
                  <span className="history-demo-badge">Demo</span>
                )}
              </div>

              <div className="history-card__body">
                <p className="history-card__prompt" title={item.prompt}>
                  {item.prompt}
                </p>

                <div className="history-card__meta">
                  <span className="history-meta-purpose">
                    {item.intended_use?.replace(/_/g, ' ') || 'educational'}
                  </span>
                  <span className="history-meta-time">
                    {new Date(item.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </span>
                </div>

                <div className="history-card__metrics-row">
                  <div className="history-metric">
                    <span className="metric-label">Relative Units:</span>
                    <span className="metric-val">{typeof units === 'number' && units <= 1 ? units.toFixed(3) : units} / 1.000</span>
                  </div>
                  <div className="history-metric">
                    <span className="metric-label">HQ Savings:</span>
                    <span className={`metric-val ${savings > 0 ? 'metric-val--green' : ''}`}>
                      {savings}%
                    </span>
                  </div>
                </div>

                {latency && (
                  <div className="history-card__latency">
                    <span>Latency: {latency}s ({timingLabel})</span>
                  </div>
                )}

                <div className="history-card__btn-row">
                  <button
                    type="button"
                    className={`btn-compare-toggle ${isSelected ? 'btn-compare-toggle--active' : ''}`}
                    onClick={() => toggleCompare(item)}
                    aria-pressed={isSelected}
                  >
                    {isSelected ? '✓ In Compare' : '+ Compare'}
                  </button>
                  <button
                    type="button"
                    className="btn-view-result"
                    onClick={() => onSelectForView && onSelectForView(item)}
                  >
                    View Result
                  </button>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
