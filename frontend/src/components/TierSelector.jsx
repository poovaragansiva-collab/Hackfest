import { TIERS } from '../services/apiService';
import './TierSelector.css';

/**
 * TierSelector
 * Apple iOS Liquid Glass Segmented Tier Cards
 * Renders Standard vs HD quality tiers with recommendation tags and clear feedback.
 */
export function TierSelector({
  selected,
  onChange,
  recommendedTierId,
  recommendReason,
  disabled,
}) {
  const isOverride = selected && selected !== recommendedTierId;

  return (
    <div className="tier-selector">
      <div className="tier-selector__header">
        <span className="tier-selector__label">
          Quality &amp; Effort Tier <span className="required" aria-hidden="true">*</span>
        </span>
      </div>

      <div className="tier-cards" role="group" aria-label="Select quality tier">
        {TIERS.map(tier => {
          const isSelected = selected === tier.id;
          const isRecommended = tier.id === recommendedTierId;

          return (
            <button
              key={tier.id}
              type="button"
              id={`tier-${tier.id}`}
              className={`tier-card${isSelected ? ' tier-card--selected' : ''}`}
              onClick={() => onChange(tier.id)}
              disabled={disabled}
              aria-pressed={isSelected}
              aria-label={`${tier.label}${isRecommended ? ' — recommended for this purpose' : ''}`}
            >
              {isRecommended && (
                <span className="tier-card__rec-badge" aria-hidden="true">
                  <span className="rec-star">★</span> Recommended
                </span>
              )}

              <div className="tier-card__top">
                <span className="tier-card__icon" aria-hidden="true">{tier.icon}</span>
                <div className="tier-card__heading">
                  <span className="tier-card__name">{tier.label}</span>
                  <span className="tier-card__tagline">{tier.tagline}</span>
                </div>
              </div>

              <p className="tier-card__desc">{tier.description}</p>

              <ul className="tier-card__caps" aria-label={`${tier.label} capabilities`}>
                {tier.capabilities.map((cap, i) => (
                  <li key={i}>{cap}</li>
                ))}
              </ul>
            </button>
          );
        })}
      </div>

      {/* Recommendation reasoning */}
      {recommendReason && !isOverride && (
        <div className="tier-rec-note" role="note">
          <span className="tier-note-icon">💡</span>
          <span><strong>Why recommended:</strong> {recommendReason}</span>
        </div>
      )}

      {/* Override Notice */}
      {isOverride && (
        <div className="tier-override-note" role="note">
          <span className="tier-note-icon">ℹ️</span>
          <span>
            User manual override active.
            {recommendReason && <> (Default recommended: {recommendReason})</>}
          </span>
        </div>
      )}
    </div>
  );
}
