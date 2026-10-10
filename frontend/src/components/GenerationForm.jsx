import { useState, useEffect, useRef } from 'react';
import { STATUS } from '../hooks/useGeneration';
import { inferPurposeApi, TIERS, USE_CASES } from '../services/apiService';
import './GenerationForm.css';

const PROMPT_SUGGESTIONS = [
  {
    label: 'Colouring sheet (7yo)',
    prompt: 'Make a simple black-and-white colouring sheet of a butterfly for a seven-year-old.',
    hint: 'Acceptance Scenario 1 (Infers Eco)',
  },
  {
    label: 'Water cycle poster',
    prompt: 'Create an illustrated educational poster about the water cycle.',
    hint: 'Acceptance Scenario 2 (Infers Standard)',
  },
  {
    label: 'Exhibition banner',
    prompt: 'Create a highly detailed illustration for a large printed school exhibition banner.',
    hint: 'Acceptance Scenario 3 (Infers High)',
  },
  {
    label: 'Geometry worksheet',
    prompt: 'A simple geometry worksheet illustration showing fractions of a circle.',
    hint: 'Classroom handout (Infers Eco)',
  },
  {
    label: 'Thumbnail icon',
    prompt: 'A small thumbnail icon of a science beaker for a student project.',
    hint: 'Small Icon / Thumbnail (Infers Eco)',
  },
];

const MAX_PROMPT = 600;

