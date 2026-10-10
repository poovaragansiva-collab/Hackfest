import './HeroSection.css';

/**
 * HeroSection
 * Clean editorial hero matching reference design:
 * "Generate Smarter. Use Less."
 */
export function HeroSection() {
  return (
    <div className="hero-studio" aria-label="ResourceAware introduction">
      <h1 className="hero-studio__title">Generate Smarter. Use Less.</h1>
      <p className="hero-studio__sub">
        Different visual tasks require different compute depths. By matching resolution and diffusion sampling
        steps to your intended educational purpose, ResourceAware right-sizes GPU inference — reducing estimated
        compute-work units by up to 86.6% compared with maximum High-tier rendering.
      </p>
    </div>
  );
}
