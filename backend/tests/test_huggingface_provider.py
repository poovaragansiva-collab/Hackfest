import asyncio
import pytest
from unittest.mock import MagicMock, patch
from PIL import Image
from huggingface_hub.errors import HfHubHTTPError

from backend.app.config import settings
from backend.app.schemas.request import (
    ImageGenerationRequest,
    IntendedUseEnum,
    GenerationModeEnum,
)
from backend.app.schemas.response import AppliedConfiguration
from backend.app.providers.huggingface_provider import (
    HuggingFaceImageProvider,
    HuggingFaceProviderError,
    sanitize_error_text,
)
from backend.app.services.decision_engine import DecisionEngine


@pytest.fixture
def mock_pil_image():
    """Generates a small in-memory PIL image for test mock responses."""
    return Image.new("RGB", (512, 512), color="white")


def test_hf_provider_not_configured_raises_error():
    provider = HuggingFaceImageProvider(token="")
    assert provider.is_configured() is False

    req = ImageGenerationRequest(
        prompt="A cute cat outline",
        intended_use=IntendedUseEnum.COLORING_WORKSHEET,
    )
    config = AppliedConfiguration(
        model="stabilityai/stable-diffusion-xl-base-1.0",
        quality_tier="standard",
        effective_resolution="1024x1024",
        steps=20,
        color_mode="monochrome_line_art",
        prompt_refinement="A cute cat outline, line art",
    )

    with pytest.raises(HuggingFaceProviderError) as exc_info:
        asyncio.run(provider.generate_image(req, config))

    assert exc_info.value.status_code == 503
    assert exc_info.value.error_code == "HF_AUTH_MISSING"
    assert "HF_TOKEN" in exc_info.value.message


@patch("backend.app.providers.huggingface_provider.InferenceClient")
def test_hf_provider_success_standard_tier(mock_client_cls, mock_pil_image):
    mock_client_instance = MagicMock()
    mock_client_instance.text_to_image.return_value = mock_pil_image
    mock_client_cls.return_value = mock_client_instance

    provider = HuggingFaceImageProvider(token="hf_mock_token_for_testing")
    assert provider.is_configured() is True

    req = ImageGenerationRequest(
        prompt="A cute cat outline",
        intended_use=IntendedUseEnum.COLORING_WORKSHEET,
    )
    config = AppliedConfiguration(
        model="stabilityai/stable-diffusion-xl-base-1.0",
        quality_tier="standard",
        effective_resolution="1024x1024",
        steps=20,
        color_mode="monochrome_line_art",
        prompt_refinement="A cute cat outline, line art",
    )

    result = asyncio.run(provider.generate_image(req, config))

    assert result.format == "png"
    assert result.url.startswith("data:image/png;base64,")
    assert result.width == 512
    assert result.height == 512

    # Check client call arguments
    mock_client_instance.text_to_image.assert_called_once()
    call_kwargs = mock_client_instance.text_to_image.call_args.kwargs
    assert call_kwargs["width"] == 1024
    assert call_kwargs["height"] == 1024
    assert call_kwargs["num_inference_steps"] == 20
    assert "shading" in call_kwargs["negative_prompt"]


@patch("backend.app.providers.huggingface_provider.InferenceClient")
def test_hf_provider_success_hd_tier(mock_client_cls, mock_pil_image):
    mock_client_instance = MagicMock()
    mock_client_instance.text_to_image.return_value = mock_pil_image
    mock_client_cls.return_value = mock_client_instance

    provider = HuggingFaceImageProvider(token="hf_mock_token_for_testing")

    req = ImageGenerationRequest(
        prompt="District STEM Hallway Banner",
        intended_use=IntendedUseEnum.HALLWAY_BANNER,
    )
    config = AppliedConfiguration(
        model="stabilityai/stable-diffusion-xl-base-1.0",
        quality_tier="hd",
        effective_resolution="1024x1792",
        steps=40,
        color_mode="vibrant_full_color",
        prompt_refinement="District STEM Hallway Banner",
    )

    result = asyncio.run(provider.generate_image(req, config))
    assert result.format == "png"

    call_kwargs = mock_client_instance.text_to_image.call_args.kwargs
    assert call_kwargs["width"] == 1024
    assert call_kwargs["height"] == 1792
    assert call_kwargs["num_inference_steps"] == 40


