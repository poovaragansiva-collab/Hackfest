import base64
import io
import logging
import re
from typing import Optional
import httpx
from PIL import Image

from .base import BaseImageProvider
from ..config import settings
from ..schemas.request import ImageGenerationRequest, AspectRatioEnum
from ..schemas.response import AppliedConfiguration, ImageData

logger = logging.getLogger(__name__)


class OpenRouterProviderError(Exception):
    """Custom exception for OpenRouter image provider failures."""

    def __init__(self, message: str, status_code: int = 502, error_code: str = "OPENROUTER_PROVIDER_ERROR"):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_code = error_code


def sanitize_error_text(text: str, key: Optional[str] = None) -> str:
    """Removes sensitive API keys, tokens, and authorization secrets from text."""
    if not text:
        return ""
    sanitized = str(text)
    if key and len(key) > 4:
        sanitized = sanitized.replace(key, "[REDACTED]")
    # Redact OpenRouter key patterns (typically sk-or-v1-...)
    sanitized = re.sub(r"sk-or-v1-[A-Za-z0-9_\-]+", "[REDACTED]", sanitized)
    sanitized = re.sub(r"Bearer\s+[A-Za-z0-9_\-\.]+", "Bearer [REDACTED]", sanitized, flags=re.IGNORECASE)
    sanitized = re.sub(r"(?:api[_-]?key|key|token|auth)=([^\s&]+)", r"key=[REDACTED]", sanitized, flags=re.IGNORECASE)
    return sanitized


