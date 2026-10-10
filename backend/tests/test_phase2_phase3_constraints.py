"""Comprehensive Acceptance Tests for Hackfest Phase 2 (Constraint 1) and Phase 3 (Constraint 2).

Verifies strict compliance with:
- Constraint 1 (Phase 2):
  Every generation must display its estimated cost (compute time, energy or an equivalent measure)
  alongside the saving compared with the maximum setting. Teams must explain how the estimate is calculated.
- Constraint 2 (Phase 3):
  The purpose must be inferred, not only selected from a menu. The system must propose a tier
  automatically from the user's request, explain why, and allow the user to override it.
"""

import pytest
from httpx import ASGITransport, AsyncClient
from backend.app.main import app
from backend.app.schemas.request import ImageGenerationRequest, IntendedUseEnum
from backend.app.services.decision_engine import DecisionEngine
from backend.app.services.purpose_inference import infer_purpose_from_prompt
from backend.app.services.resource_estimator import (
    HIGH_REFERENCE_WORK_UNITS,
    calculate_compute_work_units,
    calculate_normalized_resource_units,
    calculate_compute_savings_percent,
    estimate_transparent_resources,
)
from backend.app.services.storage import get_generation_history, clear_generation_history


@pytest.fixture(autouse=True)
def clean_and_mock(monkeypatch):
    """Ensures offline mock provider and clean history for every test."""
    from backend.app.config import settings
    monkeypatch.setattr(settings, "active_provider", "mock")
    clear_generation_history()
    yield
    clear_generation_history()


# ==============================================================================
# PHASE 2 - CONSTRAINT 1 TESTS
# "Every generation must display its estimated cost (compute time, energy or an
# equivalent measure) alongside the saving compared with the maximum setting.
# Teams must explain how the estimate is calculated."
# ==============================================================================

def test_phase2_constraint1_mathematical_work_and_savings_calculation():
    """Validates the mathematical calculation of compute-work proxy units and relative savings."""
    # 1. High Reference (Maximum Setting Baseline)
    high_work = calculate_compute_work_units(512, 768, 28)
    assert high_work == HIGH_REFERENCE_WORK_UNITS == 11010048
    assert calculate_normalized_resource_units(512, 768, 28) == 1.000
    assert calculate_compute_savings_percent(512, 768, 28) == 0.0

    # 2. Standard Tier (Balanced Classroom Poster)
    std_work = calculate_compute_work_units(512, 512, 18)
    assert std_work == 4718592
    assert calculate_normalized_resource_units(512, 512, 18) == 0.4286
    assert calculate_compute_savings_percent(512, 512, 18) == 57.1

    # 3. Eco Tier (Right-sized Colouring Sheet)
    eco_work = calculate_compute_work_units(384, 384, 10)
    assert eco_work == 1474560
    assert calculate_normalized_resource_units(384, 384, 10) == 0.1339
    assert calculate_compute_savings_percent(384, 384, 10) == 86.6


def test_phase2_constraint1_explanation_of_how_estimate_is_calculated():
    """Validates that teams explain how the estimate is calculated with formula and assumptions."""
    eco_est = estimate_transparent_resources("eco", measured_seconds=1.45)

    # Explanation formula
    assert "formula" in eco_est
    assert "384 × 384 × 10" in eco_est["formula"]
    assert "11,010,048" in eco_est["formula"]
    assert "86.6%" in eco_est["formula"]

    # Explicit assumptions explaining the metric is an algorithmic proxy
    assert "assumptions" in eco_est
    assert "proxy for GPU load" in eco_est["assumptions"]
    assert "not a calibrated direct physical measurement of electrical energy" in eco_est["assumptions"]
    assert "Joules or kWh" in eco_est["assumptions"]

    # Measured compute time
    assert eco_est["elapsed_seconds"] == 1.45
    assert eco_est["timing_type"] == "measured"


