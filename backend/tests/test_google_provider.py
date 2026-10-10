import asyncio
import io
import pytest
from unittest.mock import MagicMock, patch
# pyrefly: ignore [missing-import]
from PIL import Image
# pyrefly: ignore [missing-import]
from google import genai
# pyrefly: ignore [missing-import]
from google.genai import errors

from backend.app.config import settings
from backend.app.schemas.request import (
    ImageGenerationRequest,
    IntendedUseEnum,
    AspectRatioEnum,
    GenerationModeEnum,
)
from backend.app.schemas.response import AppliedConfiguration
from backend.app.providers.google_provider import (
    GoogleImageProvider,
    GoogleProviderError,
    sanitize_error_text,
)
from backend.app.providers import get_image_provider
from backend.app.services.decision_engine import DecisionEngine


@pytest.fixture
def mock_png_bytes():
    """Generates valid in-memory PNG bytes for test responses."""
    img = Image.new("RGB", (640, 480), color="blue")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def test_google_provider_not_configured_raises_error():
    provider = GoogleImageProvider(api_key="")
    assert provider.is_configured() is False

    req = ImageGenerationRequest(
        prompt="A cute cat outline",
        intended_use=IntendedUseEnum.COLORING_WORKSHEET,
    )
    config = AppliedConfiguration(
        model="gemini-2.5-flash-image",
        quality_tier="standard",
        effective_resolution="1024x1024",
        steps=None,
        color_mode="monochrome_line_art",
        prompt_refinement="A cute cat outline, line art",
    )

    with pytest.raises(GoogleProviderError) as exc_info:
        asyncio.run(provider.generate_image(req, config))

    assert exc_info.value.status_code == 503
    assert exc_info.value.error_code == "GOOGLE_AUTH_MISSING"
    assert "GOOGLE_API_KEY" in exc_info.value.message


@patch("backend.app.providers.google_provider.genai.Client")
def test_google_provider_success_standard_tier(mock_client_cls, mock_png_bytes):
    # Construct mock Google GenAI response
    mock_part = MagicMock()
    mock_part.inline_data.data = mock_png_bytes
    mock_part.inline_data.mime_type = "image/png"

    mock_candidate = MagicMock()
    mock_candidate.finish_reason = "STOP"
    mock_candidate.content.parts = [mock_part]

    mock_response = MagicMock()
    mock_response.candidates = [mock_candidate]

    mock_client_instance = MagicMock()
    mock_client_instance.models.generate_content.return_value = mock_response
    mock_client_cls.return_value = mock_client_instance

    provider = GoogleImageProvider(api_key="AIzaSyMockValidTestKey1234567890123456")
    assert provider.is_configured() is True

    req = ImageGenerationRequest(
        prompt="A friendly elephant in savanna",
        intended_use=IntendedUseEnum.COLORING_WORKSHEET,
        aspect_ratio=AspectRatioEnum.SQUARE,
    )
    config = AppliedConfiguration(
        model="gemini-2.5-flash-image",
        quality_tier="standard",
        effective_resolution="1024x1024",
        steps=None,
        color_mode="monochrome_line_art",
        prompt_refinement="A friendly elephant, clean coloring lines",
    )

    result = asyncio.run(provider.generate_image(req, config))

    assert result.format == "png"
    assert result.url.startswith("data:image/png;base64,")
    assert result.width == 640
    assert result.height == 480

    mock_client_instance.models.generate_content.assert_called_once()
    call_kwargs = mock_client_instance.models.generate_content.call_args[1]
    assert call_kwargs["model"] == "gemini-2.5-flash-image"
    assert call_kwargs["contents"] == "A friendly elephant, clean coloring lines"
    assert call_kwargs["config"].response_modalities == ["IMAGE"]
    assert call_kwargs["config"].image_config.aspect_ratio == "1:1"


