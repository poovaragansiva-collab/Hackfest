import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def use_mock_provider(monkeypatch):
    """Ensures API integration tests always use offline mock provider."""
    from backend.app.config import settings
    monkeypatch.setattr(settings, "active_provider", "mock")


def test_generate_image_coloring_worksheet_success():
    payload = {
        "prompt": "An outline of an elephant in the savanna for young kids to color",
        "intended_use": "coloring_worksheet",
        "color_preference": "black_and_white",
        "detail_level": "minimal",
        "target_medium": "standard_print",
        "aspect_ratio": "1:1",
        "mode": "optimized",
    }
    response = client.post("/api/v1/generate", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "success"
    assert data["job_id"].startswith("gen_")
    assert "image" in data
    assert data["image"]["url"].startswith("data:image/svg+xml")
    assert data["image"]["format"] == "svg"
    
    assert data["applied_configuration"]["quality_tier"] == "standard"
    assert data["applied_configuration"]["color_mode"] == "monochrome_line_art"
    
    assert data["decision_rationale"]["purpose_identified"] == "coloring_worksheet"
    assert len(data["decision_rationale"]["reasons"]) > 0

    assert data["resource_metrics"]["estimated_cost_usd"] == 0.040
    assert data["resource_metrics"]["baseline_cost_usd"] == 0.080
    assert data["resource_metrics"]["cost_reduction_percent"] == 50.0
    assert data["resource_metrics"]["unit"] == "USD"
    assert data["resource_metrics"]["provenance"] == "mock_illustrative"
    assert data["resource_metrics"]["is_live_billed"] is False
    assert data["resource_metrics"]["calculation_explanation"] is not None
    assert data["resource_metrics"]["latency_seconds"] is not None


def test_generate_image_baseline_mode_comparison():
    payload = {
        "prompt": "An outline of an elephant in the savanna for young kids to color",
        "intended_use": "coloring_worksheet",
        "mode": "baseline",
    }
    response = client.post("/api/v1/generate", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["applied_configuration"]["quality_tier"] == "hd"
    assert data["resource_metrics"]["cost_reduction_percent"] == 0.0


def test_automatic1111_offline_returns_503_no_mock_fallback(monkeypatch):
    """Verifies that when Automatic1111 provider is active and WebUI is unreachable,
    the API returns HTTP 503 and never silently falls back to mock data or fake images.
    """
    from backend.app.config import settings
    monkeypatch.setattr(settings, "active_provider", "automatic1111")
    monkeypatch.setattr(settings, "automatic1111_base_url", "http://127.0.0.1:59999")
    monkeypatch.setattr(settings, "sd_webui_url", "http://127.0.0.1:59999")

    payload = {
        "prompt": "An outline of an elephant for coloring",
        "quality_tier": "eco",
    }
    response = client.post("/api/v1/generate", json=payload)
    assert response.status_code == 503
    data = response.json()
    assert "detail" in data
    assert "Could not connect" in data["detail"] or "AUTOMATIC1111" in data["detail"] or "unreachable" in data["detail"]
