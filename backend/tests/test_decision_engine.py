import pytest
from backend.app.schemas.request import (
    ImageGenerationRequest,
    IntendedUseEnum,
    ColorPreferenceEnum,
    GenerationModeEnum,
)
from backend.app.services.decision_engine import DecisionEngine
from backend.app.config import settings


@pytest.fixture(autouse=True)
def use_mock_settings(monkeypatch):
    """Ensures baseline decision engine tests run against mock provider settings."""
    monkeypatch.setattr(settings, "active_provider", "mock")


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


def test_decision_engine_quality_tier_override():
    # User manually overrides coloring sheet to HD
    req_hd_override = ImageGenerationRequest(
        prompt="A friendly cartoon giraffe in a savanna",
        intended_use=IntendedUseEnum.COLORING_WORKSHEET,
        quality_tier="hd",
    )
    decision_hd = DecisionEngine.evaluate(req_hd_override)
    assert decision_hd.configuration.quality_tier == "hd"
    assert decision_hd.metrics.estimated_cost_usd == 0.080
    assert "High Quality (HD)" in decision_hd.rationale.reasons[0]

    # User manually specifies standard tier
    req_std = ImageGenerationRequest(
        prompt="A district poster banner",
        intended_use=IntendedUseEnum.ANNUAL_REPORT_POSTER,
        quality_tier="standard",
    )
    decision_std = DecisionEngine.evaluate(req_std)
    assert decision_std.configuration.quality_tier == "standard"
    assert decision_std.metrics.estimated_cost_usd == 0.040