@patch("backend.app.providers.google_provider.genai.Client")
def test_google_provider_aspect_ratio_widescreen(mock_client_cls, mock_png_bytes):
    mock_part = MagicMock()
    mock_part.inline_data.data = mock_png_bytes
    mock_part.inline_data.mime_type = "image/png"
    mock_candidate = MagicMock()
    mock_candidate.finish_reason = "STOP"
    mock_candidate.content.parts = [mock_part]
    mock_response = MagicMock()
    mock_response.candidates = [mock_candidate]

    mock_client_instance = MagicMock()
    mock_client_instance.models.generate_content.return_value = mock_response
    mock_client_cls.return_value = mock_client_instance

    provider = GoogleImageProvider(api_key="AIzaSyMockValidTestKey1234567890123456")

    req = ImageGenerationRequest(
        prompt="District hallway banner",
        intended_use=IntendedUseEnum.HALLWAY_BANNER,
        aspect_ratio=AspectRatioEnum.WIDESCREEN,
    )
    config = AppliedConfiguration(
        model="gemini-2.5-flash-image",
        quality_tier="hd",
        effective_resolution="1024x1792",
        steps=None,
        color_mode="unconstrained_full_color",
        prompt_refinement="District hallway banner",
    )

    result = asyncio.run(provider.generate_image(req, config))
    assert result.format == "png"

    call_kwargs = mock_client_instance.models.generate_content.call_args[1]
    assert call_kwargs["config"].image_config.aspect_ratio == "16:9"


def test_sanitize_error_text_redacts_api_keys():
    secret_key = "AIzaSyTestGoogleSecretKey9876543210123"
    raw_error = f"Error calling Google API with key={secret_key}: Permission Denied"
    sanitized = sanitize_error_text(raw_error, secret_key)
    assert secret_key not in sanitized
    assert "[REDACTED]" in sanitized


@patch("backend.app.providers.google_provider.genai.Client")
def test_google_provider_401_authentication_failure(mock_client_cls):
    mock_client_instance = MagicMock()
    mock_client_instance.models.generate_content.side_effect = errors.ClientError(
        401, {"error": {"code": 401, "message": "API_KEY_INVALID: The provided API key is invalid."}}
    )
    mock_client_cls.return_value = mock_client_instance

    provider = GoogleImageProvider(api_key="AIzaSyMockKeyInvalid1234567890123456")
    req = ImageGenerationRequest(prompt="Test cat", intended_use=IntendedUseEnum.FLASHCARD)
    config = AppliedConfiguration(
        model="gemini-2.5-flash-image",
        quality_tier="standard",
        effective_resolution="1024x1024",
        steps=None,
        color_mode="auto",
        prompt_refinement="Test cat",
    )

    with pytest.raises(GoogleProviderError) as exc_info:
        asyncio.run(provider.generate_image(req, config))

    assert exc_info.value.status_code == 401
    assert exc_info.value.error_code == "GOOGLE_AUTH_FAILED"
    assert "GOOGLE_API_KEY" in exc_info.value.message


@patch("backend.app.providers.google_provider.genai.Client")
def test_google_provider_429_quota_exhausted(mock_client_cls):
    mock_client_instance = MagicMock()
    mock_client_instance.models.generate_content.side_effect = errors.ClientError(
        429,
        {
            "error": {
                "code": 429,
                "message": "RESOURCE_EXHAUSTED: You exceeded your current quota, please check your plan. limit: 0",
                "status": "RESOURCE_EXHAUSTED",
            }
        },
    )
    mock_client_cls.return_value = mock_client_instance

    provider = GoogleImageProvider(api_key="AIzaSyMockValidTestKey1234567890123456")
    req = ImageGenerationRequest(prompt="Test cat", intended_use=IntendedUseEnum.FLASHCARD)
    config = AppliedConfiguration(
        model="gemini-2.5-flash-image",
        quality_tier="standard",
        effective_resolution="1024x1024",
        steps=None,
        color_mode="auto",
        prompt_refinement="Test cat",
    )

    with pytest.raises(GoogleProviderError) as exc_info:
        asyncio.run(provider.generate_image(req, config))

    assert exc_info.value.status_code == 429
    assert exc_info.value.error_code == "GOOGLE_QUOTA_EXHAUSTED"
    assert "quota" in exc_info.value.message.lower()


