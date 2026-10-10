import urllib.parse
from .base import BaseImageProvider
from ..schemas.request import ImageGenerationRequest
from ..schemas.response import AppliedConfiguration, ImageData
from ..services.resource_estimator import (
    get_tier_resource_units,
    calculate_resource_savings_percent,
)


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
        parts = config.effective_resolution.split("x")
        width = int(parts[0]) if len(parts) == 2 else 512
        height = int(parts[1]) if len(parts) == 2 else 512

        purpose_str = request.intended_use.value if request.intended_use else "general_purpose"
        svg_content = self._generate_labeled_svg(
            prompt=request.prompt,
            purpose=purpose_str,
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
        safe_prompt = prompt[:80] + ("..." if len(prompt) > 80 else "")
        units = get_tier_resource_units(tier)
        savings = calculate_resource_savings_percent(tier)
        p_lower = prompt.lower()
        purpose_lower = purpose.lower()
        is_elephant = "elephant" in p_lower

        # ======================================================================
        # THREE DISTINCT TIERS (ECO vs STANDARD vs HIGH QUALITY)
        # ======================================================================
        is_turtle = "turtle" in p_lower
        is_elephant = "elephant" in p_lower
        tier_norm = (tier or "eco").lower()

        # ----------------------------------------------------------------------
        # TIER 1: ECO MODE (1 Unit, 75% Savings, 15 Steps)
        # Pure Black & White Line Art, bold outline, zero fills, zero shading
        # ----------------------------------------------------------------------
        if tier_norm == "eco" or color_mode == "monochrome_line_art":
            bg_color = "#FFFFFF"
            stroke_col = "#111827"
            banner_bg = "#F3F4F6"
            banner_text = "#1F2937"

            is_turtle = "turtle" in p_lower

            if is_turtle:
                illustration = f"""
                <!-- Child-friendly Coloring Sheet: Sea Turtle Line Art -->
                <g stroke="{stroke_col}" stroke-width="6" stroke-linecap="round" stroke-linejoin="round" fill="none">
                    <!-- Turtle Oval Shell -->
                    <ellipse cx="{width * 0.50}" cy="{height * 0.48}" rx="{width * 0.22}" ry="{height * 0.17}" fill="#FFFFFF" />
                    <!-- Shell Scutes / Hexagonal Pattern -->
                    <polygon points="{width * 0.50},{height * 0.40} {width * 0.56},{height * 0.44} {width * 0.56},{height * 0.52} {width * 0.50},{height * 0.56} {width * 0.44},{height * 0.52} {width * 0.44},{height * 0.44}" />
                    <line x1="{width * 0.50}" y1="{height * 0.31}" x2="{width * 0.50}" y2="{height * 0.40}" />
                    <line x1="{width * 0.56}" y1="{height * 0.44}" x2="{width * 0.70}" y2="{height * 0.42}" />
                    <line x1="{width * 0.56}" y1="{height * 0.52}" x2="{width * 0.69}" y2="{height * 0.55}" />
                    <line x1="{width * 0.50}" y1="{height * 0.56}" x2="{width * 0.50}" y2="{height * 0.65}" />
                    <line x1="{width * 0.44}" y1="{height * 0.52}" x2="{width * 0.31}" y2="{height * 0.55}" />
                    <line x1="{width * 0.44}" y1="{height * 0.44}" x2="{width * 0.30}" y2="{height * 0.42}" />
                    <!-- Front Flippers -->
                    <path d="M {width * 0.34} {height * 0.40} C {width * 0.20} {height * 0.34}, {width * 0.14} {height * 0.46}, {width * 0.29} {height * 0.49}" fill="#FFFFFF" />
                    <path d="M {width * 0.66} {height * 0.40} C {width * 0.80} {height * 0.34}, {width * 0.86} {height * 0.46}, {width * 0.71} {height * 0.49}" fill="#FFFFFF" />
                    <!-- Rear Flippers -->
                    <path d="M {width * 0.36} {height * 0.60} C {width * 0.28} {height * 0.65}, {width * 0.28} {height * 0.71}, {width * 0.39} {height * 0.65}" fill="#FFFFFF" />
                    <path d="M {width * 0.64} {height * 0.60} C {width * 0.72} {height * 0.65}, {width * 0.72} {height * 0.71}, {width * 0.61} {height * 0.65}" fill="#FFFFFF" />
                    <!-- Cute Head -->
                    <ellipse cx="{width * 0.50}" cy="{height * 0.26}" rx="{width * 0.08}" ry="{height * 0.07}" fill="#FFFFFF" />
                    <!-- Smiling Eyes -->
                    <circle cx="{width * 0.46}" cy="{height * 0.25}" r="5" fill="{stroke_col}" />
                    <circle cx="{width * 0.54}" cy="{height * 0.25}" r="5" fill="{stroke_col}" />
                    <path d="M {width * 0.47} {height * 0.29} Q {width * 0.50} {height * 0.32} {width * 0.53} {height * 0.29}" />
                    <!-- Cute Tail -->
                    <polygon points="{width * 0.48},{height * 0.65} {width * 0.52},{height * 0.65} {width * 0.50},{height * 0.71}" fill="#FFFFFF" />
                    <!-- Gentle Water Bubbles for Kids -->
                    <circle cx="{width * 0.20}" cy="{height * 0.24}" r="10" stroke-dasharray="4,2" />
                    <circle cx="{width * 0.25}" cy="{height * 0.18}" r="6" stroke-dasharray="4,2" />
                    <circle cx="{width * 0.78}" cy="{height * 0.22}" r="12" stroke-dasharray="4,2" />
                </g>
                <text x="{width // 2}" y="{height * 0.82}" font-family="system-ui, sans-serif" font-size="20" font-weight="700" fill="{stroke_col}" text-anchor="middle" letter-spacing="1">SEA TURTLE COLORING OUTLINE</text>
                <text x="{width // 2}" y="{height * 0.86}" font-family="system-ui, sans-serif" font-size="14" fill="#6B7280" text-anchor="middle">Pure black &amp; white line art • Bold contours • Zero fills</text>
                """
            elif is_elephant:
                illustration = f"""
                <!-- Child-friendly Coloring Sheet: Elephant Line Art -->
                <g stroke="{stroke_col}" stroke-width="6" stroke-linecap="round" stroke-linejoin="round" fill="none">
                    <!-- Body & Back -->
                    <ellipse cx="{width * 0.55}" cy="{height * 0.52}" rx="{width * 0.24}" ry="{height * 0.18}" fill="#FFFFFF" />
                    <!-- Back Leg Left -->
                    <rect x="{width * 0.65}" y="{height * 0.56}" width="{width * 0.08}" height="{height * 0.18}" rx="8" fill="#FFFFFF" />
                    <!-- Back Leg Right -->
                    <rect x="{width * 0.53}" y="{height * 0.56}" width="{width * 0.08}" height="{height * 0.18}" rx="8" fill="#FFFFFF" />
                    <!-- Front Leg Left -->
                    <rect x="{width * 0.42}" y="{height * 0.56}" width="{width * 0.08}" height="{height * 0.18}" rx="8" fill="#FFFFFF" />
                    <!-- Head -->
                    <circle cx="{width * 0.35}" cy="{height * 0.44}" r="{width * 0.13}" fill="#FFFFFF" />
                    <!-- Large Ear -->
                    <path d="M {width * 0.34} {height * 0.35} C {width * 0.44} {height * 0.32}, {width * 0.48} {height * 0.52}, {width * 0.36} {height * 0.54} Z" fill="#FFFFFF" />
                    <!-- Curling Trunk -->
                    <path d="M {width * 0.28} {height * 0.46} C {width * 0.20} {height * 0.50}, {width * 0.16} {height * 0.38}, {width * 0.24} {height * 0.34} C {width * 0.26} {height * 0.33}, {width * 0.27} {height * 0.38}, {width * 0.25} {height * 0.40}" />
                    <!-- Cute Eye -->
                    <circle cx="{width * 0.31}" cy="{height * 0.40}" r="6" fill="{stroke_col}" />
                    <circle cx="{width * 0.30}" cy="{height * 0.39}" r="2" fill="#FFFFFF" />
                    <!-- Gentle Smile -->
                    <path d="M {width * 0.28} {height * 0.48} Q {width * 0.31} {height * 0.50} {width * 0.33} {height * 0.48}" />
                    <!-- Little Tail -->
                    <path d="M {width * 0.78} {height * 0.50} Q {width * 0.83} {height * 0.54} {width * 0.81} {height * 0.62}" />
                    <!-- Ground Outline (clean grass tufts) -->
                    <path d="M {width * 0.15} {height * 0.74} L {width * 0.85} {height * 0.74}" stroke-dasharray="12,6" />
                    <path d="M {width * 0.20} {height * 0.74} L {width * 0.22} {height * 0.70} L {width * 0.24} {height * 0.74}" />
                    <path d="M {width * 0.75} {height * 0.74} L {width * 0.77} {height * 0.70} L {width * 0.79} {height * 0.74}" />
                </g>
                <text x="{width // 2}" y="{height * 0.82}" font-family="system-ui, sans-serif" font-size="20" font-weight="700" fill="{stroke_col}" text-anchor="middle" letter-spacing="1">CHILD-FRIENDLY COLORING OUTLINE</text>
                <text x="{width // 2}" y="{height * 0.86}" font-family="system-ui, sans-serif" font-size="14" fill="#6B7280" text-anchor="middle">Pure black &amp; white line art • Bold contours • Zero fills</text>
                """
            else:
                illustration = f"""
                <g stroke="{stroke_col}" stroke-width="5" stroke-linecap="round" fill="none">
                    <circle cx="{width // 2}" cy="{height // 2 - 20}" r="{min(width, height) * 0.22}" fill="#FFFFFF" />
                    <path d="M {width // 2 - 50} {height // 2 - 20} Q {width // 2} {height // 2 + 30} {width // 2 + 50} {height // 2 - 20}" />
                    <circle cx="{width // 2 - 30}" cy="{height // 2 - 50}" r="8" fill="{stroke_col}" />
                    <circle cx="{width // 2 + 30}" cy="{height // 2 - 50}" r="8" fill="{stroke_col}" />
                </g>
                <text x="{width // 2}" y="{height * 0.82}" font-family="system-ui, sans-serif" font-size="20" font-weight="700" fill="{stroke_col}" text-anchor="middle">CLEAN COLORING OUTLINE</text>
                <text x="{width // 2}" y="{height * 0.86}" font-family="system-ui, sans-serif" font-size="14" fill="#6B7280" text-anchor="middle">Monochrome outline art • High-contrast printable</text>
                """

        # 2. Flashcard: Crisp educational card, clear central subject, vocabulary text
        elif "flashcard" in purpose_lower:
            bg_color = "#F0FDF4"
            banner_bg = "#DCFCE7"
            banner_text = "#166534"
            card_x = width * 0.12
            card_y = height * 0.22
            card_w = width * 0.76
            card_h = height * 0.58

            subject_title = "ELEPHANT" if is_elephant else "STUDY VOCABULARY"
            pronunciation = "/ˈɛl.ɪ.fənt/" if is_elephant else "/ˈstʌd.i/"
            definition = "A massive herbivore with a prehensile trunk" if is_elephant else "Focused single subject study concept"

            illustration = f"""
            <rect x="{card_x}" y="{card_y}" width="{card_w}" height="{card_h}" rx="20" fill="#FFFFFF" stroke="#16A34A" stroke-width="3" filter="drop-shadow(0 4px 6px rgba(0,0,0,0.05))" />
            <circle cx="{width // 2}" cy="{height * 0.42}" r="{min(width, height) * 0.14}" fill="#DCFCE7" stroke="#16A34A" stroke-width="2" />
            <!-- Centered Flashcard Icon -->
            <path d="M {width // 2 - 30} {height * 0.44} C {width // 2 - 20} {height * 0.38}, {width // 2 + 20} {height * 0.38}, {width // 2 + 30} {height * 0.44}" stroke="#15803D" stroke-width="4" fill="none" stroke-linecap="round" />
            <circle cx="{width // 2 - 15}" cy="{height * 0.41}" r="4" fill="#15803D" />
            <circle cx="{width // 2 + 15}" cy="{height * 0.41}" r="4" fill="#15803D" />
            
            <text x="{width // 2}" y="{height * 0.60}" font-family="system-ui, sans-serif" font-size="28" font-weight="800" fill="#166534" text-anchor="middle" letter-spacing="2">{subject_title}</text>
            <text x="{width // 2}" y="{height * 0.65}" font-family="system-ui, sans-serif" font-size="16" fill="#15803D" text-anchor="middle" font-style="italic">{pronunciation}</text>
            <text x="{width // 2}" y="{height * 0.72}" font-family="system-ui, sans-serif" font-size="14" fill="#4B5563" text-anchor="middle">{definition}</text>
            """

        # 3. Worksheet illustration: Technical diagram box, clean lines, instructional annotation
        elif "worksheet" in purpose_lower:
            bg_color = "#F8FAFC"
            banner_bg = "#E2E8F0"
            banner_text = "#1E293B"
            diag_x = width * 0.10
            diag_y = height * 0.22
            diag_w = width * 0.80
            diag_h = height * 0.58

            illustration = f"""
            <rect x="{diag_x}" y="{diag_y}" width="{diag_w}" height="{diag_h}" rx="12" fill="#FFFFFF" stroke="#64748B" stroke-width="2" stroke-dasharray="6,4" />
            <rect x="{diag_x + 15}" y="{diag_y + 15}" width="{diag_w - 30}" height="32" rx="6" fill="#F1F5F9" />
            <text x="{diag_x + 25}" y="{diag_y + 36}" font-family="system-ui, sans-serif" font-size="14" font-weight="700" fill="#334155">FIGURE 1.1 — CURRICULUM WORKSHEET DIAGRAM</text>
            
            <!-- Technical Central Subject -->
            <circle cx="{width // 2}" cy="{height * 0.48}" r="{min(width, height) * 0.16}" fill="#F8FAFC" stroke="#0284C7" stroke-width="3" />
            
            <!-- Annotation pointers -->
            <line x1="{width * 0.32}" y1="{height * 0.42}" x2="{width * 0.20}" y2="{height * 0.36}" stroke="#0284C7" stroke-width="2" />
            <rect x="{width * 0.12}" y="{height * 0.33}" width="{width * 0.16}" height="24" rx="4" fill="#E0F2FE" />
            <text x="{width * 0.20}" y="{height * 0.35}" font-family="system-ui, sans-serif" font-size="11" font-weight="600" fill="#0369A1" text-anchor="middle">ANATOMY [A]</text>
            
            <line x1="{width * 0.68}" y1="{height * 0.52}" x2="{width * 0.80}" y2="{height * 0.58}" stroke="#0284C7" stroke-width="2" />
            <rect x="{width * 0.72}" y="{height * 0.57}" width="{width * 0.16}" height="24" rx="4" fill="#E0F2FE" />
            <text x="{width * 0.80}" y="{height * 0.59}" font-family="system-ui, sans-serif" font-size="11" font-weight="600" fill="#0369A1" text-anchor="middle">FUNCTION [B]</text>
            
            <text x="{width // 2}" y="{height * 0.74}" font-family="system-ui, sans-serif" font-size="14" fill="#475569" text-anchor="middle">Activity: Label key components using vocabulary terms above.</text>
            """

        # 4. Educational poster & Premium poster: Rich colors, vivid background, high visual fidelity
        else:
            is_premium = "premium" in purpose_lower or tier == "high_quality"
            bg_color = "#0B0F19"
            banner_bg = "#1E293B"
            banner_text = "#F8FAFC"
            poster_x = width * 0.08
            poster_y = height * 0.20
            poster_w = width * 0.84
            poster_h = height * 0.62

            grad_stops = """
                <stop offset="0%" stop-color="#3B82F6" />
                <stop offset="45%" stop-color="#8B5CF6" />
                <stop offset="100%" stop-color="#EC4899" />
            """ if not is_premium else """
                <stop offset="0%" stop-color="#1E3A8A" />
                <stop offset="35%" stop-color="#4338CA" />
                <stop offset="70%" stop-color="#7C3AED" />
                <stop offset="100%" stop-color="#DB2777" />
            """

            badge_title = "PREMIUM PRINT-READY POSTER" if is_premium else "CLASSROOM EDUCATIONAL POSTER"
            subject_headline = "SAVANNAH WILDLIFE: AFRICAN ELEPHANT" if is_elephant else "ADVANCED VISUAL LEARNING POSTER"

            illustration = f"""
            <defs>
              <linearGradient id="posterGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                {grad_stops}
              </linearGradient>
            </defs>
            <rect x="{poster_x}" y="{poster_y}" width="{poster_w}" height="{poster_h}" rx="20" fill="url(#posterGrad)" stroke="#60A5FA" stroke-width="2" />
            
            <!-- Graphic Aura Elements -->
            <circle cx="{width // 2}" cy="{height * 0.46}" r="{min(width, height) * 0.18}" fill="#FFFFFF" opacity="0.15" />
            <circle cx="{width // 2}" cy="{height * 0.46}" r="{min(width, height) * 0.12}" fill="#FFFFFF" opacity="0.25" />
            
            <!-- Poster Header Ribbon -->
            <rect x="{poster_x + 20}" y="{poster_y + 20}" width="{poster_w - 40}" height="32" rx="6" fill="#000000" opacity="0.35" />
            <text x="{width // 2}" y="{poster_y + 42}" font-family="system-ui, sans-serif" font-size="14" font-weight="700" fill="#F8FAFC" text-anchor="middle" letter-spacing="2">{badge_title}</text>
            
            <!-- Main Focal Title -->
            <text x="{width // 2}" y="{height * 0.63}" font-family="system-ui, sans-serif" font-size="24" font-weight="800" fill="#FFFFFF" text-anchor="middle">{subject_headline}</text>
            <text x="{width // 2}" y="{height * 0.68}" font-family="system-ui, sans-serif" font-size="14" fill="#E2E8F0" text-anchor="middle">Full Color Gamut • High Resolution Rendering • Rich Contrast</text>
            
            <!-- Quality Badge -->
            <rect x="{width // 2 - 90}" y="{height * 0.72}" width="180" height="28" rx="14" fill="#F59E0B" />
            <text x="{width // 2}" y="{height * 0.74}" font-family="system-ui, sans-serif" font-size="12" font-weight="800" fill="#000000" text-anchor="middle">TIER: {tier.upper()} ({units} UNITS)</text>
            """

        # Header watermark banner: "Demo preview — not AI-generated"
        banner_height = 80
        footer_height = 90
        return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="100%" height="100%">
  <rect width="{width}" height="{height}" fill="{bg_color}" />

  <!-- PROMINENT DEMO BANNER -->
  <rect x="0" y="0" width="{width}" height="{banner_height}" fill="#FEF3C7" stroke="#F59E0B" stroke-width="2" />
  <rect x="16" y="16" width="{width - 32}" height="{banner_height - 32}" rx="8" fill="#FDE68A" />
  <text x="{width // 2}" y="42" font-family="system-ui, -apple-system, sans-serif" font-size="18" font-weight="800" fill="#92400E" text-anchor="middle" letter-spacing="1">DEMO PREVIEW — NOT AI-GENERATED</text>
  <text x="{width // 2}" y="60" font-family="system-ui, -apple-system, sans-serif" font-size="12" font-weight="600" fill="#B45309" text-anchor="middle">Offline simulation active • Local SD WebUI offline • Illustrative estimate</text>

  <!-- PURPOSE-SPECIFIC CONTENT -->
  {illustration}

  <!-- FOOTER METRICS SPECS CARD -->
  <rect x="16" y="{height - footer_height - 10}" width="{width - 32}" height="{footer_height}" rx="10" fill="#1E293B" opacity="0.95" />
  <text x="32" y="{height - footer_height + 22}" font-family="system-ui, sans-serif" font-size="14" fill="#F8FAFC"><b>Prompt:</b> {safe_prompt}</text>
  <text x="32" y="{height - footer_height + 48}" font-family="system-ui, sans-serif" font-size="13" fill="#94A3B8">Purpose: <tspan fill="#38BDF8" font-weight="bold">{purpose}</tspan> | Tier: <tspan fill="#FBBF24" font-weight="bold">{tier.upper()}</tspan> | Res: {resolution}</text>
  <text x="32" y="{height - footer_height + 72}" font-family="system-ui, sans-serif" font-size="12" fill="#34D399" font-weight="bold">Resource Units: {units} unit(s) • Savings vs HQ: {savings:.0f}%</text>
</svg>"""
