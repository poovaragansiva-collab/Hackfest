import asyncio
import base64
import io
import logging
import re
from typing import Optional
from PIL import Image
from google import genai
from google.genai import types, errors

from .base import BaseImageProvider
from ..config import settings
from ..schemas.request import ImageGenerationRequest, AspectRatioEnum
from ..schemas.response import AppliedConfiguration, ImageData

logger = logging.getLogger(__name__)


class GoogleProviderError(Exception):
    """Custom exception for Google Gemini provider failures."""

    def __init__(self, message: str, status_code: int = 502, error_code: str = "GOOGLE_PROVIDER_ERROR"):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_code = error_code


def sanitize_error_text(text: str, key: Optional[str] = None) -> str:
    """Removes sensitive API keys and authorization secrets from error messages."""
    if not text:
        return ""
    sanitized = str(text)
    if key and len(key) > 4:
        sanitized = sanitized.replace(key, "[REDACTED]")
    # Redact Google API key patterns (typically AIzaSy followed by 33 base64 chars)
    sanitized = re.sub(r"AIzaSy[A-Za-z0-9_\-]{33}", "[REDACTED]", sanitized)
    sanitized = re.sub(r"Bearer\s+[A-Za-z0-9_\-\.]+", "Bearer [REDACTED]", sanitized, flags=re.IGNORECASE)
    sanitized = re.sub(r"(?:api[_-]?key|key|token|auth)=([^\s&]+)", r"key=[REDACTED]", sanitized, flags=re.IGNORECASE)
    return sanitized


