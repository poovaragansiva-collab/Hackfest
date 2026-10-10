"""Purpose-Aware Decision Engine

Maps user intent and educational use-cases into right-sized image generation
configurations based on defensible, published provider capabilities and pricing tiers.
"""

from dataclasses import dataclass
from typing import List, Tuple
from ..schemas.request import (
    ImageGenerationRequest,
    IntendedUseEnum,
    ColorPreferenceEnum,
    DetailLevelEnum,
    TargetMediumEnum,
    GenerationModeEnum,
)
from ..schemas.response import (
    AppliedConfiguration,
    DecisionRationale,
    ResourceMetrics,
)


@dataclass
class EngineDecision:
    configuration: AppliedConfiguration
    rationale: DecisionRationale
    metrics: ResourceMetrics


# Defensible Pricing Model Reference:
# OpenAI DALL-E 3 Official Pricing:
# - Standard 1024x1024: $0.040 / image
# - HD 1024x1024: $0.080 / image
# - HD 1024x1792 or 1792x1024: $0.120 / image
#
# Baseline (Naive District Tool behavior):
# Always requested HD large-format image ($0.080 - $0.120 per generation)
# even for simple monochrome classroom printouts.
BASELINE_COST_USD = 0.080
BASELINE_QUALITY_TIER = "hd"
BASELINE_RESOLUTION = "1024x1792"