export function GenerationForm({ onSubmit, status }) {
  const isLoading = status === STATUS.LOADING;

  const [prompt, setPrompt] = useState(
    'Make a simple black-and-white colouring sheet of a butterfly for a seven-year-old.'
  );
  const [negativePrompt, setNegativePrompt] = useState('');
  const [showNegPrompt, setShowNegPrompt] = useState(false);

  // Purpose Inference & Menu State (Constraint 2)
  const [purposeMode, setPurposeMode] = useState('auto'); // 'auto' | use_case_value
  const [inferredPurpose, setInferredPurpose] = useState("Children's colouring sheet");
  const [recommendedTier, setRecommendedTier] = useState('eco');
  const [explanation, setExplanation] = useState(
    'Simple outlines, black-and-white output, and classroom worksheet use do not require maximum rendering effort.'
  );
  const [selectedTier, setSelectedTier] = useState('eco');
  const [userOverrodeTier, setUserOverrodeTier] = useState(false);
  const [error, setError] = useState('');

  const debounceTimer = useRef(null);

  // Trigger automatic purpose inference on prompt change (when in auto mode)
  useEffect(() => {
    if (purposeMode !== 'auto') return;

    if (!prompt.trim()) {
      setInferredPurpose('Awaiting prompt description');
      setRecommendedTier('standard');
      setExplanation('Please enter an image prompt description to automatically infer purpose and recommend compute effort.');
      return;
    }
    if (prompt.trim().length < 3) {
      setInferredPurpose('Prompt too short');
      setRecommendedTier('standard');
      setExplanation('Please enter at least 3 characters to analyze purpose.');
      return;
    }

    if (debounceTimer.current) clearTimeout(debounceTimer.current);

    debounceTimer.current = setTimeout(async () => {
      try {
        const result = await inferPurposeApi(prompt);
        if (result && result.purpose) {
          setInferredPurpose(result.purpose);
          setRecommendedTier(result.recommended_tier);
          setExplanation(result.reason);

          // If user hasn't manually selected an override, follow recommendation
          if (!userOverrodeTier) {
            setSelectedTier(result.recommended_tier);
          }
        }
      } catch {
        // Silent catch for live inference
      }
    }, 350);

    return () => {
      if (debounceTimer.current) clearTimeout(debounceTimer.current);
    };
  }, [prompt, purposeMode, userOverrodeTier]);

  function handlePurposeSelectChange(e) {
    const val = e.target.value;
    setPurposeMode(val);

    if (val === 'auto') {
      // Re-run inference on current prompt
      inferPurposeApi(prompt).then(res => {
        if (res && res.purpose) {
          setInferredPurpose(res.purpose);
          setRecommendedTier(res.recommended_tier);
          setExplanation(res.reason);
          if (!userOverrodeTier) {
            setSelectedTier(res.recommended_tier);
          }
        }
      });
    } else {
      // Find selected use-case from menu
      const uc = USE_CASES.find(u => u.value === val);
      if (uc) {
        setInferredPurpose(uc.label);
        setRecommendedTier(uc.recommendedTier);
        setExplanation(uc.recommendReason);
        if (!userOverrodeTier) {
          setSelectedTier(uc.recommendedTier);
        }
      }
    }
  }

  function handleSelectTier(tierId) {
    if (isLoading) return;
    setSelectedTier(tierId);
    if (tierId !== recommendedTier) {
      setUserOverrodeTier(true);
    } else {
      setUserOverrodeTier(false);
    }
  }

  function applySuggestion(sug) {
    setPrompt(sug.prompt);
    setPurposeMode('auto');
    setUserOverrodeTier(false);
    setError('');

    // Instant local evaluation for responsiveness
    inferPurposeApi(sug.prompt).then(res => {
      if (res && res.purpose) {
        setInferredPurpose(res.purpose);
        setRecommendedTier(res.recommended_tier);
        setExplanation(res.reason);
        setSelectedTier(res.recommended_tier);
      }
    });
  }

  function handleSubmit(e) {
    e.preventDefault();
    if (!prompt.trim()) {
      setError('Please enter an image prompt description before generating.');
      return;
    }
    if (prompt.trim().length < 3) {
      setError('Prompt must be at least 3 characters long before generating.');
      return;
    }
    setError('');

    onSubmit({
      prompt: prompt.trim(),
      negative_prompt: negativePrompt.trim(),
      intended_use: purposeMode !== 'auto' ? purposeMode : undefined,
      quality_tier: selectedTier,
      color_preference: 'auto',
      mode: 'optimized',
    });
  }

  // Active configuration preview
  const currentTierMeta = TIERS.find(t => t.id === selectedTier) || TIERS[0];
  const isOverridden = selectedTier !== recommendedTier;

  return (
    <form className="studio-card studio-form" onSubmit={handleSubmit} noValidate aria-label="Image generation parameters">
      {/* ── 1. PURPOSE INFERENCE & RECOMMENDATION (CONSTRAINT 2) ── */}
      <div className="studio-field">
        <div className="studio-field__header-row">
          <label className="studio-field__label" htmlFor="purpose-select">
            CURRICULUM PURPOSE (CONSTRAINT 2: INFERRED &amp; MENU)
          </label>
          <span className="studio-char-count">
            Status: <strong>{purposeMode === 'auto' ? '✨ Inferred from Request' : 'Menu Selected'}</strong>
          </span>
        </div>

        {/* Purpose Menu Dropdown (Allows menu selection in addition to auto-inference) */}
        <div className="studio-select-wrapper">
          <select
            id="purpose-select"
            className="studio-select"
            value={purposeMode}
            onChange={handlePurposeSelectChange}
            disabled={isLoading}
            aria-label="Curriculum purpose menu or auto-inferred"
          >
            <option value="auto">
              ✨ Auto-Inferred: {inferredPurpose} ({recommendedTier.toUpperCase()} proposed)
            </option>
            <optgroup label="Select or Override Purpose from Menu:">
              {USE_CASES.map(uc => (
                <option key={uc.value} value={uc.value}>
                  {uc.label} &rarr; Proposes {uc.recommendedTier.toUpperCase()} Tier
                </option>
              ))}
            </optgroup>
          </select>
          <span className="studio-select-arrow" aria-hidden="true">▾</span>
        </div>

        {/* Dynamic proposed tier and explanation box */}
        <div className="studio-rec-box" role="status">
          <p className="studio-rec-text">
            <strong>Proposed Tier: {recommendedTier.toUpperCase()}</strong> (Automatic recommendation based on request) — {explanation}
          </p>
        </div>

        {/* Manual Tier Override Notice */}
        {isOverridden && (
          <div className="studio-override-alert" role="alert">
            <span className="studio-override-alert__badge">User Override</span>
            <span>
              Selected <strong>{selectedTier.toUpperCase()}</strong> differs from proposed <strong>{recommendedTier.toUpperCase()}</strong> tier. Actual generation parameters will follow your selection.
            </span>
            <button
              type="button"
              className="studio-override-reset-btn"
              onClick={() => {
                setSelectedTier(recommendedTier);
                setUserOverrodeTier(false);
              }}
              title="Reset to proposed tier"
            >
              Reset to Proposed ({recommendedTier.toUpperCase()})
            </button>
          </div>
        )}
      </div>

      {/* ── 2. NATURAL LANGUAGE PROMPT ──────────────────── */}
      <div className="studio-field">
        <div className="studio-field__header-row">
          <label className="studio-field__label" htmlFor="prompt-input">
            NATURAL-LANGUAGE IMAGE PROMPT
          </label>
          <span className="studio-char-count" aria-live="polite">
            {prompt.length} / {MAX_PROMPT} chars
          </span>
        </div>

        <textarea
          id="prompt-input"
          className={`studio-textarea ${error ? 'studio-textarea--error' : ''}`}
          rows={3}
          value={prompt}
          onChange={e => {
            if (e.target.value.length <= MAX_PROMPT) setPrompt(e.target.value);
            if (error) setError('');
          }}
          placeholder="e.g. Make a simple black-and-white colouring sheet of a butterfly for a seven-year-old."
          disabled={isLoading}
          maxLength={MAX_PROMPT}
        />

        {error && (
          <p className="studio-field-error" role="alert">
            {error}
          </p>
        )}

        {/* Clickable prompt suggestions */}
        <div className="studio-pills-row" role="group" aria-label="Suggested acceptance test prompts">
          {PROMPT_SUGGESTIONS.map(sug => (
            <button
              key={sug.label}
              type="button"
              className={`studio-pill-btn ${prompt === sug.prompt ? 'studio-pill-btn--active' : ''}`}
              onClick={() => applySuggestion(sug)}
              disabled={isLoading}
              title={sug.hint}
            >
              {sug.label}
            </button>
          ))}
        </div>

        {/* Optional Negative Prompt Toggle */}
        <div style={{ marginTop: '6px' }}>
          <button
            type="button"
            className="studio-neg-toggle"
            onClick={() => setShowNegPrompt(!showNegPrompt)}
          >
            {showNegPrompt ? '▾ Hide negative prompt' : '▸ Add optional negative prompt'}
          </button>
        </div>

        {showNegPrompt && (
          <div style={{ marginTop: '6px' }}>
            <input
              type="text"
              className="studio-select"
              style={{ fontSize: '0.84rem', padding: '8px 12px' }}
              value={negativePrompt}
              onChange={e => setNegativePrompt(e.target.value)}
              placeholder="e.g. blurry, text watermark, photographic background"
              disabled={isLoading}
            />
          </div>
        )}
      </div>

      {/* ── 3. EDITABLE QUALITY TIER OVERRIDE ───────────── */}
      <div className="studio-field">
        <div className="studio-field__header-row">
          <label className="studio-field__label">
            QUALITY / EFFORT TIER (OVERRIDE SELECTOR)
          </label>
          <span className="studio-char-count">
            Selected: <strong>{selectedTier.toUpperCase()}</strong>
          </span>
        </div>

        <div className="studio-tiers-grid" role="radiogroup" aria-label="Select generation quality tier">
          {TIERS.map(item => {
            const isSelected = selectedTier === item.id;
            const isRecommended = recommendedTier === item.id;

            return (
              <div
                key={item.id}
                role="radio"
                aria-checked={isSelected}
                tabIndex={0}
                className={`studio-tier-card ${isSelected ? 'studio-tier-card--selected' : ''}`}
                onClick={() => handleSelectTier(item.id)}
                onKeyDown={e => {
                  if (e.key === ' ' || e.key === 'Enter') {
                    e.preventDefault();
                    handleSelectTier(item.id);
                  }
                }}
              >
                <div className="studio-tier-card__header">
                  <div className="studio-tier-card__radio-row">
                    <span className={`studio-radio-circle ${isSelected ? 'studio-radio-circle--checked' : ''}`}>
                      {isSelected && <span className="studio-radio-dot" />}
                    </span>
                    <span className="studio-tier-card__title">{item.label}</span>
                  </div>

                  {isRecommended && (
                    <span className="studio-rec-pill">
                      ✓ Recommended
                    </span>
                  )}
                </div>

                <div className="studio-tier-card__footer">
                  <span className="studio-tier-card__specs">
                    {item.width}×{item.height} • {item.steps} steps
                  </span>
                  <span className={`studio-tier-card__savings ${item.id === 'eco' ? 'tier-savings--eco' : item.id === 'standard' ? 'tier-savings--standard' : 'tier-savings--baseline'}`}>
                    {item.id === 'high' ? '0% (Baseline)' : `${item.savingsPercent}% Savings`}
                  </span>
                </div>
              </div>
            );
          })}
        </div>

        {/* ── 4. APPLIED PARAMETERS PREVIEW ─────────────── */}
        <div className="studio-params-preview" aria-label="Generation parameters preview">
          <div className="studio-param-item">
            <span className="studio-param-item__label">Resolution</span>
            <span className="studio-param-item__val">{currentTierMeta.width} × {currentTierMeta.height}</span>
          </div>
          <div className="studio-param-item">
            <span className="studio-param-item__label">Inference Steps</span>
            <span className="studio-param-item__val">{currentTierMeta.steps} (Euler a)</span>
          </div>
          <div className="studio-param-item">
            <span className="studio-param-item__label">Compute Work</span>
            <span className="studio-param-item__val">{currentTierMeta.relativeUnits} units</span>
          </div>
          <div className="studio-param-item">
            <span className="studio-param-item__label">Est. Savings</span>
            <span className="studio-param-item__val" style={{ color: selectedTier === 'high' ? 'inherit' : '#16a34a' }}>
              {selectedTier === 'high' ? '0% (Baseline)' : `${currentTierMeta.savingsPercent}% vs High`}
            </span>
          </div>
        </div>
      </div>

      {/* ── 5. SUBMIT BUTTON ────────────────────────────── */}
      <button
        type="submit"
        id="generate-btn"
        className="studio-submit-btn"
        disabled={isLoading}
      >
        {isLoading ? (
          <>
            <span className="studio-spinner" aria-hidden="true" />
            <span>Generating Locally with Stable Diffusion…</span>
          </>
        ) : (
          <>
            <span className="studio-bolt-icon" aria-hidden="true">⚡</span>
            <span>Generate Local Image ({selectedTier.toUpperCase()} • {currentTierMeta.width}×{currentTierMeta.height})</span>
          </>
        )}
      </button>
    </form>
  );
}