@pytest.mark.anyio
async def test_phase2_constraint1_generation_endpoint_displays_cost_savings_and_explanation():
    """Validates that EVERY generation API response displays estimated cost alongside savings and explanation."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        # Generate Eco image
        res = await client.post(
            "/api/v1/generate",
            json={
                "prompt": "Make a simple black-and-white colouring sheet of a butterfly for a seven-year-old.",
                "quality_tier": "eco",
            },
        )
        assert res.status_code == 200
        data = res.json()

        metrics = data["resource_metrics"]

        # Estimated cost / compute time (measured duration)
        assert metrics["latency_seconds"] is not None
        assert metrics["measured_elapsed_seconds"] is not None
        assert metrics["generation_time_label"] == "measured"

        # Estimated cost / equivalent measure (compute-work units)
        assert metrics["work_units"] is not None
        assert metrics["estimated_compute_work_units"] is not None
        assert metrics["high_reference_units"] == 11010048

        # Alongside savings compared with maximum setting
        assert metrics["compute_savings_percent"] is not None
        assert metrics["cost_reduction_percent"] >= 0

        # Explanation of how the estimate is calculated
        assert metrics["formula"] is not None
        assert metrics["assumptions"] is not None
        assert "proxy for GPU load" in metrics["assumptions"]


# ==============================================================================
# PHASE 3 - CONSTRAINT 2 TESTS
# "The purpose must be inferred, not only selected from a menu. The system
# must propose a tier automatically from the user's request, explain why,
# and allow the user to override it."
# ==============================================================================

def test_phase3_constraint2_purpose_inferred_from_user_request():
    """Validates that purpose is inferred from user's request without requiring menu selection."""
    # Scenario 1: Children's colouring sheet
    inf1 = infer_purpose_from_prompt("Make a simple black-and-white colouring sheet of a butterfly for a seven-year-old.")
    assert inf1.purpose == "Children's colouring sheet"
    assert inf1.purpose_key == "coloring_sheet"
    assert inf1.recommended_tier == "eco"
    assert "Simple outlines" in inf1.reason
    assert "black-and-white output" in inf1.reason

    # Scenario 2: Educational poster
    inf2 = infer_purpose_from_prompt("Create an illustrated educational poster about the water cycle.")
    assert inf2.purpose == "Educational poster"
    assert inf2.purpose_key == "educational_poster"
    assert inf2.recommended_tier == "standard"
    assert "readable composition" in inf2.reason

    # Scenario 3: Large-format printed banner
    inf3 = infer_purpose_from_prompt("Create a highly detailed illustration for a large printed school exhibition banner.")
    assert inf3.purpose == "Large-format printed banner"
    assert inf3.purpose_key == "large_format_banner"
    assert inf3.recommended_tier == "high"
    assert "intended print use" in inf3.reason


def test_phase3_constraint2_system_proposes_tier_and_explains_why():
    """Validates that the system automatically proposes a tier and gives an explicit why explanation."""
    req = ImageGenerationRequest(
        prompt="Make a simple black-and-white colouring sheet of a butterfly for a seven-year-old."
    )
    decision = DecisionEngine.evaluate(req)

    # Proposed tier
    assert decision.rationale.recommended_tier == "eco"
    assert decision.rationale.selected_tier in ("eco", "standard")
    assert decision.rationale.tier_overridden is False

    # Explanation why
    assert len(decision.rationale.reasons) > 0
    full_reasons = " ".join(decision.rationale.reasons)
    assert "Simple outlines" in full_reasons or "coloring" in full_reasons.lower() or "eco" in full_reasons.lower()


def test_phase3_constraint2_allows_user_to_override_tier(monkeypatch):
    """Validates that the user can override the automatically proposed tier."""
    from backend.app.config import settings
    monkeypatch.setattr(settings, "active_provider", "automatic1111")

    # User prompt infers Eco, but user explicitly overrides to High
    req_override = ImageGenerationRequest(
        prompt="Make a simple black-and-white colouring sheet of a butterfly for a seven-year-old.",
        quality_tier="high",
    )
    decision = DecisionEngine.evaluate(req_override)

    # Inferred recommendation stays Eco, but selected tier is overridden to High
    assert decision.rationale.recommended_tier == "eco"
    assert decision.rationale.selected_tier == "high"
    assert decision.rationale.tier_overridden is True

    # Applied configuration follows user override
    assert decision.configuration.effective_resolution == "512x768"
    assert decision.configuration.steps == 28

    # Explanation of override is explicitly preserved
    reasons_text = " ".join(decision.rationale.reasons)
    assert "User manual override applied" in reasons_text
    assert "changed from recommended 'Eco' to 'High'" in reasons_text


def test_phase3_constraint2_purpose_not_only_selected_from_menu():
    """Validates that purpose can be inferred from prompt, OR explicitly supplied from a menu."""
    # Case A: Inferred from prompt alone (no menu selection)
    req_inferred = ImageGenerationRequest(
        prompt="Create an educational flashcard of an apple for vocabulary"
    )
    dec_inferred = DecisionEngine.evaluate(req_inferred)
    assert dec_inferred.rationale.recommended_tier == "eco"
    assert "flashcard" in dec_inferred.rationale.purpose_identified.lower()

    # Case B: Selected from menu (intended_use enum explicitly provided)
    req_menu = ImageGenerationRequest(
        prompt="An apple image",
        intended_use=IntendedUseEnum.FLASHCARD,
    )
    dec_menu = DecisionEngine.evaluate(req_menu)
    assert dec_menu.rationale.recommended_tier == "eco"
    assert dec_menu.rationale.purpose_identified == "flashcard"


@pytest.mark.anyio
async def test_phase3_constraint2_e2e_api_override_persistence():
    """Validates that tier override flows through API and is recorded in persistent history."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        res = await client.post(
            "/api/v1/generate",
            json={
                "prompt": "Make a simple black-and-white colouring sheet of a butterfly for a seven-year-old.",
                "quality_tier": "high",  # User override over recommended Eco
            },
        )
        assert res.status_code == 200
        data = res.json()

        assert data["decision_rationale"]["recommended_tier"] == "eco"
        assert data["decision_rationale"]["selected_tier"] == "high"
        assert data["decision_rationale"]["tier_overridden"] is True

        # Check SQLite history
        history_res = await client.get("/api/v1/history")
        assert history_res.status_code == 200
        history = history_res.json()
        assert len(history) == 1
        record = history[0]
        assert record["recommended_tier"] == "eco"
        assert record["selected_tier"] == "high"
        assert record["tier_overridden"] is True