class DecisionEngine:
    """Evaluates request context and selects an optimal, justifiable configuration."""

    @classmethod
    def evaluate(cls, req: ImageGenerationRequest) -> EngineDecision:
        if req.mode == GenerationModeEnum.BASELINE:
            return cls._evaluate_baseline(req)
        return cls._evaluate_optimized(req)

    @classmethod
    def _evaluate_baseline(cls, req: ImageGenerationRequest) -> EngineDecision:
        """Represents the unoptimized legacy district behavior: maximum settings for everything."""
        config = AppliedConfiguration(
            model="dall-e-3-hd",
            quality_tier=BASELINE_QUALITY_TIER,
            effective_resolution=BASELINE_RESOLUTION,
            steps=None,
            color_mode="unconstrained_full_color",
            prompt_refinement=req.prompt,
        )
        rationale = DecisionRationale(
            summary="Baseline mode active: unoptimized high-resource configuration applied.",
            purpose_identified=req.intended_use.value,
            reasons=[
                "Legacy default applies HD tier and maximum dimensions regardless of purpose.",
                "No prompt refinement or color restrictions were applied to minimize GPU compute.",
            ],
        )
        metrics = ResourceMetrics(
            estimated_cost_usd=BASELINE_COST_USD,
            baseline_cost_usd=BASELINE_COST_USD,
            cost_reduction_percent=0.0,
            unit="USD",
            provenance="mock_illustrative",
            pricing_basis="OpenAI DALL-E 3 reference pricing tiers ($0.040 Standard 1024x1024 vs $0.080 HD 1024x1792)",
            pricing_source="OpenAI API Official Pricing Documentation (Reference Benchmark)",
            is_live_billed=False,
            calculation_explanation=(
                f"Illustrative baseline: HD quality tier (1024x1792) at ${BASELINE_COST_USD:.3f}/image reference rate "
                "(standard district legacy default). Active provider is 'mock' (no live financial billing)."
            ),
            latency_seconds=None,
        )
        return EngineDecision(configuration=config, rationale=rationale, metrics=metrics)

    @classmethod
    def _evaluate_optimized(cls, req: ImageGenerationRequest) -> EngineDecision:
        """Determines the appropriate tier and generates explicit rationale."""
        reasons: List[str] = []
        
        # 1. Determine Quality Tier & Pricing
        if req.intended_use in [
            IntendedUseEnum.ANNUAL_REPORT_POSTER,
            IntendedUseEnum.HALLWAY_BANNER,
        ]:
            quality_tier = "hd"
            effective_res = "1024x1792" if req.target_medium == TargetMediumEnum.HIGH_RESOLUTION_PRINT else "1024x1024"
            cost_usd = 0.080
            reasons.append(
                f"Purpose '{req.intended_use.value}' requires high visual fidelity and large-format rendering."
            )
            reasons.append(
                "Retained HD tier to avoid pixelation on official district public displays."
            )
        elif req.intended_use == IntendedUseEnum.COLORING_WORKSHEET:
            quality_tier = "standard"
            effective_res = "1024x1024"
            cost_usd = 0.040
            reasons.append(
                "Coloring worksheets require clear outline contours; HD micro-texture synthesis is unnecessary."
            )
            reasons.append(
                "Standard quality tier selected, reducing generation cost by 50% compared to baseline."
            )
        elif req.intended_use == IntendedUseEnum.FLASHCARD:
            quality_tier = "standard"
            effective_res = "1024x1024"
            cost_usd = 0.040
            reasons.append(
                "Flashcards prioritize high subject readability over photorealistic detail."
            )
            reasons.append(
                "Standard tier provides full print clarity at 1024x1024 for card stock without HD cost."
            )
        else:
            # CLASSROOM_HANDOUT, PRESENTATION_SLIDE
            quality_tier = "standard"
            effective_res = "1024x1024"
            cost_usd = 0.040
            reasons.append(
                f"Purpose '{req.intended_use.value}' fits standard classroom display and reproduction."
            )
            reasons.append(
                "Standard quality avoids unnecessary cloud compute bill inflation."
            )

        # 2. Determine Color Mode & Prompt Refinement
        refined_prompt, color_mode_label, prompt_reason = cls._refine_prompt_for_purpose(
            req.prompt, req.intended_use, req.color_preference
        )
        if prompt_reason:
            reasons.append(prompt_reason)

        # 3. Calculate defensible cost reduction
        savings_percent = round(((BASELINE_COST_USD - cost_usd) / BASELINE_COST_USD) * 100, 1)

        config = AppliedConfiguration(
            model=f"dall-e-3-{quality_tier}",
            quality_tier=quality_tier,
            effective_resolution=effective_res,
            steps=None,
            color_mode=color_mode_label,
            prompt_refinement=refined_prompt,
        )

        rationale = DecisionRationale(
            summary=f"Optimized configuration for {req.intended_use.value} ({quality_tier.upper()}, {effective_res}).",
            purpose_identified=req.intended_use.value,
            reasons=reasons,
        )

        metrics = ResourceMetrics(
            estimated_cost_usd=cost_usd,
            baseline_cost_usd=BASELINE_COST_USD,
            cost_reduction_percent=savings_percent,
            unit="USD",
            provenance="mock_illustrative",
            pricing_basis="OpenAI DALL-E 3 reference pricing tiers ($0.040 Standard 1024x1024 vs $0.080 HD 1024x1792)",
            pricing_source="OpenAI API Official Pricing Documentation (Reference Benchmark)",
            is_live_billed=False,
            calculation_explanation=(
                f"Illustrative reference calculation: {quality_tier.upper()} tier (${cost_usd:.3f}/image) vs. "
                f"Baseline HD tier (${BASELINE_COST_USD:.3f}/image). "
                f"Illustrative savings: ${BASELINE_COST_USD - cost_usd:.3f}/image ({savings_percent}% reduction). "
                "Pricing basis is derived from published OpenAI DALL-E 3 tiers. Active provider is 'mock' (no live financial billing)."
            ),
            latency_seconds=None,
        )

        return EngineDecision(configuration=config, rationale=rationale, metrics=metrics)

    @classmethod
    def _refine_prompt_for_purpose(
        cls,
        base_prompt: str,
        purpose: IntendedUseEnum,
        color_pref: ColorPreferenceEnum,
    ) -> Tuple[str, str, str]:
        """Refines prompt to eliminate wasted render artifacts based on educational purpose."""
        if purpose == IntendedUseEnum.COLORING_WORKSHEET or color_pref in [
            ColorPreferenceEnum.BLACK_AND_WHITE,
            ColorPreferenceEnum.LINE_ART,
        ]:
            refined = (
                f"{base_prompt}, black and white coloring page style, clean bold line art, "
                f"crisp outlines, zero shading, pure white background, no complex gradients"
            )
            return (
                refined,
                "monochrome_line_art",
                "Appended outline-specific directives to ensure printer-friendly black and white output.",
            )
        elif purpose == IntendedUseEnum.FLASHCARD:
            refined = (
                f"{base_prompt}, clear educational flashcard style, single centered subject, "
                f"uncluttered clean background, high contrast"
            )
            return (
                refined,
                "isolated_subject",
                "Constrained composition to centered subject for educational flashcard readability.",
            )
        elif purpose in [IntendedUseEnum.ANNUAL_REPORT_POSTER, IntendedUseEnum.HALLWAY_BANNER]:
            refined = f"{base_prompt}, professional district publication poster style, high visual appeal"
            return (
                refined,
                "full_color_vibrant",
                "Preserved rich color gamut for high-visibility public district display.",
            )
        else:
            return (
                base_prompt,
                "standard_color",
                "",
            )
