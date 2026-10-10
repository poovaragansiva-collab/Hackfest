import pytest
from httpx import ASGITransport, AsyncClient
from backend.app.main import app
from backend.app.schemas.request import ImageGenerationRequest, IntendedUseEnum
from backend.app.services.decision_engine import DecisionEngine
from backend.app.services.resource_estimator import (
    get_tier_resource_units,
    calculate_resource_savings_percent,
    estimate_generation_resources,
)


@pytest.fixture(autouse=True)
def use_mock_provider(monkeypatch):
    """Ensures test runs always use offline mock provider."""
    from backend.app.config import settings
    monkeypatch.setattr(settings, "active_provider", "mock")


def test_resource_estimator_units_and_savings():
    # Eco tier
    assert get_tier_resource_units("eco") == 1
    assert calculate_resource_savings_percent("eco") == 75.0

    # Standard tier
    assert get_tier_resource_units("standard") == 2
    assert calculate_resource_savings_percent("standard") == 50.0

    # High quality tier
    assert get_tier_resource_units("high_quality") == 4
    assert calculate_resource_savings_percent("high_quality") == 0.0

    # Check shared resource summary dict
    eco_summary = estimate_generation_resources("eco")
    assert eco_summary["relative_resource_units"] == 1
    assert eco_summary["baseline_resource_units"] == 4
    assert eco_summary["resource_savings_percent"] == 75.0

    hq_summary = estimate_generation_resources("high_quality")
    assert hq_summary["relative_resource_units"] == 4
    assert hq_summary["baseline_resource_units"] == 4
    assert hq_summary["resource_savings_percent"] == 0.0


def test_purpose_based_recommendations():
    # Coloring sheet -> Eco
    req_color = ImageGenerationRequest(
        prompt="A friendly elephant for a children's colouring sheet",
        intended_use=IntendedUseEnum.COLORING_SHEET,
    )
    dec_color = DecisionEngine.evaluate(req_color)
    assert dec_color.configuration.quality_tier == "eco"
    assert dec_color.metrics.relative_resource_units == 1
    assert dec_color.metrics.resource_savings_percent == 75.0

    # Flashcard -> Eco
    req_fc = ImageGenerationRequest(
        prompt="An apple illustration for vocabulary",
        intended_use=IntendedUseEnum.FLASHCARD,
    )
    dec_fc = DecisionEngine.evaluate(req_fc)
    assert dec_fc.configuration.quality_tier == "eco"
    assert dec_fc.metrics.relative_resource_units == 1
    assert dec_fc.metrics.resource_savings_percent == 75.0

    # Worksheet illustration -> Eco
    req_ws = ImageGenerationRequest(
        prompt="Plant cell diagram with labeled parts",
        intended_use=IntendedUseEnum.WORKSHEET_ILLUSTRATION,
    )
    dec_ws = DecisionEngine.evaluate(req_ws)
    assert dec_ws.configuration.quality_tier == "eco"
    assert dec_ws.metrics.relative_resource_units == 1
    assert dec_ws.metrics.resource_savings_percent == 75.0

    # Educational poster -> Standard
    req_post = ImageGenerationRequest(
        prompt="Solar system poster for middle school",
        intended_use=IntendedUseEnum.EDUCATIONAL_POSTER,
    )
    dec_post = DecisionEngine.evaluate(req_post)
    assert dec_post.configuration.quality_tier == "standard"
    assert dec_post.metrics.relative_resource_units == 2
    assert dec_post.metrics.resource_savings_percent == 50.0

    # Premium poster -> High Quality (or legacy 'hd' tag)
    req_prem = ImageGenerationRequest(
        prompt="Auditorium science exhibition banner",
        intended_use=IntendedUseEnum.PREMIUM_POSTER,
    )
    dec_prem = DecisionEngine.evaluate(req_prem)
    assert dec_prem.configuration.quality_tier in ("high_quality", "hd")
    assert dec_prem.metrics.relative_resource_units == 4
    assert dec_prem.metrics.resource_savings_percent == 0.0


def test_manual_tier_override():
    # User selects coloring sheet but explicitly requests High Quality
    req_override = ImageGenerationRequest(
        prompt="A friendly elephant for a children's colouring sheet",
        intended_use=IntendedUseEnum.COLORING_SHEET,
        quality_tier="high_quality",
    )
    dec_override = DecisionEngine.evaluate(req_override)
    assert dec_override.configuration.quality_tier in ("high_quality", "hd")
    assert dec_override.metrics.relative_resource_units == 4
    assert dec_override.metrics.resource_savings_percent == 0.0


@pytest.mark.anyio
async def test_generate_endpoint_resource_metrics_and_demo():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/api/v1/generate",
            json={
                "prompt": "A friendly elephant for a children's colouring sheet",
                "intended_use": "coloring_sheet",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        metrics = data["resource_metrics"]
        assert metrics["relative_resource_units"] == 1
        assert metrics["baseline_resource_units"] == 4
        assert metrics["resource_savings_percent"] == 75.0
        assert metrics["is_demo"] is True
        assert metrics["generation_time_label"] == "measured"
        assert metrics["calculation_method"] == "illustrative_relative_units"
        assert "Demo preview" in data["image"]["url"] or "data:image/svg+xml" in data["image"]["url"]
