import asyncio
import base64
import io
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
# pyrefly: ignore [missing-import]
from PIL import Image
import httpx

from backend.app.config import settings
from backend.app.schemas.request import (
    ImageGenerationRequest,
    IntendedUseEnum,
    AspectRatioEnum,
    GenerationModeEnum,
)
from backend.app.schemas.response import AppliedConfiguration
from backend.app.providers.openrouter_provider import (
    OpenRouterImageProvider,
    OpenRouterProviderError,
    sanitize_error_text,
)
from backend.app.providers import get_image_provider
from backend.app.services.decision_engine import DecisionEngine


@pytest.fixture
def mock_png_bytes():
    """Generates valid in-memory PNG bytes for mock responses."""
    img = Image.new("RGB", (1024, 1024), color="indigo")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


@pytest.fixture
def mock_png_base64(mock_png_bytes):
    return base64.b64encode(mock_png_bytes).decode("utf-8")


def test_openrouter_provider_not_configured():
    provider = OpenRouterImageProvider(api_key="")
    assert provider.is_configured() is False

    req = ImageGenerationRequest(
        prompt="A cartoon puppy for colouring",
        intended_use=IntendedUseEnum.COLORING_WORKSHEET,
    )
    config = AppliedConfiguration(
        model="sourceful/riverflow-v2-fast",
        quality_tier="standard",
        effective_resolution="1024x1024",
        steps=None,
        color_mode="monochrome_line_art",
        prompt_refinement="A cartoon puppy for colouring, line art",
    )

    with pytest.raises(OpenRouterProviderError) as exc_info:
        asyncio.run(provider.generate_image(req, config))

    assert exc_info.value.status_code == 503
    assert exc_info.value.error_code == "OPENROUTER_AUTH_MISSING"
    assert "OPENROUTER_API_KEY" in exc_info.value.message


def test_sanitize_error_text():
    key = "sk-or-v1-abcdef1234567890abcdef1234567890"
    raw = f"Error communicating with key {key} and Bearer abc.xyz.123"
    sanitized = sanitize_error_text(raw, key)
    assert key not in sanitized
    assert "[REDACTED]" in sanitized


@patch("httpx.AsyncClient.post")
def test_openrouter_provider_success_standard_tier(mock_post, mock_png_base64):
    provider = OpenRouterImageProvider(api_key="sk-or-v1-testkey12345")
    assert provider.is_configured() is True

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "data": [{"b64_json": mock_png_base64}],
        "usage": {"total_cost": 0.0035},
    }
    mock_post.return_value = mock_resp

    req = ImageGenerationRequest(
        prompt="Solar system poster",
        intended_use=IntendedUseEnum.CLASSROOM_HANDOUT,
        aspect_ratio=AspectRatioEnum.SQUARE,
    )
    config = AppliedConfiguration(
        model="sourceful/riverflow-v2-fast",
        quality_tier="standard",
        effective_resolution="1024x1024",
        steps=20,
        color_mode="full_color",
        prompt_refinement="Solar system poster, educational diagram",
    )

    result = asyncio.run(provider.generate_image(req, config))

    assert result.url.startswith("data:image/png;base64,")
    assert result.width == 1024
    assert result.height == 1024
    assert result.format == "png"
    assert result.actual_cost_usd == 0.0035

    # Verify payload format
    call_kwargs = mock_post.call_args.kwargs
    payload = call_kwargs["json"]
    assert payload["image_size"] == "1K"
    assert payload["aspect_ratio"] == "1:1"
    assert payload["prompt"] == "Solar system poster, educational diagram"


@patch("httpx.AsyncClient.post")
def test_openrouter_provider_success_hd_tier(mock_post, mock_png_base64):
    provider = OpenRouterImageProvider(api_key="sk-or-v1-testkey12345")

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "data": [{"b64_json": mock_png_base64}],
        "usage": {"total_cost": 0.008},
    }
    mock_post.return_value = mock_resp

    req = ImageGenerationRequest(
        prompt="District Science Fair Banner",
        intended_use=IntendedUseEnum.HALLWAY_BANNER,
        aspect_ratio=AspectRatioEnum.PORTRAIT_TALL,
    )
    config = AppliedConfiguration(
        model="sourceful/riverflow-v2-fast",
        quality_tier="hd",
        effective_resolution="1024x1792",
        steps=40,
        color_mode="vibrant_full_color",
        prompt_refinement="District Science Fair Banner, high fidelity",
    )

    result = asyncio.run(provider.generate_image(req, config))
    assert result.format == "png"

    call_kwargs = mock_post.call_args.kwargs
    payload = call_kwargs["json"]
    assert payload["image_size"] == "2K"
    assert payload["aspect_ratio"] == "9:16"


