"""Tests for Local SQLite Storage and Analytics Persistence.

Verifies:
- Saving real generation records
- Retrieving history (newest first)
- Empty state analytics reporting (genuine zeros, no fake figures)
- Correct aggregation across real records
- History clearing
"""

import pytest
from backend.app.services.storage import (
    init_db,
    save_generation_record,
    get_generation_history,
    clear_generation_history,
    get_real_analytics,
)


@pytest.fixture(autouse=True)
def clean_db():
    clear_generation_history()
    yield
    clear_generation_history()


def test_empty_analytics_state():
    analytics = get_real_analytics()
    assert analytics["total_generations"] == 0
    assert analytics["eco_count"] == 0
    assert analytics["standard_count"] == 0
    assert analytics["high_count"] == 0
    assert analytics["overridden_count"] == 0
    assert analytics["total_compute_units"] == 0.0
    assert analytics["baseline_units"] == 0.0
    assert analytics["units_saved"] == 0.0
    assert analytics["overall_savings_percent"] == 0.0
    assert analytics["avg_elapsed_seconds"] == 0.0
    assert analytics["is_empty"] is True


def test_save_and_retrieve_generation_records():
    record1 = {
        "job_id": "gen_test001",
        "timestamp": "2026-10-11T01:00:00Z",
        "prompt": "Coloring sheet butterfly",
        "inferred_purpose": "Children's colouring sheet",
        "recommended_tier": "eco",
        "selected_tier": "eco",
        "tier_overridden": False,
        "width": 384,
        "height": 384,
        "steps": 10,
        "elapsed_seconds": 1.45,
        "compute_work_units": 0.1339,
        "savings_percent": 86.6,
        "model": "stable-diffusion-v1-5",
        "provider": "automatic1111",
        "status": "success",
        "image_url": "data:image/png;base64,sample1",
    }
    record2 = {
        "job_id": "gen_test002",
        "timestamp": "2026-10-11T01:05:00Z",
        "prompt": "Educational poster water cycle",
        "inferred_purpose": "Educational poster",
        "recommended_tier": "standard",
        "selected_tier": "high",
        "tier_overridden": True,
        "width": 512,
        "height": 768,
        "steps": 28,
        "elapsed_seconds": 3.82,
        "compute_work_units": 1.0,
        "savings_percent": 0.0,
        "model": "stable-diffusion-v1-5",
        "provider": "automatic1111",
        "status": "success",
        "image_url": "data:image/png;base64,sample2",
    }

    save_generation_record(record1)
    save_generation_record(record2)

    history = get_generation_history(limit=10)
    assert len(history) == 2
    # Newest first
    assert history[0]["job_id"] == "gen_test002"
    assert history[1]["job_id"] == "gen_test001"

    # Analytics aggregation
    analytics = get_real_analytics()
    assert analytics["total_generations"] == 2
    assert analytics["eco_count"] == 1
    assert analytics["standard_count"] == 0
    assert analytics["high_count"] == 1
    assert analytics["overridden_count"] == 1
    # total_compute_units = 0.1339 + 1.0 = 1.1339 -> round 1.134
    assert round(analytics["total_compute_units"], 3) == 1.134
    assert analytics["baseline_units"] == 2.0
    # units saved = 2.0 - 1.134 = 0.866
    assert round(analytics["units_saved"], 3) == 0.866
    assert analytics["overall_savings_percent"] == round((0.866 / 2.0) * 100, 1)
    assert 2.63 <= analytics["avg_elapsed_seconds"] <= 2.64
    assert analytics["is_empty"] is False


def test_save_output_artifact_and_serve():
    from backend.app.services.storage import save_output_artifact, OUTPUTS_DIR
    from fastapi.testclient import TestClient
    from backend.app.main import app
    import base64
    import os

    client = TestClient(app)

    # 1. Save PNG artifact
    sample_bytes = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4"
    sample_b64 = base64.b64encode(sample_bytes).decode("utf-8")
    data_uri = f"data:image/png;base64,{sample_b64}"

    artifact_url = save_output_artifact("gen_artifact_test001", data_uri, "png")
    assert artifact_url == "/api/v1/outputs/gen_artifact_test001.png"

    expected_file = os.path.join(OUTPUTS_DIR, "gen_artifact_test001.png")
    assert os.path.isfile(expected_file)

    # 2. Serve PNG artifact via API
    resp = client.get("/api/v1/outputs/gen_artifact_test001.png")
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "image/png"
    assert resp.content == sample_bytes

    # 3. Non-existent file returns 404
    resp_404 = client.get("/api/v1/outputs/gen_nonexistent_999.png")
    assert resp_404.status_code == 404

    # 4. Path traversal attempt returns 400 (rejected by regex) or 403
    resp_traversal = client.get("/api/v1/outputs/..%2F..%2Fetc%2Fpasswd")
    assert resp_traversal.status_code in (400, 404)

    # 5. Invalid extension returns 400
    resp_invalid_ext = client.get("/api/v1/outputs/script.exe")
    assert resp_invalid_ext.status_code == 400
