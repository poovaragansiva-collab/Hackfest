"""Production AUTOMATIC1111 Stable Diffusion WebUI Local Provider Adapter.

Integrates with local AUTOMATIC1111 Stable Diffusion WebUI API running on Windows:
- Endpoints: POST /sdapi/v1/txt2img, GET /sdapi/v1/sd-models
- Monotonic timing with time.perf_counter()
- Concurrency serialization via asyncio.Lock() to prevent OOM on 4 GB RTX 2050
- Loopback security constraint (127.0.0.1/localhost only)
- Real base64 PNG decoding to data URI
- Explicit error classification (WebUI offline, --api flag missing, OOM, timeout)
- Never returns fake/placeholder images or simulates success
"""

import asyncio
import logging
import time
from urllib.parse import urlparse
from typing import Optional, Dict, Any, List
import httpx

from .base import BaseImageProvider
from ..config import settings
from ..schemas.request import ImageGenerationRequest
from ..schemas.response import AppliedConfiguration, ImageData

logger = logging.getLogger(__name__)

# GPU Concurrency Lock: Prevents simultaneous generation requests from exhausting
# the 4 GB VRAM on NVIDIA RTX 2050
_GPU_GENERATION_LOCK = asyncio.Lock()


class Automatic1111ProviderError(Exception):
    """Specific error for AUTOMATIC1111 WebUI communication issues."""
    def __init__(self, message: str, status_code: int = 503, error_code: str = "webui_error", instruction: Optional[str] = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.instruction = instruction or ""


class Automatic1111ImageProvider(BaseImageProvider):
    """Production provider for AUTOMATIC1111 Stable Diffusion WebUI."""

    def __init__(self, base_url: Optional[str] = None):
        raw_url = (
            base_url
            or getattr(settings, "sd_webui_url", None)
            or getattr(settings, "automatic1111_base_url", None)
            or "http://127.0.0.1:7860"
        )
        self.base_url = self._validate_and_sanitize_url(raw_url)

    @staticmethod
    def _validate_and_sanitize_url(url: str) -> str:
        """Enforces loopback restriction to prevent SSRF and arbitrary remote execution."""
        clean = (url or "http://127.0.0.1:7860").rstrip("/")
        parsed = urlparse(clean)
        hostname = (parsed.hostname or "").lower()

        if hostname not in ("127.0.0.1", "localhost", "::1"):
            raise ValueError(
                f"Security restriction: Local AUTOMATIC1111 provider requires a loopback address "
                f"(127.0.0.1 or localhost), received: '{hostname}'."
            )
        return clean

    @property
    def provider_id(self) -> str:
        return "automatic1111"

    def is_configured(self) -> bool:
        return bool(self.base_url)

    async def check_health(self) -> Dict[str, Any]:
        """Checks WebUI availability, verifies if REST API is enabled, and identifies loaded model."""
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                res = await client.get(f"{self.base_url}/sdapi/v1/sd-models")
                if res.status_code == 200:
                    models = res.json()
                    model_title = "Unknown Model"
                    if models and isinstance(models, list):
                        model_title = models[0].get("title") or models[0].get("model_name") or "v1-5-pruned"
                        try:
                            opt_res = await client.get(f"{self.base_url}/sdapi/v1/options", timeout=2.0)
                            if opt_res.status_code == 200:
                                opt_data = opt_res.json()
                                if opt_data.get("sd_model_checkpoint"):
                                    model_title = opt_data["sd_model_checkpoint"]
                        except Exception:
                            pass
                    return {
                        "reachable": True,
                        "api_enabled": True,
                        "model": model_title,
                        "models_count": len(models) if isinstance(models, list) else 0,
                    }
                elif res.status_code == 404:
                    return {
                        "reachable": True,
                        "api_enabled": False,
                        "error": "AUTOMATIC1111 WebUI is running, but the REST API is disabled. Launch with --api in COMMANDLINE_ARGS.",
                    }
                else:
                    return {
                        "reachable": True,
                        "api_enabled": False,
                        "error": f"AUTOMATIC1111 WebUI returned unexpected status HTTP {res.status_code}.",
                    }
        except httpx.ConnectError:
            return {
                "reachable": False,
                "api_enabled": False,
                "error": f"Could not connect to {self.base_url}. WebUI is stopped or unreachable.",
            }
        except Exception as exc:
            return {
                "reachable": False,
                "api_enabled": False,
                "error": str(exc),
            }

    async def is_available(self) -> bool:
        """Checks whether the /sdapi/v1/sd-models or /sdapi/v1/options endpoint is responsive."""
        health = await self.check_health()
        return health.get("reachable") is True and health.get("api_enabled") is True

    async def get_active_model_name(self) -> str:
        """Queries loaded model name from /sdapi/v1/sd-models or /sdapi/v1/options."""
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                res = await client.get(f"{self.base_url}/sdapi/v1/sd-models")
                if res.status_code == 200:
                    models = res.json()
                    if models and isinstance(models, list):
                        return models[0].get("model_name") or models[0].get("title", "stable-diffusion-v1-5")
        except Exception:
            pass
        return "stable-diffusion-v1-5"

    async def generate_image(
        self,
        request: ImageGenerationRequest,
        config: AppliedConfiguration,
    ) -> ImageData:
        """Generates an image using the local AUTOMATIC1111 /sdapi/v1/txt2img endpoint."""
        # 1. Parse effective dimensions
        parts = config.effective_resolution.split("x")
        width = int(parts[0]) if len(parts) == 2 else 512
        height = int(parts[1]) if len(parts) == 2 else 512
        steps = config.steps or 18

        # 2. Purpose-specific negative prompt
        purpose_val = request.intended_use.value.lower() if request.intended_use else ""
        if "color" in purpose_val or "colour" in purpose_val or config.color_mode == "monochrome_line_art":
            negative_prompt = (
                "color, colourful, shading, gradients, photorealistic, complex background, "
                "3d, realistic, shadow, texture, noisy, watermark, blurry, low quality"
            )
        elif "flashcard" in purpose_val or "worksheet" in purpose_val:
            negative_prompt = (
                "cluttered background, chaotic composition, text artifacts, blurry, watermark, noisy"
            )
        else:
            negative_prompt = "blurry, low quality, distorted, artifacts, watermark, lowres, deformed"

        payload = {
            "prompt": config.prompt_refinement,
            "negative_prompt": negative_prompt,
            "steps": steps,
            "width": width,
            "height": height,
            "sampler_name": "Euler a",
            "cfg_scale": 7.0,
            "seed": -1,
            "batch_size": 1,
            "n_iter": 1,
        }

        # 3. Serialize GPU access via lock
        async with _GPU_GENERATION_LOCK:
            t0 = time.perf_counter()
            timeout_sec = float(getattr(settings, "sd_timeout_seconds", 180.0))
            try:
                async with httpx.AsyncClient(timeout=timeout_sec) as client:
                    resp = await client.post(f"{self.base_url}/sdapi/v1/txt2img", json=payload)
                    
                    if resp.status_code == 404:
                        raise Automatic1111ProviderError(
                            message=(
                                "AUTOMATIC1111 WebUI is running on 127.0.0.1:7860, but the REST API is disabled. "
                                "The WebUI was started without the '--api' flag."
                            ),
                            status_code=503,
                            error_code="api_not_enabled",
                            instruction=(
                                "To enable the API:\n"
                                "1. Open webui-user.bat in D:\\stable-diffusion-webui-master.\n"
                                "2. Ensure '--api' is included in COMMANDLINE_ARGS (e.g. set COMMANDLINE_ARGS=--api --skip-install --medvram --skip-torch-cuda-test).\n"
                                "3. Save the file and restart webui-user.bat."
                            ),
                        )
                    
                    if resp.status_code == 500:
                        err_text = resp.text
                        if "out of memory" in err_text.lower() or "outofmemoryerror" in err_text.lower():
                            raise Automatic1111ProviderError(
                                message="GPU Out of Memory (CUDA OOM) during image generation.",
                                status_code=500,
                                error_code="cuda_out_of_memory",
                                instruction=(
                                    "Your NVIDIA RTX 2050 has 4 GB VRAM. To resolve:\n"
                                    "1. Use Eco tier (384x384, 10 steps) or Standard tier (512x512, 18 steps).\n"
                                    "2. Ensure '--medvram' is included in COMMANDLINE_ARGS in webui-user.bat.\n"
                                    "3. Close other GPU-intensive applications."
                                ),
                            )
                        if "model" in err_text.lower() and ("not found" in err_text.lower() or "none" in err_text.lower()):
                            raise Automatic1111ProviderError(
                                message=f"AUTOMATIC1111 model error: {err_text[:200]}",
                                status_code=503,
                                error_code="model_not_loaded",
                                instruction="Ensure a Stable Diffusion model checkpoint is loaded in WebUI.",
                            )
                        raise Automatic1111ProviderError(
                            message=f"AUTOMATIC1111 generation failed with internal error: {err_text[:200]}",
                            status_code=500,
                            error_code="internal_generation_error",
                        )
                    
                    resp.raise_for_status()
                    data = resp.json()

            except httpx.ConnectError:
                raise Automatic1111ProviderError(
                    message=f"Could not connect to local AUTOMATIC1111 WebUI at {self.base_url}. The WebUI is stopped or unreachable.",
                    status_code=503,
                    error_code="webui_unreachable",
                    instruction=(
                        "To start the WebUI:\n"
                        "1. Open D:\\stable-diffusion-webui-master in terminal.\n"
                        "2. Run webui-user.bat (with COMMANDLINE_ARGS=--api --skip-install --medvram --skip-torch-cuda-test).\n"
                        "3. Wait until the terminal displays: 'Running on local URL: http://127.0.0.1:7860'."
                    ),
                )
            except httpx.TimeoutException:
                raise Automatic1111ProviderError(
                    message=f"Image generation timed out after {int(timeout_sec)} seconds.",
                    status_code=504,
                    error_code="generation_timeout",
                    instruction="Generation exceeded timeout limit. Select Eco or Standard tier with fewer sampling steps.",
                )
            except Automatic1111ProviderError:
                raise
            except httpx.HTTPStatusError as http_err:
                raise Automatic1111ProviderError(
                    message=f"AUTOMATIC1111 HTTP {http_err.response.status_code}: {http_err.response.text[:200]}",
                    status_code=http_err.response.status_code if http_err.response.status_code in (400, 422, 500, 502, 503, 504) else 500,
                    error_code="provider_http_error",
                )
            except Exception as exc:
                raise Automatic1111ProviderError(
                    message=f"AUTOMATIC1111 generation failed: {str(exc)}",
                    status_code=500,
                    error_code="unexpected_provider_error",
                )

            elapsed = round(time.perf_counter() - t0, 3)

        images = data.get("images", [])
        if not images or len(images) == 0:
            raise Automatic1111ProviderError(
                message="AUTOMATIC1111 WebUI returned an empty image list.",
                status_code=502,
                error_code="empty_image_response",
            )

        b64_str = images[0]
        data_uri = f"data:image/png;base64,{b64_str}"

        # Return real image data with measured elapsed duration
        img_data = ImageData(
            url=data_uri,
            format="png",
            width=width,
            height=height,
        )
        img_data._measured_elapsed = elapsed  # internal attribute
        return img_data
