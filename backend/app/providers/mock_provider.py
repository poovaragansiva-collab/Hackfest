import urllib.parse
from .base import BaseImageProvider
from ..schemas.request import ImageGenerationRequest, IntendedUseEnum
from ..schemas.response import AppliedConfiguration, ImageData


class DevMockProvider(BaseImageProvider):
    """Clearly labelled development mock provider for offline end-to-end testing."""

    @property
    def provider_id(self) -> str:
        return "mock"

    def is_configured(self) -> bool:
        return True

    async def generate_image(
        self,
        request: ImageGenerationRequest,
        config: AppliedConfiguration,
    ) -> ImageData:
        # Determine dimensions from config
        parts = config.effective_resolution.split("x")
        width = int(parts[0]) if len(parts) == 2 else 1024
        height = int(parts[1]) if len(parts) == 2 else 1024

        svg_content = self._generate_labeled_svg(
            prompt=request.prompt,
            purpose=request.intended_use.value,
            tier=config.quality_tier,
            resolution=config.effective_resolution,
            color_mode=config.color_mode,
            width=width,
            height=height,
        )

        encoded_svg = urllib.parse.quote(svg_content)
        data_uri = f"data:image/svg+xml;utf8,{encoded_svg}"

        return ImageData(
            url=data_uri,
            format="svg",
            width=width,
            height=height,
        )

    def _generate_labeled_svg(
        self,
        prompt: str,
        purpose: str,
        tier: str,
        resolution: str,
        color_mode: str,
        width: int,
        height: int,
    ) -> str:
        safe_prompt = prompt[:90] + ("..." if len(prompt) > 90 else "")

        if color_mode == "monochrome_line_art":
            bg_color = "#FFFFFF"
            accent_color = "#111827"
            sub_color = "#4B5563"
            illustration = f"""
            <rect x="150" y="240" width="{width - 300}" height="{height - 480}" rx="16" fill="none" stroke="{accent_color}" stroke-width="8" stroke-dasharray="16,8" />
            <circle cx="{width // 2}" cy="{height // 2 - 40}" r="140" fill="none" stroke="{accent_color}" stroke-width="10" />
            <path d="M {width // 2 - 80} {height // 2 + 10} Q {width // 2} {height // 2 + 80} {width // 2 + 80} {height // 2 + 10}" fill="none" stroke="{accent_color}" stroke-width="8" />
            <text x="{width // 2}" y="{height // 2 + 120}" font-family="Arial, sans-serif" font-size="28" font-weight="bold" fill="{accent_color}" text-anchor="middle">BLACK &amp; WHITE COLORING CONTOUR</text>
            """
        elif purpose == "flashcard":
            bg_color = "#F0FDF4"
            accent_color = "#166534"
            sub_color = "#15803D"
            illustration = f"""
            <rect x="100" y="200" width="{width - 200}" height="{height - 400}" rx="24" fill="#FFFFFF" stroke="{accent_color}" stroke-width="6" />
            <circle cx="{width // 2}" cy="{height // 2 - 50}" r="120" fill="#DCFCE7" stroke="{accent_color}" stroke-width="6" />
            <text x="{width // 2}" y="{height // 2 - 40}" font-family="Arial, sans-serif" font-size="36" font-weight="bold" fill="{accent_color}" text-anchor="middle">STUDY FLASHCARD</text>
            <text x="{width // 2}" y="{height // 2 + 80}" font-family="Arial, sans-serif" font-size="24" fill="{sub_color}" text-anchor="middle">Clean educational focal subject</text>
            """
        else:
            # Full color / Poster / Banner
            bg_color = "#0F172A"
            accent_color = "#38BDF8"
            sub_color = "#94A3B8"
            illustration = f"""
            <defs>
              <linearGradient id="grad" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stop-color="#3B82F6" />
                <stop offset="50%" stop-color="#8B5CF6" />
                <stop offset="100%" stop-color="#EC4899" />
              </linearGradient>
            </defs>
            <rect x="80" y="180" width="{width - 160}" height="{height - 360}" rx="24" fill="url(#grad)" opacity="0.85" />
            <circle cx="{width // 2}" cy="{height // 2 - 50}" r="150" fill="#FFFFFF" opacity="0.2" />
            <text x="{width // 2}" y="{height // 2 - 40}" font-family="Arial, sans-serif" font-size="36" font-weight="bold" fill="#FFFFFF" text-anchor="middle">HIGH-FIDELITY DISTRICT POSTER</text>
            """

        return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="100%" height="100%">
  <rect width="{width}" height="{height}" fill="{bg_color}" />
  
  <!-- Header Banner -->
  <rect x="0" y="0" width="{width}" height="90" fill="#1E293B" />
  <text x="30" y="55" font-family="Arial, sans-serif" font-size="24" font-weight="bold" fill="#F8FAFC">[DEV MOCK PREVIEW] Resource-Aware Generation</text>
  <rect x="{width - 240}" y="25" width="210" height="40" rx="8" fill="#F59E0B" />
  <text x="{width - 135}" y="50" font-family="Arial, sans-serif" font-size="16" font-weight="bold" fill="#000000" text-anchor="middle">OFFLINE MOCK</text>

  <!-- Illustration Area -->
  {illustration}

  <!-- Footer Specs Card -->
  <rect x="40" y="{height - 140}" width="{width - 80}" height="100" rx="12" fill="#1E293B" opacity="0.95" />
  <text x="60" y="{height - 100}" font-family="Arial, sans-serif" font-size="20" fill="#F8FAFC"><b>Prompt:</b> {safe_prompt}</text>
  <text x="60" y="{height - 65}" font-family="Arial, sans-serif" font-size="18" fill="#94A3B8">Purpose: <tspan fill="#38BDF8">{purpose}</tspan> | Tier: <tspan fill="#F59E0B">{tier.upper()}</tspan> | Res: {resolution} | Mode: {color_mode}</text>
</svg>"""
