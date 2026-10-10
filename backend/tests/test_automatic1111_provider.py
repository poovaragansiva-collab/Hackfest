"""Unit tests for the Automatic1111ImageProvider adapter.

Uses mocked HTTP transports to thoroughly verify:
- Successful response parsing (PNG data URL extraction)
- Loopback security constraint enforcement
- WebUI unavailable (ConnectError) with startup instructions
- WebUI running without '--api' flag (HTTP 404) with remediation guidance
- GPU CUDA Out of Memory error handling
- Generation timeout handling
- Health check interrogation
"""

import pytest
import httpx
from backend.app.providers.automatic1111_provider import (
    Automatic1111ImageProvider,
    Automatic1111ProviderError,
)
from backend.app.schemas.request import ImageGenerationRequest, IntendedUseEnum
from backend.app.schemas.response import AppliedConfiguration

ORIGINAL_ASYNC_CLIENT = httpx.AsyncClient


def test_loopback_security_constraint():
    # Valid loopback addresses
    p1 = Automatic1111ImageProvider("http://127.0.0.1:7860")
    assert p1.base_url == "http://127.0.0.1:7860"

    p2 = Automatic1111ImageProvider("http://localhost:7860")
    assert p2.base_url == "http://localhost:7860"

    # Reject non-loopback addresses
    with pytest.raises(ValueError, match="Security restriction"):
        Automatic1111ImageProvider("http://192.168.1.50:7860")

    with pytest.raises(ValueError, match="Security restriction"):
        Automatic1111ImageProvider("https://external-api.com:7860")


@pytest.mark.anyio
async def test_successful_generation_parsing(monkeypatch):
    provider = Automatic1111ImageProvider("http://127.0.0.1:7860")

    fake_b64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="

    def mock_handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/sdapi/v1/txt2img"
        return httpx.Response(200, json={"images": [fake_b64]})

    transport = httpx.MockTransport(mock_handler)
    monkeypatch.setattr(httpx, "AsyncClient", lambda **kwargs: ORIGINAL_ASYNC_CLIENT(transport=transport))

    req = ImageGenerationRequest(
        prompt="A butterfly coloring sheet for young kids",
        intended_use=IntendedUseEnum.COLORING_SHEET,
    )
    config = AppliedConfiguration(
        model="stable-diffusion-v1-5",
        quality_tier="eco",
        effective_resolution="384x384",
        steps=10,
        color_mode="monochrome_line_art",
        prompt_refinement="A butterfly coloring sheet, bold outlines",
    )

    image_data = await provider.generate_image(req, config)

    assert image_data.format == "png"
    assert image_data.width == 384
    assert image_data.height == 384
    assert image_data.url.startswith("data:image/png;base64,")
    assert fake_b64 in image_data.url
    assert hasattr(image_data, "_measured_elapsed")


@pytest.mark.anyio
async def test_webui_offline_connection_error(monkeypatch):
    provider = Automatic1111ImageProvider("http://127.0.0.1:7860")

    def mock_handler(request: httpx.Request):
        raise httpx.ConnectError("Connection refused")

    transport = httpx.MockTransport(mock_handler)
    monkeypatch.setattr(httpx, "AsyncClient", lambda **kwargs: ORIGINAL_ASYNC_CLIENT(transport=transport))

    req = ImageGenerationRequest(
        prompt="Test prompt",
        intended_use=IntendedUseEnum.EDUCATIONAL_POSTER,
    )
    config = AppliedConfiguration(
        model="stable-diffusion-v1-5",
        quality_tier="standard",
        effective_resolution="512x512",
        steps=18,
        color_mode="standard_color",
        prompt_refinement="Test prompt",
    )

    with pytest.raises(Automatic1111ProviderError) as exc_info:
        await provider.generate_image(req, config)

    assert exc_info.value.status_code == 503
    assert exc_info.value.error_code == "webui_unreachable"
    assert "--api" in exc_info.value.instruction


@pytest.mark.anyio
async def test_webui_api_not_enabled_404(monkeypatch):
    provider = Automatic1111ImageProvider("http://127.0.0.1:7860")

    def mock_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, text="Not Found")

    transport = httpx.MockTransport(mock_handler)
    monkeypatch.setattr(httpx, "AsyncClient", lambda **kwargs: ORIGINAL_ASYNC_CLIENT(transport=transport))

    req = ImageGenerationRequest(
        prompt="Test prompt",
        intended_use=IntendedUseEnum.EDUCATIONAL_POSTER,
    )
    config = AppliedConfiguration(
        model="stable-diffusion-v1-5",
        quality_tier="standard",
        effective_resolution="512x512",
        steps=18,
        color_mode="standard_color",
        prompt_refinement="Test prompt",
    )

    with pytest.raises(Automatic1111ProviderError) as exc_info:
        await provider.generate_image(req, config)

    assert exc_info.value.status_code == 503
    assert exc_info.value.error_code == "api_not_enabled"
    assert "webui-user.bat" in exc_info.value.instruction


