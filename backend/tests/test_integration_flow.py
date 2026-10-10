"""End-to-End Integration Tests for ResourceAware.

Verifies:
1. Complete flow from natural-language prompt -> purpose inference -> tier selection
   -> API response schema -> SQLite generation record persistence.
2. Real local WebUI live smoke test: executed only if AUTOMATIC1111 is reachable
   with the REST API enabled. If offline or missing --api, gracefully marked as skipped
   (not run) rather than pretending to pass.
"""

import pytest
import urllib.request
import json
from httpx import ASGITransport, AsyncClient
from backend.app.main import app
from backend.app.services.storage import get_generation_history, clear_generation_history


def is_live_webui_ready() -> bool:
    """Checks whether the live AUTOMATIC1111 server is running with --api enabled."""
    try:
        req = urllib.request.Request("http://127.0.0.1:7860/sdapi/v1/sd-models")
        with urllib.request.urlopen(req, timeout=1.5) as res:
            return res.status == 200
    except Exception:
        return False


@pytest.fixture(autouse=True)
def clean_history():
    clear_generation_history()
    yield
    clear_generation_history()


@pytest.mark.anyio
async def test_full_flow_inference_to_persistence_with_mock(monkeypatch):
    """Verifies complete end-to-end pipeline using mock provider."""
    from backend.app.config import settings
    monkeypatch.setattr(settings, "active_provider", "mock")

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        # 1. Infer purpose endpoint
        infer_res = await client.post(
            "/api/v1/infer-purpose",
            json={"prompt": "Make a simple black-and-white colouring sheet of a butterfly for a seven-year-old."},
        )
        assert infer_res.status_code == 200
        infer_data = infer_res.json()
        assert infer_data["purpose"] == "Children's colouring sheet"
        assert infer_data["recommended_tier"] == "eco"

        # 2. Generate image
        gen_res = await client.post(
            "/api/v1/generate",
            json={
                "prompt": "Make a simple black-and-white colouring sheet of a butterfly for a seven-year-old.",
                "quality_tier": "eco",
            },
        )
        assert gen_res.status_code == 200
        gen_data = gen_res.json()

        assert gen_data["status"] == "success"
        assert gen_data["job_id"].startswith("gen_")
        assert gen_data["applied_configuration"]["quality_tier"] == "eco"
        assert gen_data["resource_metrics"]["work_units"] is not None
        assert gen_data["resource_metrics"]["formula"] is not None
        assert gen_data["resource_metrics"]["assumptions"] is not None

        # 3. Verify record was persisted in SQLite
        history_res = await client.get("/api/v1/history")
        assert history_res.status_code == 200
        history = history_res.json()
        assert len(history) == 1
        assert history[0]["job_id"] == gen_data["job_id"]
        assert history[0]["selected_tier"] == "eco"
        assert history[0]["status"] == "success"

        # 4. Verify analytics updated
        analytics_res = await client.get("/api/v1/analytics")
        assert analytics_res.status_code == 200
        analytics = analytics_res.json()
        assert analytics["total_generations"] == 1
        assert analytics["eco_count"] == 1
        assert analytics["is_empty"] is False


@pytest.mark.anyio
@pytest.mark.skipif(
    not is_live_webui_ready(),
    reason="Live AUTOMATIC1111 WebUI is not reachable with --api at http://127.0.0.1:7860. Smoke test reported as not run (skipped)."
)
async def test_live_webui_txt2img_smoke_test():
    """Live smoke test against real local AUTOMATIC1111 instance.
    Runs ONLY when WebUI is started with --api.
    """
    from backend.app.config import settings
    settings.active_provider = "automatic1111"

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        res = await client.post(
            "/api/v1/generate",
            json={
                "prompt": "A simple black and white coloring sheet of a small cat",
                "quality_tier": "eco",
            },
        )
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "success"
        assert data["image"]["url"].startswith("data:image/png;base64,")
        assert data["resource_metrics"]["measured_elapsed_seconds"] > 0
