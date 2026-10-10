import './AppHeader.css';

export function AppHeader() {
  return (
    <header className="header" role="banner">
      <div className="header__inner">
        <div className="header__wordmark">
          <h1>
            <span className="header__wordmark-resource">Resource</span>
            <span className="header__wordmark-aware">Aware</span>
          </h1>
          <span className="header__wordmark-ai" aria-hidden="true">AI</span>
        </div>
        <p className="header__subtitle">
          Generate smarter. Use resources wisely.
        </p>
        <div className="header__badge">
          <span className="header__badge-dot" aria-hidden="true"></span>
          District Education — 300 schools
        </div>
      </div>
    </header>
  );
}
