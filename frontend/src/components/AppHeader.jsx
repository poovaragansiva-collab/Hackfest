import { useState, useEffect } from 'react';
import { fetchHealth } from '../services/apiService';
import { SettingsModal } from './SettingsModal';
import './AppHeader.css';

/**
 * AppHeader
 * Header matching the reference screenshot design:
 * [EG] EcoGen AI - Resource-Aware Studio
 * Nav: Studio | Resource Telemetry | Recent | Theme / Settings
 */
export function AppHeader({
  theme = 'light',
  onToggleTheme,
  activeTab = 'studio',
  onSelectTab,
  historyCount = 0,
}) {
  const [providerInfo, setProviderInfo] = useState({ status: 'checking', active_provider: '' });
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);

  useEffect(() => {
    let mounted = true;
    fetchHealth().then(data => {
      if (mounted) {
        setProviderInfo(data);
      }
    });
    return () => {
      mounted = false;
    };
  }, []);

  let badgeLabel = 'Checking…';
  let badgeStatusClass = 'header__status--checking';

  if (providerInfo.status === 'healthy') {
    badgeStatusClass = 'header__status--healthy';
    if (providerInfo.active_provider === 'automatic1111' || providerInfo.active_provider === 'local') {
      badgeLabel = 'Local SD WebUI';
    } else if (providerInfo.active_provider === 'mock') {
      badgeLabel = 'Demo Mode';
    } else if (providerInfo.active_provider === 'openrouter') {
      badgeLabel = 'OpenRouter';
    } else if (providerInfo.active_provider === 'google') {
      badgeLabel = 'Google Gemini';
    } else if (providerInfo.active_provider === 'huggingface') {
      badgeLabel = 'Hugging Face';
    } else {
      badgeLabel = providerInfo.active_provider;
    }
  } else if (providerInfo.status === 'offline') {
    badgeStatusClass = 'header__status--offline';
    badgeLabel = 'Offline';
  }

  return (
    <>
      <header className="header" role="banner">
        <div className="header__inner">
          {/* Brand: [EG] EcoGen AI Resource-Aware Studio */}
          <div className="header__brand" onClick={() => onSelectTab && onSelectTab('studio')} style={{ cursor: 'pointer' }}>
            <div className="header__logo-icon" aria-hidden="true">
              <span>EG</span>
            </div>
            <div className="header__brand-text">
              <span className="header__brand-name">
                EcoGen <span className="header__brand-highlight">AI</span>
              </span>
              <span className="header__brand-tag">Resource-Aware Studio · ROTCREW</span>
            </div>
          </div>

          {/* Center Navigation Links matching reference screenshot */}
          <nav className="header__nav" aria-label="Main view switcher">
            <button
              type="button"
              className={`nav-link-btn ${activeTab === 'studio' ? 'nav-link-btn--active' : ''}`}
              onClick={() => onSelectTab && onSelectTab('studio')}
              aria-current={activeTab === 'studio' ? 'page' : undefined}
            >
              Studio
            </button>
            <button
              type="button"
              className={`nav-link-btn ${activeTab === 'analytics' ? 'nav-link-btn--active' : ''}`}
              onClick={() => onSelectTab && onSelectTab('analytics')}
              aria-current={activeTab === 'analytics' ? 'page' : undefined}
            >
              Resource Telemetry
            </button>
            <button
              type="button"
              className={`nav-link-btn ${activeTab === 'history' ? 'nav-link-btn--active' : ''}`}
              onClick={() => onSelectTab && onSelectTab('history')}
              aria-current={activeTab === 'history' ? 'page' : undefined}
            >
              Recent
              {historyCount > 0 && <span className="nav-count-badge">{historyCount}</span>}
            </button>
          </nav>

          {/* Right Controls: Engine indicator + Divider + Settings + Theme Switcher */}
          <div className="header__controls">
            <div 
              className={`header__status ${badgeStatusClass}`}
              title={`Active generator: ${providerInfo.active_provider || 'unknown'}`}
              role="status"
              aria-live="polite"
            >
              <span className="header__status-dot" aria-hidden="true" />
              <span className="header__status-text">{badgeLabel}</span>
            </div>

            <div className="header__divider" aria-hidden="true" />

            {/* Settings button */}
            <button
              type="button"
              id="settings-modal-btn"
              className="header__settings-btn"
              onClick={() => setIsSettingsOpen(true)}
              aria-label="Open studio settings"
              title="Studio Settings"
            >
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                <circle cx="12" cy="12" r="3" />
                <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z" />
              </svg>
            </button>

            {/* Theme / Mode Switcher */}
            <button
              type="button"
              id="theme-toggle-btn"
              className="header__settings-btn"
              onClick={onToggleTheme}
              aria-label={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
              title={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
            >
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                {theme === 'dark' ? (
                  <>
                    <circle cx="12" cy="12" r="5" />
                    <line x1="12" y1="1" x2="12" y2="3" />
                    <line x1="12" y1="21" x2="12" y2="23" />
                    <line x1="4.22" y1="4.22" x2="5.64" y2="5.64" />
                    <line x1="18.36" y1="18.36" x2="19.78" y2="19.78" />
                    <line x1="1" y1="12" x2="3" y2="12" />
                    <line x1="21" y1="12" x2="23" y2="12" />
                    <line x1="4.22" y1="19.78" x2="5.64" y2="18.36" />
                    <line x1="18.36" y1="5.64" x2="19.78" y2="4.22" />
                  </>
                ) : (
                  <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
                )}
              </svg>
              <span>{theme === 'dark' ? 'Light' : 'Dark'}</span>
            </button>
          </div>
        </div>
      </header>

      {/* Settings Modal */}
      <SettingsModal
        isOpen={isSettingsOpen}
        onClose={() => setIsSettingsOpen(false)}
        providerInfo={providerInfo}
        theme={theme}
        onToggleTheme={onToggleTheme}
      />
    </>
  );
}