@pytest.mark.anyio
async def test_cuda_out_of_memory_error(monkeypatch):
    provider = Automatic1111ImageProvider("http://127.0.0.1:7860")

    def mock_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, text="torch.cuda.OutOfMemoryError: CUDA out of memory. Tried to allocate 2.00 GiB")

    transport = httpx.MockTransport(mock_handler)
    monkeypatch.setattr(httpx, "AsyncClient", lambda **kwargs: ORIGINAL_ASYNC_CLIENT(transport=transport))

    req = ImageGenerationRequest(
        prompt="Very large banner",
        intended_use=IntendedUseEnum.HALLWAY_BANNER,
    )
    config = AppliedConfiguration(
        model="stable-diffusion-v1-5",
        quality_tier="high",
        effective_resolution="512x768",
        steps=28,
        color_mode="standard_color",
        prompt_refinement="Very large banner",
    )

    with pytest.raises(Automatic1111ProviderError) as exc_info:
        await provider.generate_image(req, config)

    assert exc_info.value.status_code == 500
    assert exc_info.value.error_code == "cuda_out_of_memory"
    assert "medvram" in exc_info.value.instruction or "lowvram" in exc_info.value.instruction


@pytest.mark.anyio
async def test_generation_timeout_error(monkeypatch):
    provider = Automatic1111ImageProvider("http://127.0.0.1:7860")

    def mock_handler(request: httpx.Request):
        raise httpx.ReadTimeout("Generation timed out")

    transport = httpx.MockTransport(mock_handler)
    monkeypatch.setattr(httpx, "AsyncClient", lambda **kwargs: ORIGINAL_ASYNC_CLIENT(transport=transport))

    req = ImageGenerationRequest(prompt="Test prompt")
    config = AppliedConfiguration(
        model="stable-diffusion-v1-5",
        quality_tier="high",
        effective_resolution="512x768",
        steps=28,
        color_mode="standard_color",
        prompt_refinement="Test prompt",
    )

    with pytest.raises(Automatic1111ProviderError) as exc_info:
        await provider.generate_image(req, config)

    assert exc_info.value.status_code == 504
    assert exc_info.value.error_code == "generation_timeout"


@pytest.mark.anyio
async def test_empty_images_response_error(monkeypatch):
    provider = Automatic1111ImageProvider("http://127.0.0.1:7860")

    def mock_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"images": []})

    transport = httpx.MockTransport(mock_handler)
    monkeypatch.setattr(httpx, "AsyncClient", lambda **kwargs: ORIGINAL_ASYNC_CLIENT(transport=transport))

    req = ImageGenerationRequest(prompt="Test prompt")
    config = AppliedConfiguration(
        model="stable-diffusion-v1-5",
        quality_tier="eco",
        effective_resolution="384x384",
        steps=10,
        color_mode="monochrome_line_art",
        prompt_refinement="Test prompt",
    )

    with pytest.raises(Automatic1111ProviderError) as exc_info:
        await provider.generate_image(req, config)

    assert exc_info.value.status_code == 502
    assert exc_info.value.error_code == "empty_image_response"


@pytest.mark.anyio
async def test_internal_server_error_reporting(monkeypatch):
    provider = Automatic1111ImageProvider("http://127.0.0.1:7860")

    def mock_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, text="RuntimeError: Failed to process latent tensor")

    transport = httpx.MockTransport(mock_handler)
    monkeypatch.setattr(httpx, "AsyncClient", lambda **kwargs: ORIGINAL_ASYNC_CLIENT(transport=transport))

    req = ImageGenerationRequest(prompt="Test prompt")
    config = AppliedConfiguration(
        model="stable-diffusion-v1-5",
        quality_tier="standard",
        effective_resolution="512x512",
        steps=18,
        color_mode="standard_color",
        prompt_refinement="Test prompt",
    )

    with pytest.raises(Automatic1111ProviderError) as exc_info:
        await provider.generate_image(req, config)

    assert exc_info.value.status_code == 500
    assert exc_info.value.error_code == "internal_generation_error"


@pytest.mark.anyio
async def test_health_check_reporting(monkeypatch):
    provider = Automatic1111ImageProvider("http://127.0.0.1:7860")

    def mock_handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/sdapi/v1/sd-models":
            return httpx.Response(200, json=[{"title": "v1-5-pruned-emaonly.safetensors", "model_name": "v1-5-pruned"}])
        return httpx.Response(404)

    transport = httpx.MockTransport(mock_handler)
    monkeypatch.setattr(httpx, "AsyncClient", lambda **kwargs: ORIGINAL_ASYNC_CLIENT(transport=transport))

    health = await provider.check_health()
    assert health["reachable"] is True
    assert health["api_enabled"] is True
    assert "v1-5" in health["model"]


@pytest.mark.anyio
async def test_health_check_api_disabled(monkeypatch):
    provider = Automatic1111ImageProvider("http://127.0.0.1:7860")

    def mock_handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/sdapi/v1/sd-models":
            return httpx.Response(404, text="Not Found")
        if request.url.path == "/":
            return httpx.Response(200, text="<html>Gradio</html>")
        return httpx.Response(404)

    transport = httpx.MockTransport(mock_handler)
    monkeypatch.setattr(httpx, "AsyncClient", lambda **kwargs: ORIGINAL_ASYNC_CLIENT(transport=transport))

    health = await provider.check_health()
    assert health["reachable"] is True
    assert health["api_enabled"] is False


@pytest.mark.anyio
async def test_health_check_webui_offline(monkeypatch):
    provider = Automatic1111ImageProvider("http://127.0.0.1:7860")

    def mock_handler(request: httpx.Request):
        raise httpx.ConnectError("Connection refused")

    transport = httpx.MockTransport(mock_handler)
    monkeypatch.setattr(httpx, "AsyncClient", lambda **kwargs: ORIGINAL_ASYNC_CLIENT(transport=transport))

    health = await provider.check_health()
    assert health["reachable"] is False
    assert health["api_enabled"] is False
