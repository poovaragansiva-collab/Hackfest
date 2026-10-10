from .base import BaseImageProvider
from .mock_provider import DevMockProvider
from ..config import settings


def get_image_provider() -> BaseImageProvider:
    """Factory to retrieve active provider based on configuration."""
    provider_name = settings.active_provider.lower().strip()
    
    if provider_name == "mock":
        return DevMockProvider()
    
    # Placeholders for Member 3's provider research:
    if provider_name == "openai":
        # When Member 3 confirms OpenAI adapter
        raise NotImplementedError("OpenAI provider adapter is pending Member 3 integration.")
    elif provider_name == "stability":
        # When Member 3 confirms Stability adapter
        raise NotImplementedError("Stability AI provider adapter is pending Member 3 integration.")
    
    # Fallback to dev mock for safety
    return DevMockProvider()


__all__ = ["BaseImageProvider", "DevMockProvider", "get_image_provider"]
