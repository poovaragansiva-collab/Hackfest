import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


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