def test_sanitize_error_text_removes_tokens():
    token = "hf_1234567890abcdef12345"
    raw_error = f"Unauthorized access using {token} and Bearer abcdef.12345 on remote server"

    sanitized = sanitize_error_text(raw_error, token)
    assert token not in sanitized
    assert "[REDACTED]" in sanitized


@patch("backend.app.providers.huggingface_provider.InferenceClient")
def test_hf_provider_402_insufficient_credits_server_message(mock_client_cls):
    mock_resp = MagicMock()
    mock_resp.status_code = 402
    mock_resp.headers = {}
    mock_client_instance = MagicMock()
    mock_client_instance.text_to_image.side_effect = HfHubHTTPError(
        "Client error '402 Payment Required'",
        response=mock_resp,
        server_message="You have no remaining credits on provider fal-ai.",
    )
    mock_client_cls.return_value = mock_client_instance

    provider = HuggingFaceImageProvider(token="hf_mock_token_for_testing")
    req = ImageGenerationRequest(prompt="Test cat", intended_use=IntendedUseEnum.COLORING_WORKSHEET)
    config = AppliedConfiguration(
        model="stabilityai/stable-diffusion-xl-base-1.0",
        quality_tier="standard",
        effective_resolution="1024x1024",
        steps=20,
        color_mode="monochrome_line_art",
        prompt_refinement="Test cat outline",
    )

    with pytest.raises(HuggingFaceProviderError) as exc_info:
        asyncio.run(provider.generate_image(req, config))

    assert exc_info.value.status_code == 402
    assert exc_info.value.error_code == "HF_INSUFFICIENT_CREDITS"
    assert "402 Payment Required" in exc_info.value.message
    assert "ACTIVE_PROVIDER=mock" in exc_info.value.message


@patch("backend.app.providers.huggingface_provider.InferenceClient")
def test_hf_provider_402_insufficient_credits_in_raw_text(mock_client_cls):
    mock_resp = MagicMock()
    mock_resp.status_code = 402
    mock_resp.headers = {}
    mock_client_instance = MagicMock()
    mock_client_instance.text_to_image.side_effect = HfHubHTTPError(
        "Client error '402 Payment Required': Out of credits",
        response=mock_resp,
    )
    mock_client_cls.return_value = mock_client_instance

    provider = HuggingFaceImageProvider(token="hf_mock_token_for_testing")
    req = ImageGenerationRequest(prompt="Test cat", intended_use=IntendedUseEnum.COLORING_WORKSHEET)
    config = AppliedConfiguration(
        model="stabilityai/stable-diffusion-xl-base-1.0",
        quality_tier="standard",
        effective_resolution="1024x1024",
        steps=20,
        color_mode="monochrome_line_art",
        prompt_refinement="Test cat outline",
    )

    with pytest.raises(HuggingFaceProviderError) as exc_info:
        asyncio.run(provider.generate_image(req, config))

    assert exc_info.value.status_code == 402
    assert exc_info.value.error_code == "HF_INSUFFICIENT_CREDITS"
    assert "402 Payment Required" in exc_info.value.message
    assert "ACTIVE_PROVIDER=mock" in exc_info.value.message


@patch("backend.app.providers.huggingface_provider.InferenceClient")
def test_hf_provider_401_authentication_failure(mock_client_cls):
    mock_resp = MagicMock()
    mock_resp.status_code = 401
    mock_resp.headers = {}
    mock_client_instance = MagicMock()
    mock_client_instance.text_to_image.side_effect = HfHubHTTPError(
        "Client error '401 Unauthorized'",
        response=mock_resp,
        server_message="Invalid token",
    )
    mock_client_cls.return_value = mock_client_instance

    provider = HuggingFaceImageProvider(token="hf_invalid_token_test")
    req = ImageGenerationRequest(prompt="Test cat", intended_use=IntendedUseEnum.COLORING_WORKSHEET)
    config = AppliedConfiguration(
        model="stabilityai/stable-diffusion-xl-base-1.0",
        quality_tier="standard",
        effective_resolution="1024x1024",
        steps=20,
        color_mode="monochrome_line_art",
        prompt_refinement="Test cat outline",
    )

    with pytest.raises(HuggingFaceProviderError) as exc_info:
        asyncio.run(provider.generate_image(req, config))

    assert exc_info.value.status_code == 401
    assert exc_info.value.error_code == "HF_AUTH_FAILED"
    assert "authentication failed" in exc_info.value.message.lower()


