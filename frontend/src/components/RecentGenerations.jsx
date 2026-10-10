import { normalizeTier, getTierUnits, calculateSavingPercent } from '../services/resourceEstimation';
import './RecentGenerations.css';

/**
 * RecentGenerations
 * Matches Screenshot 2 Recent Generations Section:
 * - Header: RECENT GENERATIONS with Session History count
 * - 4-column responsive cards grid
 * - Image thumbnail with top-right tier badge
 * - Purpose tag, prompt snippet, metrics line
 * - View in Preview and Compare actions
 */
export function RecentGenerations({
  history = [],
  activeResultId,
  onSelectForView,
  onToggleCompare,
  selectedForCompare = [],
  onOpenCompareModal,
}) {
  if (!history.length) {
    return null;
  }

  return (
    <section className="recent-section" aria-label="Recent Generations">
      {/* ── Section Header ───────────────────────────────── */}
      <div className="recent-header">
        <div className="recent-header__title-group">
          <span className="recent-header__label">RECENT GENERATIONS</span>
          <span className="recent-count-badge">
            Session History ({history.length})
          </span>
        </div>

        <div className="recent-header__actions">
          {selectedForCompare.length > 0 && (
            <button
              type="button"
              className="recent-compare-btn"
              onClick={onOpenCompareModal}
            >
              Compare Selected ({selectedForCompare.length}/2)
            </button>
          )}
        </div>
      </div>

      {/* ── Horizontal Grid of Cards matching Screenshot 2 ── */}
      <div className="recent-grid">
        {history.slice(0, 8).map(item => {
          const rawTier = item.tier || item.appliedConfiguration?.quality_tier || 'eco';
          const tier = normalizeTier(rawTier);
          const units = item.resourceMetrics?.relative_resource_units ?? getTierUnits(tier);
          const savings = item.resourceMetrics?.resource_savings_percent ?? calculateSavingPercent(units);
          const latency = item.resourceMetrics?.latency_seconds !== undefined && item.resourceMetrics?.latency_seconds !== null
            ? `${item.resourceMetrics.latency_seconds}s`
            : null;

          const tierShort = tier === 'eco' ? 'Eco' : (tier === 'standard' ? 'Standard' : 'High');
          const isSelectedForCompare = selectedForCompare.some(c => c.id === item.id);
          const isActive = activeResultId === item.id;
          const purposeLabel = getPurposeName(item.intended_use || item.decisionRationale?.purpose_identified);

          return (
            <div
              key={item.id}
              className={`recent-card ${isActive ? 'recent-card--active' : ''}`}
              onClick={() => onSelectForView(item)}
            >
              {/* Thumbnail Container */}
              <div className="recent-card__thumb-wrap">
                <img
                  src={item.image?.url}
                  alt={item.prompt}
                  className="recent-card__thumb"
                  loading="lazy"
                />
                <span className={`recent-card__tier-tag recent-card__tier-tag--${tier}`}>
                  {tierShort}
                </span>
              </div>

              {/* Card Body */}
              <div className="recent-card__body">
                <span className="recent-card__purpose">{purposeLabel}</span>
                <p className="recent-card__prompt" title={item.prompt}>
                  {item.prompt}
                </p>

                <div className="recent-card__metrics-row">
                  <span className="recent-card__metrics">
                    {latency ? `${latency} (measured) • ` : ''}{units.toFixed(3)} units • {savings}% savings
                  </span>
                </div>
              </div>

              {/* Card Actions */}
              <div className="recent-card__actions" onClick={e => e.stopPropagation()}>
                <button
                  type="button"
                  className="recent-btn recent-btn--view"
                  onClick={() => onSelectForView(item)}
                >
                  View in Preview
                </button>

                <button
                  type="button"
                  className={`recent-btn recent-btn--compare ${isSelectedForCompare ? 'recent-btn--compare-active' : ''}`}
                  onClick={() => onToggleCompare(item)}
                >
                  {isSelectedForCompare ? '✓ In Compare' : '+ Compare'}
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}

function getPurposeName(use) {
  const map = {
    coloring_sheet: 'Colouring Sheet',
    worksheet_activity: 'Worksheet / Handout',
    flashcard: 'Flashcard',
    lesson_diagram: 'Lesson Diagram',
    presentation_slide: 'Presentation Slide',
    educational_poster: 'Educational Poster',
    printed_banner: 'Printed Banner',
    detailed_illustration: 'Detailed Illustration',
    general_educational: 'Educational Graphic',
  };
  return map[use] || (use ? use.replace(/_/g, ' ') : 'Educational Graphic');
}
