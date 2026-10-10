import './HeroSection.css';

export function HeroSection({ onStart }) {
  return (
    <section className="hero" aria-label="Smart Imaging introduction">
      {/* Animated background */}
      <div className="hero__bg" aria-hidden="true">
        <div className="hero__orb hero__orb--1" />
        <div className="hero__orb hero__orb--2" />
        <div className="hero__orb hero__orb--3" />
        <div className="hero__grid" />
      </div>

      <div className="hero__inner">
        <div className="hero__eyebrow stagger" style={{ '--i': 0 }}>
          <span className="hero__eyebrow-dot" aria-hidden="true" />
          Resource-aware image generation
        </div>

        <h2 className="hero__heading stagger" style={{ '--i': 1 }}>
          <span className="hero__heading-line1">Create Smarter.</span>
          <span className="hero__heading-line2">Generate Responsibly.</span>
        </h2>

        <p className="hero__sub stagger" style={{ '--i': 2 }}>
          Choose the right effort for every image and understand the resources involved —
          without guesswork or invented numbers.
        </p>

        <button
          type="button"
          id="hero-start-btn"
          className="hero__cta stagger"
          style={{ '--i': 3 }}
          onClick={onStart}
          aria-label="Start creating — scroll to generator"
        >
          Start creating
          <svg
            className="hero__cta-arrow"
            width="16"
            height="16"
            viewBox="0 0 16 16"
            fill="none"
            aria-hidden="true"
          >
            <path d="M8 3v10M3 9l5 5 5-5" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
        </button>
      </div>
    </section>
  );
}
