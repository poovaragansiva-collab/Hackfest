import { STATUS } from '../hooks/useGeneration';
import './ResultPanel.css';

/**
 * ResultPanel
 * Renders four states: idle | loading | error | success.
 * All cost/usage data is deliberately marked unavailable until
 * a real backend integration is complete.
 */
export function ResultPanel({ status, result, error, onReset }) {
  if (status === STATUS.IDLE) {
    return <IdleState />;
  }
  if (status === STATUS.LOADING) {
    return <LoadingState />;
  }
  if (status === STATUS.ERROR) {
    return <ErrorState message={error} onRetry={onReset} />;
  }
  if (status === STATUS.SUCCESS && result) {
    return <SuccessState result={result} />;
  }
  return <IdleState />;
}

/* ── Idle ────────────────────────────────────────────────── */
function IdleState() {
  return (
    <div className="result-panel result-panel--empty" role="status" aria-label="No result yet">
      <div className="empty-icon" aria-hidden="true">🖼️</div>
      <p className="empty-title">Your image appears here</p>
      <p className="empty-body">
        Fill in the settings on the left and select the requirements that match
        how you'll use the image.
      </p>
    </div>
  );
}

/* ── Loading ─────────────────────────────────────────────── */
function LoadingState() {
  return (
    <div
      className="result-panel result-panel--loading"
      role="status"
      aria-live="polite"
      aria-label="Generating image, please wait"
    >
      <div className="loading-ring" aria-hidden="true" />
      <p className="loading-label">Selecting resource profile…</p>
      <p className="loading-profile-hint">Applying use-case optimisations</p>
    </div>
  );
}

/* ── Error ───────────────────────────────────────────────── */
function ErrorState({ message, onRetry }) {
  return (
    <div className="result-panel result-panel--error" role="alert" aria-label="Generation failed">
      <div className="error-box">
        <div className="error-box__header">
          <svg
            className="error-box__icon"
            viewBox="0 0 20 20"
            fill="currentColor"
            aria-hidden="true"
          >
            <path
              fillRule="evenodd"
              d="M10 18a8 8 0 100-16 8 8 0 000 16zm-.75-9.25a.75.75 0 011.5 0v3a.75.75 0 01-1.5 0v-3zm.75 6a.75.75 0 100-1.5.75.75 0 000 1.5z"
              clipRule="evenodd"
            />
          </svg>
          Generation failed
        </div>
        <p className="error-box__message">{message}</p>
        <button
          type="button"
          id="retry-btn"
          className="btn-retry"
          onClick={onRetry}
        >
          Try again
        </button>
      </div>
    </div>
  );
}

/* ── Success ─────────────────────────────────────────────── */
function SuccessState({ result }) {
  return (
    <div className="result-panel result-panel--success" aria-label="Generation result">

      {/* Mandatory demo disclaimer */}
      <div className="demo-banner" role="note" aria-label="Simulated demo notice">
        <svg width="14" height="14" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
          <path fillRule="evenodd" d="M8.485 2.495c.673-1.167 2.357-1.167 3.03 0l6.28 10.875c.673 1.167-.17 2.625-1.516 2.625H3.72c-1.347 0-2.189-1.458-1.515-2.625L8.485 2.495zM10 5a.75.75 0 01.75.75v3.5a.75.75 0 01-1.5 0v-3.5A.75.75 0 0110 5zm0 9a1 1 0 100-2 1 1 0 000 2z" clipRule="evenodd" />
        </svg>
        SIMULATED DEMO — NOT A REAL API RESULT
      </div>

      {/* Image preview */}
      <div className="result-image-wrap">
        <img
          className="result-image"
          src={result.imageUrl}
          alt={`Simulated preview for: ${result.prompt}`}
        />
      </div>

      <div className="result-body">

        {/* Generation profile */}
        <div className="result-section">
          <span className="result-section__heading">Generation profile</span>
          <div className="profile-chip">
            <span aria-hidden="true">⚙️</span>
            {result.profile}
          </div>
          <p className="result-section__content">{result.profileDescription}</p>
        </div>

        <hr className="result-divider" />

        {/* Decision explanation */}
        <div className="result-section">
          <span className="result-section__heading">How this profile was selected</span>
          <ul className="decision-steps" aria-label="Profile selection reasoning">
            {result.decisionSteps.map((step, i) => (
              <li key={i}>{step}</li>
            ))}
          </ul>
        </div>

        <hr className="result-divider" />

        {/* Cost / usage — deliberately unavailable */}
        <div className="result-section">
          <span className="result-section__heading">Cost &amp; usage</span>
          <div
            className="unavailable-note"
            role="note"
            aria-label="Cost and usage data unavailable"
          >
            <svg width="14" height="14" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
              <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a.75.75 0 000 1.5h.253a.25.25 0 01.244.304l-.459 2.066A1.75 1.75 0 0010.747 15H11a.75.75 0 000-1.5h-.253a.25.25 0 01-.244-.304l.459-2.066A1.75 1.75 0 009.253 9H9z" clipRule="evenodd" />
            </svg>
            Actual cost and token usage are unavailable until a real provider
            integration is connected. No estimates are shown to avoid misleading figures.
          </div>
        </div>

      </div>
    </div>
  );
}
