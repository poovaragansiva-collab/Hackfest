import { useState, useEffect } from 'react';
import {
  USE_CASES,
  REQUIREMENTS_BY_USE_CASE,
} from '../services/mockGenerationService';
import { RequirementsSelector } from './RequirementsSelector';
import { STATUS } from '../hooks/useGeneration';
import './GenerationForm.css';

const MAX_PROMPT = 500;

/**
 * GenerationForm
 * Controls all user inputs: prompt, use-case, requirements.
 * Calls onSubmit({ prompt, useCase, requirements }) when valid.
 */
export function GenerationForm({ onSubmit, status }) {
  const isLoading = status === STATUS.LOADING;

  const [prompt,       setPrompt]       = useState('');
  const [useCase,      setUseCase]      = useState(USE_CASES[0].value);
  const [requirements, setRequirements] = useState([]);
  const [errors,       setErrors]       = useState({});

  // Reset requirements when use-case changes
  useEffect(() => {
    setRequirements([]);
    setErrors(prev => ({ ...prev, requirements: undefined }));
  }, [useCase]);

  function validate() {
    const next = {};
    if (!prompt.trim()) {
      next.prompt = 'Describe the image you want to generate.';
    } else if (prompt.trim().length < 10) {
      next.prompt = 'Please be a bit more descriptive (at least 10 characters).';
    }
    if (requirements.length === 0) {
      next.requirements = 'Select at least one requirement for this use case.';
    }
    return next;
  }

  function handleSubmit(e) {
    e.preventDefault();
    const errs = validate();
    setErrors(errs);
    if (Object.keys(errs).length > 0) return;
    onSubmit({ prompt: prompt.trim(), useCase, requirements });
  }

  const currentOptions = REQUIREMENTS_BY_USE_CASE[useCase] ?? [];
  const charWarn = prompt.length > MAX_PROMPT * 0.85;

  return (
    <form
      className="form-card"
      onSubmit={handleSubmit}
      noValidate
      aria-label="Image generation settings"
    >
      <h2>Generation settings</h2>

      {/* Prompt */}
      <div className="field">
        <label htmlFor="prompt-input">
          Describe your image <span className="required" aria-hidden="true">*</span>
        </label>
        <textarea
          id="prompt-input"
          className="prompt-textarea"
          placeholder="e.g. A friendly cartoon elephant holding a pencil, suitable for primary school children"
          value={prompt}
          onChange={e => {
            if (e.target.value.length <= MAX_PROMPT) setPrompt(e.target.value);
            if (errors.prompt) setErrors(prev => ({ ...prev, prompt: undefined }));
          }}
          aria-describedby={errors.prompt ? 'prompt-error' : 'prompt-hint'}
          aria-invalid={!!errors.prompt}
          aria-required="true"
          disabled={isLoading}
          maxLength={MAX_PROMPT}
        />
        <div className="prompt-meta">
          <span id="prompt-hint" className="field-hint">
            Be specific — mention subject, style, and any key elements.
          </span>
          <span
            className={`char-count${charWarn ? ' char-count--warn' : ''}`}
            aria-live="polite"
            aria-label={`${prompt.length} of ${MAX_PROMPT} characters used`}
          >
            {prompt.length}/{MAX_PROMPT}
          </span>
        </div>
        {errors.prompt && (
          <p id="prompt-error" className="field-error" role="alert">
            {errors.prompt}
          </p>
        )}
      </div>

      {/* Intended use */}
      <div className="field">
        <label htmlFor="use-case-select">
          Intended use <span className="required" aria-hidden="true">*</span>
        </label>
        <select
          id="use-case-select"
          className="select-input"
          value={useCase}
          onChange={e => setUseCase(e.target.value)}
          disabled={isLoading}
          aria-required="true"
        >
          {USE_CASES.map(u => (
            <option key={u.value} value={u.value}>{u.label}</option>
          ))}
        </select>
        <span className="field-hint">
          Chooses a resource profile appropriate for how the image will be used.
        </span>
      </div>

      {/* Requirements */}
      <div className="field">
        <RequirementsSelector
          options={currentOptions}
          selected={requirements}
          onChange={setRequirements}
          error={errors.requirements}
        />
      </div>

      {/* Submit */}
      <button
        type="submit"
        id="generate-btn"
        className="btn-generate"
        disabled={isLoading}
        aria-busy={isLoading}
      >
        {isLoading ? (
          <>
            <span className="spinner" aria-hidden="true" />
            Generating…
          </>
        ) : (
          'Generate image'
        )}
      </button>
    </form>
  );
}
