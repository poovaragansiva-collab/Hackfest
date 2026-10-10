from abc import ABC, abstractmethod
from typing import Dict, Any
from ..schemas.request import ImageGenerationRequest
from ..schemas.response import AppliedConfiguration, ImageData


class BaseImageProvider(ABC):
    """Abstract interface for image generation adapters."""

    @property
    @abstractmethod
    def provider_id(self) -> str:
        """Machine identifier of the provider (e.g., 'mock', 'openai', 'stability')."""
        pass

    @abstractmethod
    async def generate_image(
        self,
        request: ImageGenerationRequest,
        config: AppliedConfiguration,
    ) -> ImageData:
        """Generates an image according to the applied configuration."""
        pass

    @abstractmethod
    def is_configured(self) -> bool:
        """Returns True if required credentials/endpoints are set up."""
        pass
