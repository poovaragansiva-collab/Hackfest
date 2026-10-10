from .base import BaseImageProvider
from .mock_provider import DevMockProvider
from .automatic1111_provider import Automatic1111ImageProvider, Automatic1111ProviderError
from .huggingface_provider import HuggingFaceImageProvider, HuggingFaceProviderError
from .google_provider import GoogleImageProvider, GoogleProviderError
from .openrouter_provider import OpenRouterImageProvider, OpenRouterProviderError
from ..config import settings


def get_image_provider() -> BaseImageProvider:
    """Factory to retrieve active provider based on configuration."""
    provider_name = settings.active_provider.lower().strip()
    
    if provider_name in ("automatic1111", "local", "sd"):
        return Automatic1111ImageProvider()

    if provider_name in ("openrouter", "or"):
        return OpenRouterImageProvider()

    if provider_name in ("google", "gemini"):
        return GoogleImageProvider()

    if provider_name in ("huggingface", "hf"):
        return HuggingFaceImageProvider()
    
    if provider_name == "mock":
        return DevMockProvider()
    
    # Placeholders for additional providers
    if provider_name == "openai":
        raise NotImplementedError("OpenAI provider adapter is pending integration.")
    elif provider_name == "stability":
        raise NotImplementedError("Stability AI direct provider adapter is pending integration.")
    
    # Default to automatic1111 for local development
    return Automatic1111ImageProvider()


__all__ = [
    "BaseImageProvider",
    "DevMockProvider",
    "Automatic1111ImageProvider",
    "Automatic1111ProviderError",
    "HuggingFaceImageProvider",
    "HuggingFaceProviderError",
    "GoogleImageProvider",
    "GoogleProviderError",
    "OpenRouterImageProvider",
    "OpenRouterProviderError",
    "get_image_provider",
]
