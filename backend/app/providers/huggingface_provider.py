import asyncio
import base64
import io
import logging
import re
from typing import Optional
from huggingface_hub import InferenceClient
from huggingface_hub.errors import HfHubHTTPError

from .base import BaseImageProvider
from ..config import settings
from ..schemas.request import ImageGenerationRequest, IntendedUseEnum, ColorPreferenceEnum
from ..schemas.response import AppliedConfiguration, ImageData

logger = logging.getLogger(__name__)


class HuggingFaceProviderError(Exception):
    """Custom exception for Hugging Face provider failures."""
    def __init__(self, message: str, status_code: int = 502, error_code: str = "HF_PROVIDER_ERROR"):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_code = error_code


def sanitize_error_text(text: str, token: Optional[str] = None) -> str:
    """Removes sensitive tokens and authorization secrets from error messages."""
    if not text:
        return ""
    sanitized = str(text)
    if token and len(token) > 4:
        sanitized = sanitized.replace(token, "[REDACTED]")
    # Redact common token patterns like hf_*** or Bearer ***
    sanitized = re.sub(r"hf_[A-Za-z0-9]{16,}", "[REDACTED]", sanitized)
    sanitized = re.sub(r"Bearer\s+[A-Za-z0-9_\-\.]+", "Bearer [REDACTED]", sanitized, flags=re.IGNORECASE)
    sanitized = re.sub(r"(?:api[_-]?key|token|auth)=([^\s&]+)", r"token=[REDACTED]", sanitized, flags=re.IGNORECASE)
    return sanitized


