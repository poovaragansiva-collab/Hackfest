import pytest
from backend.app.schemas.request import (
    ImageGenerationRequest,
    IntendedUseEnum,
    ColorPreferenceEnum,
    GenerationModeEnum,
)
from backend.app.services.decision_engine import DecisionEngine


def test_decision_engine_coloring_worksheet_optimized():
    req = ImageGenerationRequest(
        prompt="A friendly cartoon giraffe in a savanna",
        intended_use=IntendedUseEnum.COLORING_WORKSHEET,
        mode=GenerationModeEnum.OPTIMIZED,
    )
    decision = DecisionEngine.evaluate(req)

    assert decision.configuration.quality_tier == "standard"
    assert decision.configuration.effective_resolution == "1024x1024"
    assert decision.configuration.color_mode == "monochrome_line_art"
    assert "coloring page style" in decision.configuration.prompt_refinement
    assert decision.metrics.estimated_cost_usd == 0.040
    assert decision.metrics.baseline_cost_usd == 0.080
    assert decision.metrics.cost_reduction_percent == 50.0
    assert decision.metrics.unit == "USD"
    assert decision.metrics.provenance == "mock_illustrative"
    assert decision.metrics.is_live_billed is False
    assert "DALL-E 3" in decision.metrics.pricing_basis
    assert decision.metrics.calculation_explanation is not None
    assert "STANDARD tier" in decision.metrics.calculation_explanation
    assert len(decision.rationale.reasons) >= 2


def test_decision_engine_annual_report_poster():
    req = ImageGenerationRequest(
        prompt="District STEM robotics championship celebration",
        intended_use=IntendedUseEnum.ANNUAL_REPORT_POSTER,
        mode=GenerationModeEnum.OPTIMIZED,
    )
    decision = DecisionEngine.evaluate(req)

    assert decision.configuration.quality_tier == "hd"
    assert decision.metrics.estimated_cost_usd == 0.080
    assert decision.metrics.cost_reduction_percent == 0.0


def test_decision_engine_baseline_mode():
    req = ImageGenerationRequest(
        prompt="A friendly cartoon giraffe in a savanna",
        intended_use=IntendedUseEnum.COLORING_WORKSHEET,
        mode=GenerationModeEnum.BASELINE,
    )
    decision = DecisionEngine.evaluate(req)

    assert decision.configuration.quality_tier == "hd"
    assert decision.configuration.effective_resolution == "1024x1792"
    assert decision.configuration.prompt_refinement == req.prompt
    assert decision.metrics.estimated_cost_usd == 0.080
    assert decision.metrics.cost_reduction_percent == 0.0
