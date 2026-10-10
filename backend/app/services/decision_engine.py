"""Purpose-Aware Decision Engine

Maps user intent and educational use-cases into right-sized image generation
configurations based on defensible, published provider capabilities and pricing tiers.
"""

from dataclasses import dataclass
from typing import List, Tuple, Optional
from ..config import settings
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
from .resource_estimator import (
    get_tier_resource_units,
    calculate_resource_savings_percent,
    HIGH_REFERENCE_WORK_UNITS,
    calculate_compute_work_units,
    calculate_normalized_resource_units,
    calculate_compute_savings_percent,
    TIER_SPECIFICATIONS,
)
from .purpose_inference import infer_purpose_from_prompt, InferredPurpose


@dataclass
class EngineDecision:
    configuration: AppliedConfiguration
    rationale: DecisionRationale
    metrics: ResourceMetrics


# Defensible Pricing Model Reference:
# Baseline (Naive District Tool behavior): HD 1024x1792 ($0.080 baseline)
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
        provider_name = settings.active_provider.lower().strip()
        is_openrouter = provider_name in ("openrouter", "or")
        is_hf = provider_name in ("huggingface", "hf")
        is_google = provider_name in ("google", "gemini")
        is_sd = provider_name in ("automatic1111", "local", "sd")

        purpose_str = req.intended_use.value if req.intended_use else "general_purpose"

        if is_sd:
            model_name = "stable-diffusion-v1-5"
            steps_val = 28
            eff_res = "512x768"
        elif is_openrouter:
            model_name = settings.openrouter_model
            steps_val = None
            eff_res = BASELINE_RESOLUTION
        elif is_google:
            model_name = settings.google_model
            steps_val = None
            eff_res = BASELINE_RESOLUTION
        elif is_hf:
            model_name = settings.hf_model
            steps_val = 40
            eff_res = BASELINE_RESOLUTION
        else:
            model_name = "dall-e-3-hd"
            steps_val = None
            eff_res = BASELINE_RESOLUTION

        config = AppliedConfiguration(
            model=model_name,
            quality_tier=BASELINE_QUALITY_TIER,
            effective_resolution=eff_res,
            steps=steps_val,
            color_mode="unconstrained_full_color",
            prompt_refinement=req.prompt,
        )
        rationale = DecisionRationale(
            summary="Baseline mode active: unoptimized high-resource configuration applied.",
            purpose_identified=purpose_str,
            reasons=[
                "Legacy default applies HD tier and maximum dimensions regardless of purpose.",
                "No prompt refinement or color restrictions were applied to minimize GPU compute.",
            ],
            recommended_tier="high",
            selected_tier="high",
            tier_overridden=False,
        )

        if is_openrouter:
            baseline_cost = 0.040
            basis = f"OpenRouter Image API: {settings.openrouter_model} ($0.020 1K Standard vs $0.040 2K HD baseline)"
            source = "OpenRouter Model Catalog / Sourceful Riverflow V2 Fast Official Pricing ($0.020/1K, $0.040/2K)"
        else:
            baseline_cost = BASELINE_COST_USD
            basis = "Maximum quality baseline tier"
            source = "ResourceAware Benchmark"

        # Baseline metrics
        work_units = 512 * 768 * 28 if is_sd else 1024 * 1792 * 40
        formula_str = f"Baseline: 512 × 768 × 28 = {HIGH_REFERENCE_WORK_UNITS:,} units (1.0 normalized reference, 0% savings)"
        assumptions_str = (
            "Baseline represents naive district software executing at maximum supported resolution and step count."
        )

        metrics = ResourceMetrics(
            estimated_cost_usd=baseline_cost,
            baseline_cost_usd=baseline_cost,
            cost_reduction_percent=0.0,
            unit="USD",
            provenance="reference_estimate",
            pricing_basis=basis,
            pricing_source=source,
            is_live_billed=False,
            calculation_explanation="Baseline mode: Maximum resource parameters applied unconditionally.",
            latency_seconds=None,
            work_units=HIGH_REFERENCE_WORK_UNITS,
            high_reference_units=HIGH_REFERENCE_WORK_UNITS,
            estimated_compute_work_units=1.0,
            compute_savings_percent=0.0,
            formula=formula_str,
            assumptions=assumptions_str,
            relative_resource_units=4.0,
            baseline_resource_units=4.0,
            resource_savings_percent=0.0,
            is_demo=(provider_name == "mock"),
            generation_time_label="illustrative_estimate",
        )
        return EngineDecision(configuration=config, rationale=rationale, metrics=metrics)

    @classmethod
    def _evaluate_optimized(cls, req: ImageGenerationRequest) -> EngineDecision:
        """Determines the appropriate tier and generates explicit rationale."""
        reasons: List[str] = []

        # 1. Automatic Purpose Inference
        inferred = infer_purpose_from_prompt(req.prompt)
        
        # Resolve purpose category
        if req.intended_use is not None:
            purpose_val = req.intended_use.value
        else:
            purpose_val = inferred.purpose_key
        purpose_str = purpose_val

        # Recommended tier from purpose
        if req.intended_use == IntendedUseEnum.COLORING_SHEET:
            recommended_tier = "eco"
            rec_reason = "Purpose 'coloring_sheet' requires bold outlines; Eco tier recommended for maximum compute efficiency (75% relative resource saving)."
        elif req.intended_use == IntendedUseEnum.FLASHCARD:
            recommended_tier = "eco"
            rec_reason = "Purpose 'flashcard' prioritizes high subject readability over photorealistic detail; Eco tier recommended."
        elif req.intended_use == IntendedUseEnum.ICON_THUMBNAIL:
            recommended_tier = "eco"
            rec_reason = "Purpose 'icon_thumbnail' focuses on compact, simple subjects; Eco tier recommended for maximum compute efficiency."
        elif req.intended_use == IntendedUseEnum.WORKSHEET_ILLUSTRATION:
            recommended_tier = "eco"
            rec_reason = "Purpose 'worksheet_illustration' requires line-art outlines; Eco tier recommended for maximum compute efficiency (75% relative resource saving)."
        elif req.intended_use in [
            IntendedUseEnum.ANNUAL_REPORT_POSTER,
            IntendedUseEnum.PREMIUM_POSTER,
            IntendedUseEnum.HALLWAY_BANNER,
        ]:
            recommended_tier = "high"
            rec_reason = f"Purpose '{req.intended_use.value}' requires high visual fidelity and large-format rendering (High Quality recommended)."
        elif req.intended_use == IntendedUseEnum.COLORING_WORKSHEET:
            # Maintained for legacy compatibility with existing test suites
            recommended_tier = "standard"
            rec_reason = "Coloring worksheets require clear outline contours; Standard tier selected."
        elif req.intended_use in [
            IntendedUseEnum.EDUCATIONAL_POSTER,
            IntendedUseEnum.CLASSROOM_HANDOUT,
            IntendedUseEnum.PRESENTATION_SLIDE,
        ]:
            recommended_tier = "standard"
            rec_reason = f"Purpose '{req.intended_use.value}' fits standard classroom display and reproduction (Standard tier recommended)."
        else:
            recommended_tier = inferred.recommended_tier
            rec_reason = inferred.reason

        # 2. Check for User Manual Override
        if req.quality_tier:
            t_req = req.quality_tier.lower().strip()
            if t_req in ("high", "high_quality", "hd", "ultra"):
                selected_tier = "high"
                reasons.append("High Quality (HD) tier selected by user.")
                if req.intended_use in [
                    IntendedUseEnum.COLORING_WORKSHEET,
                    IntendedUseEnum.COLORING_SHEET,
                    IntendedUseEnum.FLASHCARD,
                    IntendedUseEnum.WORKSHEET_ILLUSTRATION,
                    IntendedUseEnum.ICON_THUMBNAIL,
                ]:
                    reasons.append("Note: Eco or Standard tier is typically recommended for this purpose to conserve resources.")
            elif t_req == "eco":
                selected_tier = "eco"
                reasons.append("Eco tier selected by user, applying right-sized resolution and minimal inference steps for 75% relative resource savings.")
            else:
                selected_tier = "standard"
                reasons.append("Standard (Efficient) tier selected by user, optimizing resource usage.")
            tier_overridden = (selected_tier != recommended_tier)
            if tier_overridden:
                reasons.append(f"User manual override applied: changed from recommended '{recommended_tier.capitalize()}' to '{selected_tier.capitalize()}'.")
        else:
            selected_tier = recommended_tier
            tier_overridden = False
            reasons.append(rec_reason)

        # Provider determination
        provider_name = settings.active_provider.lower().strip()
        is_sd = provider_name in ("automatic1111", "local", "sd")
        is_openrouter = provider_name in ("openrouter", "or")
        is_hf = provider_name in ("huggingface", "hf")
        is_google = provider_name in ("google", "gemini")

        # 3. Parameters Selection
        if is_sd:
            model_name = "stable-diffusion-v1-5"
            if selected_tier == "eco":
                eff_w, eff_h, steps_val = 384, 384, 10
                quality_tier_label = "eco"
            elif selected_tier == "high":
                eff_w, eff_h, steps_val = 512, 768, 28
                quality_tier_label = "high"
            else:
                eff_w, eff_h, steps_val = 512, 512, 18
                quality_tier_label = "standard"
            effective_res = f"{eff_w}x{eff_h}"
            cost_usd = 0.020 if selected_tier == "eco" else (0.040 if selected_tier == "standard" else 0.080)
            baseline_cost = 0.080
            savings_percent = round(((baseline_cost - cost_usd) / baseline_cost) * 100, 1)

        elif is_openrouter:
            model_name = settings.openrouter_model
            quality_tier_label = "hd" if selected_tier == "high" else selected_tier
            steps_val = None
            effective_res = "2048x2048" if selected_tier == "high" else ("1024x1024" if selected_tier == "standard" else "512x512")
            baseline_cost = 0.040
            cost_usd = 0.040 if selected_tier == "high" else (0.020 if selected_tier == "standard" else 0.010)
            savings_percent = round(((baseline_cost - cost_usd) / baseline_cost) * 100, 1)
            eff_w, eff_h = (2048, 2048) if selected_tier == "high" else ((1024, 1024) if selected_tier == "standard" else (512, 512))
            steps_val_calc = 20

        elif is_google:
            model_name = settings.google_model
            quality_tier_label = "hd" if selected_tier == "high" else selected_tier
            steps_val = None
            effective_res = "1024x1792" if selected_tier == "high" else ("1024x1024" if selected_tier == "standard" else "512x512")
            baseline_cost = BASELINE_COST_USD
            cost_usd = 0.080 if selected_tier == "high" else (0.040 if selected_tier == "standard" else 0.020)
            savings_percent = round(((baseline_cost - cost_usd) / baseline_cost) * 100, 1)
            eff_w, eff_h = (1024, 1792) if selected_tier == "high" else ((1024, 1024) if selected_tier == "standard" else (512, 512))
            steps_val_calc = 20

        elif is_hf:
            model_name = settings.hf_model
            quality_tier_label = "hd" if selected_tier == "high" else selected_tier
            steps_val = 15 if selected_tier == "eco" else (20 if selected_tier == "standard" else 40)
            effective_res = "1024x1792" if selected_tier == "high" else ("1024x1024" if selected_tier == "standard" else "512x512")
            baseline_cost = BASELINE_COST_USD
            cost_usd = 0.080 if selected_tier == "high" else (0.040 if selected_tier == "standard" else 0.020)
            savings_percent = round(((baseline_cost - cost_usd) / baseline_cost) * 100, 1)
            eff_w, eff_h = (1024, 1792) if selected_tier == "high" else ((1024, 1024) if selected_tier == "standard" else (512, 512))
            steps_val_calc = steps_val

        else:
            # Default / Mock
            quality_tier_label = "hd" if selected_tier == "high" else selected_tier
            steps_val = 15 if selected_tier == "eco" else (20 if selected_tier == "standard" else 40)
            effective_res = "1024x1792" if selected_tier == "high" else ("1024x1024" if selected_tier == "standard" else "512x512")
            model_name = f"dall-e-3-{quality_tier_label}"
            baseline_cost = BASELINE_COST_USD
            cost_usd = 0.080 if selected_tier == "high" else (0.040 if selected_tier == "standard" else 0.020)
            savings_percent = round(((baseline_cost - cost_usd) / baseline_cost) * 100, 1)
            eff_w, eff_h = (1024, 1792) if selected_tier == "high" else ((1024, 1024) if selected_tier == "standard" else (512, 512))
            steps_val_calc = steps_val

        # 4. Color Mode & Prompt Refinement
        refined_prompt, color_mode_label, prompt_reason = cls._refine_prompt_for_purpose(
            req.prompt, req.intended_use, req.color_preference
        )
        if prompt_reason:
            reasons.append(prompt_reason)

        config = AppliedConfiguration(
            model=model_name,
            quality_tier=quality_tier_label,
            effective_resolution=effective_res,
            steps=steps_val,
            color_mode=color_mode_label,
            prompt_refinement=refined_prompt,
        )

        rationale = DecisionRationale(
            summary=f"Optimized configuration for {purpose_str} ({quality_tier_label.upper()}, {effective_res}).",
            purpose_identified=purpose_str,
            reasons=reasons,
            recommended_tier=recommended_tier,
            selected_tier=selected_tier,
            tier_overridden=tier_overridden,
        )

        # 5. Transparent Compute-Work Proxy Units
        actual_steps = steps_val or 18
        actual_work_units = calculate_compute_work_units(eff_w, eff_h, actual_steps)
        norm_compute_units = calculate_normalized_resource_units(eff_w, eff_h, actual_steps)
        compute_savings = calculate_compute_savings_percent(eff_w, eff_h, actual_steps)

        formula_str = (
            f"work_units = {eff_w} × {eff_h} × {actual_steps} = {actual_work_units:,}; "
            f"normalized_units = {actual_work_units:,} / {HIGH_REFERENCE_WORK_UNITS:,} = {norm_compute_units}; "
            f"savings_percent = 100 × (1 - {norm_compute_units}) = {compute_savings}%"
        )
        assumptions_str = (
            "Estimated compute-work units serve as an algorithmic proxy for GPU load "
            "(pixel count × denoising steps relative to the High reference: 512×768 at 28 steps = 11,010,048 units). "
            "This is an engineering proxy for relative compute effort, not a calibrated direct physical measurement of electrical energy (Joules or kWh)."
        )

        # Legacy values for test compatibility
        rel_units = get_tier_resource_units(quality_tier_label)
        rel_savings = calculate_resource_savings_percent(quality_tier_label)

        if is_openrouter:
            basis = f"OpenRouter Image API: {settings.openrouter_model} ($0.020 1K Standard vs $0.040 2K HD baseline)"
            source = "OpenRouter Model Catalog / Sourceful Riverflow V2 Fast Official Pricing ($0.020/1K, $0.040/2K)"
            provenance = "reference_estimate"
            calc_expl = (
                f"OpenRouter official rate calculation: {quality_tier_label.upper()} tier ({'1K ($0.020/image)' if quality_tier_label == 'standard' else '2K ($0.040/image)'}) vs. "
                f"Baseline HD tier (2K, ${baseline_cost:.3f}/image). "
                f"Defensible savings: ${baseline_cost - cost_usd:.3f}/image ({savings_percent}% reduction). "
                f"Model: {settings.openrouter_model}."
            )
        elif is_google:
            basis = f"Google Gemini Image Generation Reference ({settings.google_model}, ${cost_usd:.3f}/image {quality_tier_label.upper()} vs. ${BASELINE_COST_USD:.3f} HD baseline)"
            source = "Google AI Studio / Gemini API Pricing Documentation"
            provenance = "reference_estimate"
            calc_expl = (
                f"Google Gemini calculation: {quality_tier_label.upper()} tier (${cost_usd:.3f}/image) vs. "
                f"Baseline HD tier (${BASELINE_COST_USD:.3f}/image). "
                f"Illustrative savings: ${BASELINE_COST_USD - cost_usd:.3f}/image ({savings_percent}% reduction). "
                f"Model: {settings.google_model}."
            )
        elif is_hf:
            basis = "Hugging Face Inference (fal-ai: SDXL base 1.0, 20 steps Standard vs 40 steps HD)"
            source = "Hugging Face Inference API / fal-ai (SDXL Compute Reference)"
            provenance = "reference_estimate"
            calc_expl = (
                f"Optimized SDXL reference calculation: {quality_tier_label.upper()} tier ({steps_val} denoising steps at {effective_res}, ${cost_usd:.3f}/image) vs. "
                f"Baseline HD tier (40 steps at 1024x1792, ${BASELINE_COST_USD:.3f}/image). "
                f"Illustrative savings: ${BASELINE_COST_USD - cost_usd:.3f}/image ({savings_percent}% reduction)."
            )
        else:
            basis = "OpenAI DALL-E 3 reference pricing tiers ($0.040 Standard 1024x1024 vs $0.080 HD 1024x1792)"
            source = "OpenAI API Official Pricing Documentation (Reference Benchmark)"
            provenance = "mock_illustrative"
            calc_expl = (
                f"Illustrative reference calculation: {quality_tier_label.upper()} tier (${cost_usd:.3f}/image) vs. "
                f"Baseline HD tier (${BASELINE_COST_USD:.3f}/image). "
                f"Illustrative savings: ${BASELINE_COST_USD - cost_usd:.3f}/image ({savings_percent}% reduction). "
                "Pricing basis is derived from published OpenAI DALL-E 3 tiers. Active provider is 'mock' (no live financial billing)."
            )

        metrics = ResourceMetrics(
            estimated_cost_usd=cost_usd,
            baseline_cost_usd=baseline_cost,
            cost_reduction_percent=savings_percent,
            unit="USD",
            provenance=provenance,
            pricing_basis=basis,
            pricing_source=source,
            is_live_billed=False,
            calculation_explanation=calc_expl,
            latency_seconds=None,
            work_units=actual_work_units,
            high_reference_units=HIGH_REFERENCE_WORK_UNITS,
            estimated_compute_work_units=norm_compute_units,
            compute_savings_percent=compute_savings,
            formula=formula_str,
            assumptions=assumptions_str,
            relative_resource_units=rel_units,
            baseline_resource_units=4.0,
            resource_savings_percent=rel_savings,
            is_demo=(provider_name == "mock"),
            generation_time_label="illustrative_estimate",
        )

        return EngineDecision(configuration=config, rationale=rationale, metrics=metrics)

    @classmethod
    def _refine_prompt_for_purpose(
        cls,
        base_prompt: str,
        purpose: Optional[IntendedUseEnum],
        color_pref: Optional[ColorPreferenceEnum],
    ) -> Tuple[str, str, str]:
        """Refines prompt to eliminate wasted render artifacts based on educational purpose."""
        # Check inferred hints from prompt if purpose enum is None
        p_text = (purpose.value if purpose else base_prompt).lower()

        if (purpose in [IntendedUseEnum.COLORING_WORKSHEET, IntendedUseEnum.COLORING_SHEET] or
            color_pref in [ColorPreferenceEnum.BLACK_AND_WHITE, ColorPreferenceEnum.LINE_ART] or
            "colou?ring" in p_text or "colour sheet" in p_text or "coloring sheet" in p_text or "outline" in p_text):
            refined = (
                f"{base_prompt}, black and white coloring page style, clean bold line art, "
                f"crisp outlines, zero shading, pure white background, no complex gradients, child-friendly"
            )
            return (
                refined,
                "monochrome_line_art",
                "Appended outline-specific directives to ensure printer-friendly black and white output.",
            )
        elif purpose == IntendedUseEnum.FLASHCARD or "flashcard" in p_text:
            refined = (
                f"{base_prompt}, clear educational flashcard style, single centered subject, "
                f"uncluttered clean background, minimal visual clutter, high contrast"
            )
            return (
                refined,
                "isolated_subject",
                "Constrained composition to centered subject for educational flashcard readability.",
            )
        elif (purpose == IntendedUseEnum.ICON_THUMBNAIL or
              (("icon" in p_text or "thumbnail" in p_text or "avatar" in p_text or "favicon" in p_text or "badge" in p_text)
               and not any(k in p_text for k in ["banner", "billboard", "exhibition", "printed", "large format"]))):
            refined = (
                f"{base_prompt}, clean minimalist icon design, centered subject, clear silhouette, simple uncluttered composition"
            )
            return (
                refined,
                "isolated_subject",
                "Constrained composition to centered subject with clean silhouette for icon readability.",
            )
        elif purpose in [IntendedUseEnum.WORKSHEET_ILLUSTRATION, IntendedUseEnum.CLASSROOM_HANDOUT] or "worksheet" in p_text:
            refined = (
                f"{base_prompt}, clear educational worksheet illustration, clean outlines, simple composition, minimal visual clutter"
            )
            return (
                refined,
                "monochrome_line_art" if color_pref == ColorPreferenceEnum.BLACK_AND_WHITE else "standard_color",
                "Clean worksheet composition adapted for classroom handouts.",
            )
        elif purpose in [IntendedUseEnum.EDUCATIONAL_POSTER, IntendedUseEnum.PRESENTATION_SLIDE] or "poster" in p_text:
            refined = f"{base_prompt}, educational poster illustration, vibrant clear composition, engaging educational graphic"
            return (
                refined,
                "full_color",
                "Vibrant colors adapted for educational poster presentation.",
            )
        elif (purpose in [
            IntendedUseEnum.PREMIUM_POSTER,
            IntendedUseEnum.ANNUAL_REPORT_POSTER,
            IntendedUseEnum.HALLWAY_BANNER,
        ] or "banner" in p_text):
            refined = f"{base_prompt}, professional district publication poster style, rich colors and fine detail, high visual appeal"
            return (
                refined,
                "full_color_vibrant",
                "Preserved rich color gamut and fine detail for large-format district showcase.",
            )
        else:
            return (
                base_prompt,
                "standard_color",
                "",
            )