@patch("httpx.AsyncClient.post")
def test_openrouter_provider_url_fallback(mock_post):
    provider = OpenRouterImageProvider(api_key="sk-or-v1-testkey12345")

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "data": [{"url": "https://openrouter.ai/sample_image.png"}],
        "usage": {"total_cost": 0.004},
    }
    mock_post.return_value = mock_resp

    req = ImageGenerationRequest(
        prompt="Classroom poster",
        intended_use=IntendedUseEnum.CLASSROOM_HANDOUT,
    )
    config = AppliedConfiguration(
        model="sourceful/riverflow-v2-fast",
        quality_tier="standard",
        effective_resolution="1024x1024",
        steps=20,
        color_mode="full_color",
        prompt_refinement="Classroom poster",
    )

    result = asyncio.run(provider.generate_image(req, config))
    assert result.url == "https://openrouter.ai/sample_image.png"
    assert result.actual_cost_usd == 0.004


@patch("httpx.AsyncClient.post")
def test_openrouter_provider_insufficient_credits_402(mock_post):
    provider = OpenRouterImageProvider(api_key="sk-or-v1-testkey12345")

    mock_resp = MagicMock()
    mock_resp.status_code = 402
    mock_resp.json.return_value = {
        "error": {"message": "Insufficient credits to complete request."}
    }
    mock_post.return_value = mock_resp

    req = ImageGenerationRequest(
        prompt="Math worksheet geometry",
        intended_use=IntendedUseEnum.CLASSROOM_HANDOUT,
    )
    config = AppliedConfiguration(
        model="sourceful/riverflow-v2-fast",
        quality_tier="standard",
        effective_resolution="1024x1024",
        steps=20,
        color_mode="black_and_white",
        prompt_refinement="Math worksheet geometry",
    )

    with pytest.raises(OpenRouterProviderError) as exc_info:
        asyncio.run(provider.generate_image(req, config))

    assert exc_info.value.status_code == 402
    assert exc_info.value.error_code == "OPENROUTER_INSUFFICIENT_CREDITS"
    assert "ACTIVE_PROVIDER=mock" in exc_info.value.message


@patch("httpx.AsyncClient.post")
def test_openrouter_provider_rate_limit_429(mock_post):
    provider = OpenRouterImageProvider(api_key="sk-or-v1-testkey12345")

    mock_resp = MagicMock()
    mock_resp.status_code = 429
    mock_resp.json.return_value = {
        "error": {"message": "Rate limit reached."}
    }
    mock_post.return_value = mock_resp

    req = ImageGenerationRequest(
        prompt="Flashcard lion",
        intended_use=IntendedUseEnum.FLASHCARD,
    )
    config = AppliedConfiguration(
        model="sourceful/riverflow-v2-fast",
        quality_tier="standard",
        effective_resolution="1024x1024",
        steps=20,
        color_mode="color",
        prompt_refinement="Flashcard lion",
    )

    with pytest.raises(OpenRouterProviderError) as exc_info:
        asyncio.run(provider.generate_image(req, config))

    assert exc_info.value.status_code == 429
    assert exc_info.value.error_code == "OPENROUTER_RATE_LIMITED"


@patch("httpx.AsyncClient.post")
def test_openrouter_provider_401_unauthorized(mock_post):
    test_key = "sk-or-v1-secretkey9876543210"
    provider = OpenRouterImageProvider(api_key=test_key)

    mock_resp = MagicMock()
    mock_resp.status_code = 401
    mock_resp.json.return_value = {
        "error": {"code": 401, "message": f"User key not found: {test_key}"}
    }
    mock_post.return_value = mock_resp

    req = ImageGenerationRequest(
        prompt="Coloring sheet dinosaur",
        intended_use=IntendedUseEnum.COLORING_WORKSHEET,
    )
    config = AppliedConfiguration(
        model="sourceful/riverflow-v2-fast",
        quality_tier="standard",
        effective_resolution="1024x1024",
        steps=20,
        color_mode="monochrome_line_art",
        prompt_refinement="Coloring sheet dinosaur",
    )

    with pytest.raises(OpenRouterProviderError) as exc_info:
        asyncio.run(provider.generate_image(req, config))

    assert exc_info.value.status_code == 401
    assert exc_info.value.error_code == "OPENROUTER_UNAUTHORIZED"
    # Verify the secret key is NOT exposed in the formatted exception message
    assert test_key not in exc_info.value.message
    assert "[REDACTED]" in exc_info.value.message
    assert "OPENROUTER_API_KEY in backend/.env" in exc_info.value.message