class GoogleImageProvider(BaseImageProvider):
    """Real image generation provider using the official Google GenAI Python SDK."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
    ):
        self.api_key = settings.google_api_key if api_key is None else api_key
        self.model = settings.google_model if model is None else model

    @property
    def provider_id(self) -> str:
        return "google"

    def is_configured(self) -> bool:
        """Checks if GOOGLE_API_KEY is present without exposing secret."""
        return bool(self.api_key and len(self.api_key.strip()) > 0)

    async def generate_image(
        self,
        request: ImageGenerationRequest,
        config: AppliedConfiguration,
    ) -> ImageData:
        """Dispatches multimodal image generation to Google GenAI client."""
        if not self.is_configured():
            raise GoogleProviderError(
                message="Google API key is not configured. Set GOOGLE_API_KEY in backend/.env.",
                status_code=503,
                error_code="GOOGLE_AUTH_MISSING",
            )

        # Map aspect ratio to Gemini-supported values ('1:1', '3:4', '4:3', '9:16', '16:9')
        aspect_ratio_map = {
            AspectRatioEnum.SQUARE: "1:1",
            AspectRatioEnum.PORTRAIT_STANDARD: "3:4",
            AspectRatioEnum.LANDSCAPE_STANDARD: "4:3",
            AspectRatioEnum.PORTRAIT_TALL: "9:16",
            AspectRatioEnum.WIDESCREEN: "16:9",
        }
        aspect_ratio = aspect_ratio_map.get(request.aspect_ratio, "1:1")

        # Refined prompt incorporating purpose directives
        prompt_text = (config.prompt_refinement or request.prompt).strip()

        def _call_gemini_sync() -> ImageData:
            try:
                client = genai.Client(api_key=self.api_key)

                content_config = types.GenerateContentConfig(
                    response_modalities=["IMAGE"],
                    image_config=types.ImageConfig(
                        aspect_ratio=aspect_ratio,
                    ),
                )

                response = client.models.generate_content(
                    model=self.model,
                    contents=prompt_text,
                    config=content_config,
                )

                # Validate response structure
                if not response or not response.candidates:
                    raise GoogleProviderError(
                        message="Google Gemini returned an empty response candidate list.",
                        status_code=502,
                        error_code="GOOGLE_EMPTY_RESPONSE",
                    )

                candidate = response.candidates[0]
                finish_reason = getattr(candidate, "finish_reason", None)
                if finish_reason in ("SAFETY", "BLOCKLIST", "PROHIBITED_CONTENT"):
                    raise GoogleProviderError(
                        message=f"Google Gemini safety filters blocked generation for this prompt (reason: {finish_reason}).",
                        status_code=400,
                        error_code="GOOGLE_SAFETY_BLOCKED",
                    )

                if not candidate.content or not candidate.content.parts:
                    raise GoogleProviderError(
                        message="Google Gemini returned no content parts in the generation candidate.",
                        status_code=502,
                        error_code="GOOGLE_NO_PARTS",
                    )

                # Find image inline data part
                image_bytes = None
                mime_type = "image/png"
                for part in candidate.content.parts:
                    inline_data = getattr(part, "inline_data", None)
                    if inline_data and getattr(inline_data, "data", None):
                        image_bytes = inline_data.data
                        if getattr(inline_data, "mime_type", None):
                            mime_type = inline_data.mime_type
                        break

                if not image_bytes:
                    raise GoogleProviderError(
                        message="Google Gemini generation response did not contain image data.",
                        status_code=502,
                        error_code="GOOGLE_NO_IMAGE_DATA",
                    )

                # Parse dimensions from real generated bytes
                try:
                    pil_img = Image.open(io.BytesIO(image_bytes))
                    width, height = pil_img.size
                except Exception:
                    # Fallback default dimensions if PIL parse fails
                    width, height = 1024, 1024

                b64_data = base64.b64encode(image_bytes).decode("utf-8")
                data_uri = f"data:{mime_type};base64,{b64_data}"

                return ImageData(
                    url=data_uri,
                    format="png" if "png" in mime_type.lower() else "jpeg",
                    width=width,
                    height=height,
                )

            except errors.APIError as api_err:
                code = getattr(api_err, "code", None)
                err_str = sanitize_error_text(str(api_err), self.api_key)

                if code in (401, 403) or "API_KEY_INVALID" in err_str or "PERMISSION_DENIED" in err_str or "unauthorized" in err_str.lower():
                    raise GoogleProviderError(
                        message="Google Gemini authentication failed. Verify that GOOGLE_API_KEY in backend/.env is valid and active.",
                        status_code=401,
                        error_code="GOOGLE_AUTH_FAILED",
                    )
                elif code == 429 or "RESOURCE_EXHAUSTED" in err_str or "quota" in err_str.lower() or "rate limit" in err_str.lower():
                    raise GoogleProviderError(
                        message=(
                            "Google Gemini API quota exceeded or rate limit reached (HTTP 429). "
                            "The project has exhausted its image generation quota. "
                            "To run offline without live billing, set ACTIVE_PROVIDER=mock in backend/.env."
                        ),
                        status_code=429,
                        error_code="GOOGLE_QUOTA_EXHAUSTED",
                    )
                elif code == 404 or "NOT_FOUND" in err_str or "model" in err_str.lower():
                    raise GoogleProviderError(
                        message=f"Google Gemini model not found: '{self.model}'. Verify that the configured model is available.",
                        status_code=404,
                        error_code="GOOGLE_MODEL_NOT_FOUND",
                    )
                elif code in (400, 422) or "INVALID_ARGUMENT" in err_str:
                    clean_msg = err_str.split("\n")[0]
                    raise GoogleProviderError(
                        message=f"Google Gemini rejected generation parameters: {clean_msg}",
                        status_code=400,
                        error_code="GOOGLE_INVALID_REQUEST",
                    )
                elif code in (503, 504) or "UNAVAILABLE" in err_str:
                    raise GoogleProviderError(
                        message="Google Gemini service temporarily unavailable. Please retry in a moment.",
                        status_code=503,
                        error_code="GOOGLE_SERVICE_UNAVAILABLE",
                    )
                else:
                    clean_msg = err_str.split("\n")[0]
                    raise GoogleProviderError(
                        message=f"Google Gemini upstream error (HTTP {code or 502}): {clean_msg}",
                        status_code=code if (code and 400 <= code < 600) else 502,
                        error_code="GOOGLE_UPSTREAM_ERROR",
                    )
            except Exception as exc:
                if isinstance(exc, GoogleProviderError):
                    raise exc
                err_str = sanitize_error_text(str(exc), self.api_key)
                if "429" in err_str or "quota" in err_str.lower() or "RESOURCE_EXHAUSTED" in err_str:
                    raise GoogleProviderError(
                        message="Google Gemini API quota exceeded (HTTP 429). To run offline, set ACTIVE_PROVIDER=mock.",
                        status_code=429,
                        error_code="GOOGLE_QUOTA_EXHAUSTED",
                    )
                raise GoogleProviderError(
                    message=f"Google Gemini generation failed: {err_str}",
                    status_code=502,
                    error_code="GOOGLE_CALL_FAILED",
                )

        # Run synchronous client call in threadpool
        return await asyncio.to_thread(_call_gemini_sync)