@patch("backend.app.providers.huggingface_provider.InferenceClient")
def test_hf_provider_429_rate_limit(mock_client_cls):
    mock_resp = MagicMock()
    mock_resp.status_code = 429
    mock_resp.headers = {}
    mock_client_instance = MagicMock()
    mock_client_instance.text_to_image.side_effect = HfHubHTTPError(
        "Client error '429 Too Many Requests'",
        response=mock_resp,
        server_message="Rate limit reached",
    )
    mock_client_cls.return_value = mock_client_instance

    provider = HuggingFaceImageProvider(token="hf_mock_token_test")
    req = ImageGenerationRequest(prompt="Test cat", intended_use=IntendedUseEnum.COLORING_WORKSHEET)
    config = AppliedConfiguration(
        model="stabilityai/stable-diffusion-xl-base-1.0",
        quality_tier="standard",
        effective_resolution="1024x1024",
        steps=20,
        color_mode="monochrome_line_art",
        prompt_refinement="Test cat outline",
    )

    with pytest.raises(HuggingFaceProviderError) as exc_info:
        asyncio.run(provider.generate_image(req, config))

    assert exc_info.value.status_code == 429
    assert exc_info.value.error_code == "HF_RATE_LIMITED"


@patch("backend.app.providers.huggingface_provider.InferenceClient")
def test_hf_provider_404_model_not_found(mock_client_cls):
    mock_resp = MagicMock()
    mock_resp.status_code = 404
    mock_resp.headers = {}
    mock_client_instance = MagicMock()
    mock_client_instance.text_to_image.side_effect = HfHubHTTPError(
        "Client error '404 Not Found'",
        response=mock_resp,
        server_message="Model does not exist",
    )
    mock_client_cls.return_value = mock_client_instance

    provider = HuggingFaceImageProvider(token="hf_mock_token_test")
    req = ImageGenerationRequest(prompt="Test cat", intended_use=IntendedUseEnum.COLORING_WORKSHEET)
    config = AppliedConfiguration(
        model="nonexistent/model",
        quality_tier="standard",
        effective_resolution="1024x1024",
        steps=20,
        color_mode="monochrome_line_art",
        prompt_refinement="Test cat outline",
    )

    with pytest.raises(HuggingFaceProviderError) as exc_info:
        asyncio.run(provider.generate_image(req, config))

    assert exc_info.value.status_code == 404
    assert exc_info.value.error_code == "HF_MODEL_NOT_FOUND"


@patch("backend.app.providers.huggingface_provider.InferenceClient")
def test_hf_provider_redacts_token_in_unexpected_error(mock_client_cls):
    secret_token = "hf_super_secret_value_12345"
    mock_client_instance = MagicMock()
    mock_client_instance.text_to_image.side_effect = RuntimeError(
        f"Internal crash with key {secret_token} on remote connection"
    )
    mock_client_cls.return_value = mock_client_instance

    provider = HuggingFaceImageProvider(token=secret_token)
    req = ImageGenerationRequest(prompt="Test cat", intended_use=IntendedUseEnum.COLORING_WORKSHEET)
    config = AppliedConfiguration(
        model="stabilityai/stable-diffusion-xl-base-1.0",
        quality_tier="standard",
        effective_resolution="1024x1024",
        steps=20,
        color_mode="monochrome_line_art",
        prompt_refinement="Test cat outline",
    )

    with pytest.raises(HuggingFaceProviderError) as exc_info:
        asyncio.run(provider.generate_image(req, config))

    assert secret_token not in exc_info.value.message
    assert "[REDACTED]" in exc_info.value.message