@patch("httpx.AsyncClient.post")
def test_openrouter_provider_403_forbidden(mock_post):
    provider = OpenRouterImageProvider(api_key="sk-or-v1-testkey12345")

    mock_resp = MagicMock()
    mock_resp.status_code = 403
    mock_resp.json.return_value = {
        "error": {"message": "Account does not have access to this model or region."}
    }
    mock_post.return_value = mock_resp

    req = ImageGenerationRequest(
        prompt="Flashcard lion",
        intended_use=IntendedUseEnum.FLASHCARD,
    )
    config = AppliedConfiguration(
        model="sourceful/riverflow-v2-fast",
        quality_tier="standard",
        effective_resolution="1024x1024",
        steps=20,
        color_mode="color",
        prompt_refinement="Flashcard lion",
    )

    with pytest.raises(OpenRouterProviderError) as exc_info:
        asyncio.run(provider.generate_image(req, config))

    assert exc_info.value.status_code == 403
    assert exc_info.value.error_code == "OPENROUTER_FORBIDDEN"
    assert "access forbidden" in exc_info.value.message.lower()


@patch("httpx.AsyncClient.post")
def test_openrouter_provider_authorization_header(mock_post, mock_png_base64):
    provider = OpenRouterImageProvider(api_key="sk-or-v1-testkey12345")

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "data": [{"b64_json": mock_png_base64}],
    }
    mock_post.return_value = mock_resp

    req = ImageGenerationRequest(
        prompt="Poster",
        intended_use=IntendedUseEnum.CLASSROOM_HANDOUT,
    )
    config = AppliedConfiguration(
        model="sourceful/riverflow-v2-fast",
        quality_tier="standard",
        effective_resolution="1024x1024",
        steps=20,
        color_mode="full_color",
        prompt_refinement="Poster",
    )

    asyncio.run(provider.generate_image(req, config))

    call_headers = mock_post.call_args.kwargs["headers"]
    assert "Authorization" in call_headers
    assert call_headers["Authorization"] == "Bearer sk-or-v1-testkey12345"
    assert call_headers["Content-Type"] == "application/json"


@patch("httpx.AsyncClient.post")
def test_openrouter_provider_404_model_not_found(mock_post):
    provider = OpenRouterImageProvider(api_key="sk-or-v1-testkey12345", model="nonexistent/model")

    mock_resp = MagicMock()
    mock_resp.status_code = 404
    mock_resp.json.return_value = {
        "error": {"message": "Model not found."}
    }
    mock_post.return_value = mock_resp

    req = ImageGenerationRequest(
        prompt="Flashcard lion",
        intended_use=IntendedUseEnum.FLASHCARD,
    )
    config = AppliedConfiguration(
        model="nonexistent/model",
        quality_tier="standard",
        effective_resolution="1024x1024",
        steps=20,
        color_mode="color",
        prompt_refinement="Flashcard lion",
    )

    with pytest.raises(OpenRouterProviderError) as exc_info:
        asyncio.run(provider.generate_image(req, config))

    assert exc_info.value.status_code == 404
    assert exc_info.value.error_code == "OPENROUTER_MODEL_NOT_FOUND"


def test_openrouter_decision_engine_mapping_when_active(monkeypatch):
    monkeypatch.setattr(settings, "active_provider", "openrouter")
    req = ImageGenerationRequest(
        prompt="A simple coloring sheet of a butterfly",
        intended_use=IntendedUseEnum.COLORING_WORKSHEET,
        mode=GenerationModeEnum.OPTIMIZED,
    )
    decision = DecisionEngine.evaluate(req)

    assert decision.configuration.model == settings.openrouter_model
    assert decision.configuration.quality_tier == "standard"
    assert decision.configuration.effective_resolution == "1024x1024"
    assert decision.metrics.estimated_cost_usd == 0.020
    assert decision.metrics.baseline_cost_usd == 0.040
    assert decision.metrics.cost_reduction_percent == 50.0
    assert decision.metrics.provenance == "reference_estimate"
    assert "OpenRouter" in decision.metrics.pricing_basis