@patch("backend.app.providers.google_provider.genai.Client")
def test_google_provider_404_model_not_found(mock_client_cls):
    mock_client_instance = MagicMock()
    mock_client_instance.models.generate_content.side_effect = errors.ClientError(
        404, {"error": {"code": 404, "message": "NOT_FOUND: Model is not found: models/unknown-model"}}
    )
    mock_client_cls.return_value = mock_client_instance

    provider = GoogleImageProvider(api_key="AIzaSyMockValidTestKey1234567890123456", model="unknown-model")
    req = ImageGenerationRequest(prompt="Test cat", intended_use=IntendedUseEnum.FLASHCARD)
    config = AppliedConfiguration(
        model="unknown-model",
        quality_tier="standard",
        effective_resolution="1024x1024",
        steps=None,
        color_mode="auto",
        prompt_refinement="Test cat",
    )

    with pytest.raises(GoogleProviderError) as exc_info:
        asyncio.run(provider.generate_image(req, config))

    assert exc_info.value.status_code == 404
    assert exc_info.value.error_code == "GOOGLE_MODEL_NOT_FOUND"


@patch("backend.app.providers.google_provider.genai.Client")
def test_google_provider_safety_blocked(mock_client_cls):
    mock_candidate = MagicMock()
    mock_candidate.finish_reason = "SAFETY"
    mock_response = MagicMock()
    mock_response.candidates = [mock_candidate]

    mock_client_instance = MagicMock()
    mock_client_instance.models.generate_content.return_value = mock_response
    mock_client_cls.return_value = mock_client_instance

    provider = GoogleImageProvider(api_key="AIzaSyMockValidTestKey1234567890123456")
    req = ImageGenerationRequest(prompt="Dangerous content", intended_use=IntendedUseEnum.FLASHCARD)
    config = AppliedConfiguration(
        model="gemini-2.5-flash-image",
        quality_tier="standard",
        effective_resolution="1024x1024",
        steps=None,
        color_mode="auto",
        prompt_refinement="Dangerous content",
    )

    with pytest.raises(GoogleProviderError) as exc_info:
        asyncio.run(provider.generate_image(req, config))

    assert exc_info.value.status_code == 400
    assert exc_info.value.error_code == "GOOGLE_SAFETY_BLOCKED"


@patch("backend.app.providers.google_provider.genai.Client")
def test_google_provider_no_image_data_raises_502(mock_client_cls):
    mock_part = MagicMock()
    mock_part.inline_data = None  # No image data
    mock_candidate = MagicMock()
    mock_candidate.finish_reason = "STOP"
    mock_candidate.content.parts = [mock_part]
    mock_response = MagicMock()
    mock_response.candidates = [mock_candidate]

    mock_client_instance = MagicMock()
    mock_client_instance.models.generate_content.return_value = mock_response
    mock_client_cls.return_value = mock_client_instance

    provider = GoogleImageProvider(api_key="AIzaSyMockValidTestKey1234567890123456")
    req = ImageGenerationRequest(prompt="Test prompt", intended_use=IntendedUseEnum.FLASHCARD)
    config = AppliedConfiguration(
        model="gemini-2.5-flash-image",
        quality_tier="standard",
        effective_resolution="1024x1024",
        steps=None,
        color_mode="auto",
        prompt_refinement="Test prompt",
    )

    with pytest.raises(GoogleProviderError) as exc_info:
        asyncio.run(provider.generate_image(req, config))

    assert exc_info.value.status_code == 502
    assert exc_info.value.error_code == "GOOGLE_NO_IMAGE_DATA"


def test_google_decision_engine_mapping_when_active():
    orig_provider = settings.active_provider
    try:
        settings.active_provider = "google"
        req = ImageGenerationRequest(
            prompt="An outline of an elephant for coloring",
            intended_use=IntendedUseEnum.COLORING_WORKSHEET,
        )
        decision = DecisionEngine.evaluate(req)

        assert decision.configuration.model == settings.google_model
        assert decision.configuration.quality_tier == "standard"
        assert decision.metrics.estimated_cost_usd == 0.040
        assert "Google Gemini" in decision.metrics.pricing_basis
        assert "Google AI Studio" in decision.metrics.pricing_source
    finally:
        settings.active_provider = orig_provider


def test_google_provider_factory_registration():
    orig_provider = settings.active_provider
    try:
        settings.active_provider = "google"
        provider = get_image_provider()
        assert isinstance(provider, GoogleImageProvider)
        assert provider.provider_id == "google"
    finally:
        settings.active_provider = orig_provider
