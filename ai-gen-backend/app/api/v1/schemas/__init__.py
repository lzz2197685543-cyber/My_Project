"""
API 数据模型 (Schemas)
"""
from app.api.v1.schemas.common import Response, PaginatedResponse
from app.api.v1.schemas.chat import (
    ChatRequest,
    ChatResponse,
    ProviderType,
    ChatCompletionRequest,
    ChatCompletionResponse,
)
from app.api.v1.schemas.image import (
    TextToImageRequest,
    ImageToImageRequest,
    FuseImagesRequest,
    ImageGenerationResponse,
    ImageModel,
    AspectRatio,
    ImageSize,
)

__all__ = [
    # Common
    "Response",
    "PaginatedResponse",
    # Chat
    "ChatRequest",
    "ChatResponse",
    "ProviderType",
    "ChatCompletionRequest",
    "ChatCompletionResponse",
    # Image
    "TextToImageRequest",
    "ImageToImageRequest",
    "FuseImagesRequest",
    "ImageGenerationResponse",
    "ImageModel",
    "AspectRatio",
    "ImageSize",
]