def test_openrouter_decision_engine_baseline_mode(monkeypatch):
    monkeypatch.setattr(settings, "active_provider", "openrouter")
    req = ImageGenerationRequest(
        prompt="A simple coloring sheet of a butterfly",
        intended_use=IntendedUseEnum.COLORING_WORKSHEET,
        mode=GenerationModeEnum.BASELINE,
    )
    decision = DecisionEngine.evaluate(req)

    assert decision.configuration.model == settings.openrouter_model
    assert decision.configuration.quality_tier == "hd"
    assert decision.metrics.estimated_cost_usd == 0.040
    assert decision.metrics.baseline_cost_usd == 0.040
    assert decision.metrics.cost_reduction_percent == 0.0


def test_factory_resolves_openrouter_provider(monkeypatch):
    monkeypatch.setattr(settings, "active_provider", "openrouter")
    provider = get_image_provider()
    assert isinstance(provider, OpenRouterImageProvider)
    assert provider.provider_id == "openrouter"


def test_openrouter_config_loading(monkeypatch):
    """Verifies Settings properly loads openrouter_api_key from environment."""
    from backend.app.config import Settings
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-v1-mockenvkey00112233")
    monkeypatch.setenv("ACTIVE_PROVIDER", "openrouter")
    custom_settings = Settings(_env_file=None)
    assert custom_settings.active_provider == "openrouter"
    assert custom_settings.openrouter_api_key == "sk-or-v1-mockenvkey00112233"


@patch("httpx.AsyncClient.post")
def test_openrouter_api_route_401_error_mapping(mock_post, monkeypatch):
    """Tests FastAPI /api/v1/generate endpoint error mapping when OpenRouter returns HTTP 401."""
    from fastapi.testclient import TestClient
    from backend.app.main import app

    monkeypatch.setattr(settings, "active_provider", "openrouter")
    monkeypatch.setattr(settings, "openrouter_api_key", "sk-or-v1-testauthkey123")

    mock_resp = MagicMock()
    mock_resp.status_code = 401
    mock_resp.json.return_value = {
        "error": {"code": 401, "message": "User key not found: sk-or-v1-testauthkey123"}
    }
    mock_post.return_value = mock_resp

    test_client = TestClient(app, raise_server_exceptions=False)
    payload = {
        "prompt": "Solar system diagram",
        "intended_use": "classroom_handout",
        "mode": "optimized",
    }
    resp = test_client.post("/api/v1/generate", json=payload)

    assert resp.status_code == 401
    data = resp.json()
    assert "detail" in data
    assert "OpenRouter authentication failed (HTTP 401)" in data["detail"]
    assert "OPENROUTER_API_KEY in backend/.env" in data["detail"]
    assert "sk-or-v1-testauthkey123" not in data["detail"]
    assert "HF_TOKEN" not in data["detail"]


@patch("httpx.AsyncClient.post")
def test_openrouter_api_route_403_error_mapping(mock_post, monkeypatch):
    """Tests FastAPI /api/v1/generate endpoint error mapping when OpenRouter returns HTTP 403."""
    from fastapi.testclient import TestClient
    from backend.app.main import app

    monkeypatch.setattr(settings, "active_provider", "openrouter")
    monkeypatch.setattr(settings, "openrouter_api_key", "sk-or-v1-testauthkey123")

    mock_resp = MagicMock()
    mock_resp.status_code = 403
    mock_resp.json.return_value = {
        "error": {"message": "Account forbidden from accessing image models."}
    }
    mock_post.return_value = mock_resp

    test_client = TestClient(app, raise_server_exceptions=False)
    payload = {
        "prompt": "Solar system diagram",
        "intended_use": "classroom_handout",
        "mode": "optimized",
    }
    resp = test_client.post("/api/v1/generate", json=payload)

    assert resp.status_code == 403
    data = resp.json()
    assert "detail" in data
    assert "OpenRouter access forbidden (HTTP 403)" in data["detail"]
    assert "OPENROUTER_API_KEY" not in data["detail"]
    assert "HF_TOKEN" not in data["detail"]


def test_openrouter_api_route_503_missing_key(monkeypatch):
    """Tests FastAPI /api/v1/generate endpoint when OPENROUTER_API_KEY is not set."""
    from fastapi.testclient import TestClient
    from backend.app.main import app

    monkeypatch.setattr(settings, "active_provider", "openrouter")
    monkeypatch.setattr(settings, "openrouter_api_key", "")

    test_client = TestClient(app, raise_server_exceptions=False)
    payload = {
        "prompt": "Solar system diagram",
        "intended_use": "classroom_handout",
        "mode": "optimized",
    }
    resp = test_client.post("/api/v1/generate", json=payload)

    assert resp.status_code == 503
    data = resp.json()
    assert "detail" in data
    assert "OpenRouter API key is not configured" in data["detail"]
    assert "OPENROUTER_API_KEY in backend/.env" in data["detail"]

