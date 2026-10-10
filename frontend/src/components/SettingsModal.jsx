import './SettingsModal.css';

/**
 * SettingsModal
 * Quick settings popover/modal to inspect backend provider, health status,
 * and educational district parameters.
 */
export function SettingsModal({ isOpen, onClose, providerInfo, theme, onToggleTheme }) {
  if (!isOpen) return null;

  return (
    <div className="settings-backdrop" onClick={onClose} role="dialog" aria-modal="true" aria-label="EcoGen Studio Settings">
      <div className="settings-box" onClick={e => e.stopPropagation()}>
        <div className="settings-header">
          <div className="settings-header__title-group">
            <span className="settings-icon">⚙️</span>
            <h3>Studio Settings</h3>
          </div>
          <button type="button" className="settings-close-btn" onClick={onClose} aria-label="Close settings">
            ✕
          </button>
        </div>

        <div className="settings-content">
          <div className="settings-row">
            <span className="settings-label">Active Provider</span>
            <span className="settings-value settings-value--mono">
              {providerInfo?.active_provider || 'automatic1111'}
            </span>
          </div>

          <div className="settings-row">
            <span className="settings-label">Backend Health</span>
            <span className={`settings-status-pill settings-status-pill--${providerInfo?.status}`}>
              {providerInfo?.status === 'healthy' ? '● Online (Port 8000)' : '○ Offline'}
            </span>
          </div>

          <div className="settings-row">
            <span className="settings-label">Optimization Target</span>
            <span className="settings-value">300 Schools (12,000 images/mo)</span>
          </div>

          <div className="settings-row">
            <span className="settings-label">Baseline Reference</span>
            <span className="settings-value">512x768 @ 28 Steps (1.000 unit / image)</span>
          </div>

          <div className="settings-row">
            <span className="settings-label">Interface Theme</span>
            <button type="button" className="settings-theme-btn" onClick={onToggleTheme}>
              {theme === 'dark' ? '🌙 Dark Mode' : '☀ Light Mode'} (Switch)
            </button>
          </div>
        </div>

        <div className="settings-footer">
          <button type="button" className="settings-done-btn" onClick={onClose}>
            Done
          </button>
        </div>
      </div>
    </div>
  );
}