class OpenRouterImageProvider(BaseImageProvider):
    """Real image generation provider using OpenRouter's dedicated image-generation API.
    
    Target model: sourceful/riverflow-v2-fast (or user-configured OPENROUTER_MODEL).
    Dedicated endpoint: POST https://openrouter.ai/api/v1/images
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        self.api_key = settings.openrouter_api_key if api_key is None else api_key
        self.model = settings.openrouter_model if model is None else model
        self.base_url = settings.openrouter_base_url if base_url is None else base_url

    @property
    def provider_id(self) -> str:
        return "openrouter"

    def is_configured(self) -> bool:
        """Checks if OPENROUTER_API_KEY is present without exposing the secret."""
        return bool(self.api_key and len(self.api_key.strip()) > 0)

    async def generate_image(
        self,
        request: ImageGenerationRequest,
        config: AppliedConfiguration,
    ) -> ImageData:
        """Dispatches image generation request to OpenRouter's dedicated endpoint."""
        if not self.is_configured():
            raise OpenRouterProviderError(
                message="OpenRouter API key is not configured. Set OPENROUTER_API_KEY in backend/.env.",
                status_code=503,
                error_code="OPENROUTER_AUTH_MISSING",
            )

        # Map aspect ratio to model-supported values ('1:1', '3:4', '4:3', '9:16', '16:9')
        aspect_ratio_map = {
            AspectRatioEnum.SQUARE: "1:1",
            AspectRatioEnum.PORTRAIT_STANDARD: "3:4",
            AspectRatioEnum.LANDSCAPE_STANDARD: "4:3",
            AspectRatioEnum.PORTRAIT_TALL: "9:16",
            AspectRatioEnum.WIDESCREEN: "16:9",
        }
        aspect_ratio_str = aspect_ratio_map.get(request.aspect_ratio, "1:1") if request.aspect_ratio else "1:1"

        # Support 1K and 2K output resolutions only: 1K default (Standard tier), 2K for HD tier
        tier = (config.quality_tier or request.quality_tier or "standard").lower()
        if tier in ("hd", "high"):
            image_size_str = "2K"
        else:
            image_size_str = "1K"

        prompt_text = (config.prompt_refinement or request.prompt).strip()

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://hackfest.local",
            "X-Title": "Resource-Aware Image Generation",
        }

        payload = {
            "model": self.model,
            "prompt": prompt_text,
            "aspect_ratio": aspect_ratio_str,
            "image_size": image_size_str,
            "response_format": "b64_json",
        }

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    self.base_url,
                    json=payload,
                    headers=headers,
                )
        except httpx.TimeoutException:
            raise OpenRouterProviderError(
                message="OpenRouter image-generation request timed out after 60 seconds.",
                status_code=504,
                error_code="OPENROUTER_TIMEOUT",
            )
        except httpx.RequestError as exc:
            err_msg = sanitize_error_text(str(exc), self.api_key)
            raise OpenRouterProviderError(
                message=f"Failed to connect to OpenRouter endpoint: {err_msg}",
                status_code=502,
                error_code="OPENROUTER_CONNECTION_ERROR",
            )

        # Inspect HTTP response status
        if response.status_code != 200:
            self._handle_http_error(response)

        # Parse JSON response
        try:
            resp_json = response.json()
        except Exception:
            raise OpenRouterProviderError(
                message="OpenRouter returned an unparseable response payload.",
                status_code=502,
                error_code="OPENROUTER_MALFORMED_RESPONSE",
            )

        data_list = resp_json.get("data")
        if not data_list or not isinstance(data_list, list) or len(data_list) == 0:
            raise OpenRouterProviderError(
                message="OpenRouter response did not contain image data.",
                status_code=502,
                error_code="OPENROUTER_NO_IMAGE_DATA",
            )

        first_data = data_list[0]
        b64_json = first_data.get("b64_json")
        if not b64_json:
            # Fallback check if URL was provided
            img_url = first_data.get("url")
            if img_url:
                return ImageData(
                    url=img_url,
                    format="png",
                    width=1024 if image_size_str == "1K" else 2048,
                    height=1024 if image_size_str == "1K" else 2048,
                    actual_cost_usd=self._extract_actual_cost(resp_json),
                )
            raise OpenRouterProviderError(
                message="OpenRouter response data is missing image b64_json.",
                status_code=502,
                error_code="OPENROUTER_NO_IMAGE_DATA",
            )

        # Decode base64 and inspect image dimensions/format via PIL
        try:
            img_bytes = base64.b64decode(b64_json)
            pil_img = Image.open(io.BytesIO(img_bytes))
            width, height = pil_img.size
            img_format = (pil_img.format or "png").lower()
        except Exception:
            # Fallback dimensions if decoding fails
            width, height = (1024, 1024) if image_size_str == "1K" else (2048, 2048)
            img_format = "png"

        mime_type = f"image/{img_format}"
        data_uri = f"data:{mime_type};base64,{b64_json}"

        actual_cost = self._extract_actual_cost(resp_json)

        return ImageData(
            url=data_uri,
            format=img_format,
            width=width,
            height=height,
            actual_cost_usd=actual_cost,
        )

    def _extract_actual_cost(self, resp_json: dict) -> Optional[float]:
        """Extracts actual billed API cost from OpenRouter usage metadata if present."""
        usage = resp_json.get("usage")
        if isinstance(usage, dict):
            cost_val = usage.get("total_cost")
            if cost_val is None:
                cost_val = usage.get("cost")
            if cost_val is not None:
                try:
                    return float(cost_val)
                except (ValueError, TypeError):
                    pass
        return None

    def _handle_http_error(self, response: httpx.Response) -> None:
        """Parses and maps OpenRouter HTTP error codes to helpful sanitized exceptions."""
        status = response.status_code
        err_msg = ""
        try:
            err_data = response.json()
            if isinstance(err_data, dict):
                error_obj = err_data.get("error", {})
                if isinstance(error_obj, dict):
                    err_msg = error_obj.get("message") or str(error_obj)
                else:
                    err_msg = str(error_obj)
        except Exception:
            err_msg = response.text[:200]

        sanitized_msg = sanitize_error_text(err_msg, self.api_key)

        if status == 401:
            detail = f": {sanitized_msg}" if sanitized_msg else ""
            raise OpenRouterProviderError(
                message=f"OpenRouter authentication failed (HTTP 401){detail}. Verify that OPENROUTER_API_KEY in backend/.env is valid and active.",
                status_code=401,
                error_code="OPENROUTER_UNAUTHORIZED",
            )
        elif status == 403:
            detail = f": {sanitized_msg}" if sanitized_msg else ""
            raise OpenRouterProviderError(
                message=f"OpenRouter access forbidden (HTTP 403){detail}. Verify account permissions or restrictions.",
                status_code=403,
                error_code="OPENROUTER_FORBIDDEN",
            )
        elif status == 402:
            raise OpenRouterProviderError(
                message=(
                    "OpenRouter insufficient credits (HTTP 402). "
                    "Your OpenRouter balance is depleted. "
                    "To run offline without credits, set ACTIVE_PROVIDER=mock in backend/.env."
                ),
                status_code=402,
                error_code="OPENROUTER_INSUFFICIENT_CREDITS",
            )
        elif status == 429:
            raise OpenRouterProviderError(
                message="OpenRouter rate limit exceeded (HTTP 429). Please wait before retrying.",
                status_code=429,
                error_code="OPENROUTER_RATE_LIMITED",
            )
        elif status == 404:
            raise OpenRouterProviderError(
                message=f"OpenRouter model not found: '{self.model}'. Verify that the model identifier is correct.",
                status_code=404,
                error_code="OPENROUTER_MODEL_NOT_FOUND",
            )
        elif status in (400, 422):
            raise OpenRouterProviderError(
                message=f"OpenRouter rejected generation parameters (HTTP {status}): {sanitized_msg}",
                status_code=400,
                error_code="OPENROUTER_INVALID_REQUEST",
            )
        elif status in (502, 503, 504):
            raise OpenRouterProviderError(
                message=f"OpenRouter service temporarily unavailable (HTTP {status}). Please retry shortly.",
                status_code=status,
                error_code="OPENROUTER_SERVICE_UNAVAILABLE",
            )
        else:
            raise OpenRouterProviderError(
                message=f"OpenRouter upstream error (HTTP {status}): {sanitized_msg}",
                status_code=status if 400 <= status < 600 else 502,
                error_code="OPENROUTER_UPSTREAM_ERROR",
            )