class HuggingFaceImageProvider(BaseImageProvider):
    """Real image generation provider using Hugging Face InferenceClient (fal-ai)."""

    def __init__(
        self,
        token: Optional[str] = None,
        model: Optional[str] = None,
        provider: Optional[str] = None,
    ):
        self.token = settings.hf_token if token is None else token
        self.model = settings.hf_model if model is None else model
        self.provider = settings.hf_provider if provider is None else provider

    @property
    def provider_id(self) -> str:
        return "huggingface"

    def is_configured(self) -> bool:
        """Checks if HF token is present without exposing secret."""
        return bool(self.token and len(self.token.strip()) > 0)

    async def generate_image(
        self,
        request: ImageGenerationRequest,
        config: AppliedConfiguration,
    ) -> ImageData:
        """Dispatches text-to-image request to Hugging Face InferenceClient."""
        if not self.is_configured():
            raise HuggingFaceProviderError(
                message="Hugging Face API token is not configured. Set HF_TOKEN in your environment or backend/.env file.",
                status_code=503,
                error_code="HF_AUTH_MISSING",
            )

        # Parse target resolution
        parts = config.effective_resolution.split("x")
        width = int(parts[0]) if len(parts) == 2 else 1024
        height = int(parts[1]) if len(parts) == 2 else 1024

        # Configure tier-aware inference steps for SDXL
        # Standard: 20 steps (faster, lower GPU compute)
        # HD: 40 steps (higher sampling fidelity, 2x denoising passes)
        if config.quality_tier == "hd":
            num_inference_steps = 40
        else:
            num_inference_steps = 20

        # Construct purpose-informed negative prompt
        if request.intended_use == IntendedUseEnum.COLORING_WORKSHEET or request.color_preference in [
            ColorPreferenceEnum.BLACK_AND_WHITE,
            ColorPreferenceEnum.LINE_ART,
        ]:
            negative_prompt = (
                "color, colored, shading, shadow, grayscale gradients, photorealistic, "
                "3d render, complex texture, dirty background, fill color"
            )
        elif request.intended_use == IntendedUseEnum.FLASHCARD:
            negative_prompt = (
                "crowded scene, busy background, multiple subjects, complex scenery, text watermark"
            )
        else:
            negative_prompt = "blurry, low quality, distorted, bad anatomy, artifacts"

        prompt_text = (config.prompt_refinement or request.prompt).strip()

        def _call_hf_sync():
            try:
                client = InferenceClient(
                    provider=self.provider,
                    api_key=self.token,
                )
                return client.text_to_image(
                    prompt=prompt_text,
                    negative_prompt=negative_prompt,
                    width=width,
                    height=height,
                    num_inference_steps=num_inference_steps,
                    model=self.model,
                )
            except HfHubHTTPError as hf_err:
                status = getattr(getattr(hf_err, "response", None), "status_code", None)
                server_msg = sanitize_error_text(getattr(hf_err, "server_message", "") or "", self.token)
                err_str = sanitize_error_text(str(hf_err), self.token)

                if status in (401, 403) or "401" in err_str or "unauthorized" in err_str.lower():
                    raise HuggingFaceProviderError(
                        message="Hugging Face authentication failed. Please verify your HF_TOKEN has Inference permissions.",
                        status_code=401,
                        error_code="HF_AUTH_FAILED",
                    )
                elif status == 402 or "402" in err_str or "credits" in err_str.lower() or "payment" in err_str.lower():
                    detail = server_msg if server_msg else "You have no remaining credits for inference provider 'fal-ai'."
                    raise HuggingFaceProviderError(
                        message=f"Hugging Face returned 402 Payment Required: {detail} To run offline without paid credits, use ACTIVE_PROVIDER=mock.",
                        status_code=402,
                        error_code="HF_INSUFFICIENT_CREDITS",
                    )
                elif status == 429 or "429" in err_str or "rate limit" in err_str.lower():
                    raise HuggingFaceProviderError(
                        message="Hugging Face API rate limit reached. Please wait before retrying.",
                        status_code=429,
                        error_code="HF_RATE_LIMITED",
                    )
                elif status == 404 or "not found" in err_str.lower():
                    raise HuggingFaceProviderError(
                        message=f"Hugging Face model or provider endpoint not found: '{self.model}' on '{self.provider}'.",
                        status_code=404,
                        error_code="HF_MODEL_NOT_FOUND",
                    )
                elif status in (400, 422):
                    detail = server_msg or err_str.split("\n")[0]
                    raise HuggingFaceProviderError(
                        message=f"Hugging Face rejected request parameters: {detail}",
                        status_code=400,
                        error_code="HF_INVALID_REQUEST",
                    )
                elif status in (503, 504) or "loading" in err_str.lower():
                    detail = server_msg or "Service temporarily unavailable or model is loading."
                    raise HuggingFaceProviderError(
                        message=f"Hugging Face service unavailable (HTTP {status or 503}): {detail}",
                        status_code=503,
                        error_code="HF_SERVICE_UNAVAILABLE",
                    )
                else:
                    detail = server_msg or err_str.split("\n")[0] or "Unknown upstream error"
                    raise HuggingFaceProviderError(
                        message=f"Hugging Face upstream error (HTTP {status or 502}): {detail}",
                        status_code=status if (status and 400 <= status < 600) else 502,
                        error_code="HF_UPSTREAM_ERROR",
                    )
            except Exception as exc:
                if isinstance(exc, HuggingFaceProviderError):
                    raise exc
                exc_str = sanitize_error_text(str(exc), self.token)
                if "402" in exc_str or "credits" in exc_str.lower() or "payment" in exc_str.lower():
                    raise HuggingFaceProviderError(
                        message="Hugging Face returned 402 Payment Required: You have no remaining credits on provider account. Use ACTIVE_PROVIDER=mock.",
                        status_code=402,
                        error_code="HF_INSUFFICIENT_CREDITS",
                    )
                raise HuggingFaceProviderError(
                    message=f"Hugging Face generation failed: {exc_str}",
                    status_code=502,
                    error_code="HF_CALL_FAILED",
                )

        # Execute synchronous client call in thread pool to avoid blocking async event loop
        pil_image = await asyncio.to_thread(_call_hf_sync)

        # Convert PIL image to PNG base64 data URI
        buffer = io.BytesIO()
        pil_image.save(buffer, format="PNG")
        encoded_data = base64.b64encode(buffer.getvalue()).decode("utf-8")
        data_uri = f"data:image/png;base64,{encoded_data}"

        return ImageData(
            url=data_uri,
            format="png",
            width=pil_image.width,
            height=pil_image.height,
        )
