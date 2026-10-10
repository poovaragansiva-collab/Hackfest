import { TIERS } from '../services/mockGenerationService';
import './TierSelector.css';

/**
 * TierSelector
 * Renders two quality/effort tier cards with recommendation badge.
 * Shows a note when the user overrides the recommended tier.
 * Never silently overrides the user's selection.
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
      <p className="tier-selector__label">
        Quality / effort tier <span aria-hidden="true">*</span>
      </p>

      <div className="tier-cards" role="group" aria-label="Select quality tier">
        {TIERS.map(tier => {
          const isSelected  = selected === tier.id;
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
                  Recommended for this purpose
                </span>
              )}
              <span className="tier-card__icon" aria-hidden="true">{tier.icon}</span>
              <span className="tier-card__name">{tier.label}</span>
              <span className="tier-card__tagline">{tier.tagline}</span>
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

      {/* Recommendation context */}
      {recommendReason && !isOverride && (
        <p className="tier-rec-note" role="note">
          <strong>Why recommended:</strong> {recommendReason}
        </p>
      )}

      {/* Override notice — user chose differently, never hidden */}
      {isOverride && (
        <p className="tier-override-note" role="note">
          You have chosen a different tier than the one recommended for this purpose.
          {recommendReason && <> Recommendation: {recommendReason}</>}
        </p>
      )}
    </div>
  );
}
