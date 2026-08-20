"""
图片生成相关数据模型
"""
from typing import Optional, List, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field, validator


class ImageProvider(str, Enum):
    """图片提供商"""
    YI = "yi"
    BAILIAN = "bailian"


class ImageModel(str, Enum):
    """图片模型"""
    # ===== Gemini 系列 (API易) =====
    GEMINI_FLASH_LITE = "gemini-3.1-flash-lite-image"
    GEMINI_FLASH = "gemini-3.1-flash-image-preview"
    GEMINI_25_FLASH = "gemini-2.5-flash-image"
    GEMINI_PRO = "gemini-3-pro-image-preview"

    # ===== GPT-Image 系列 (API易) =====
    GPT_IMAGE_2 = "gpt-image-2"
    GPT_IMAGE_2_ALL = "gpt-image-2-all"
    GPT_IMAGE_2_VIP = "gpt-image-2-vip"

    # ===== 百炼系列 =====
    Z_IMAGE_TURBO = "z-image-turbo"
    WAN_27_PRO = "wan2.7-image-pro"
    WAN_27 = "wan2.7-image"
    QWEN_30_PRO = "qwen-image-3.0-pro"
    QWEN_30 = "qwen-image-3.0"
    QWEN_20_PRO = "qwen-image-2.0-pro"
    QWEN_20 = "qwen-image-2.0"


class AspectRatio(str, Enum):
    """宽高比"""
    RATIO_1_1 = "1:1"
    RATIO_16_9 = "16:9"
    RATIO_9_16 = "9:16"
    RATIO_3_2 = "3:2"
    RATIO_2_3 = "2:3"
    RATIO_4_3 = "4:3"
    RATIO_3_4 = "3:4"
    RATIO_21_9 = "21:9"


class ImageSize(str, Enum):
    """图片尺寸"""
    SIZE_1K = "1K"
    SIZE_2K = "2K"
    SIZE_4K = "4K"


# ==================== 文生图 ====================

class TextToImageRequest(BaseModel):
    """文生图请求"""
    prompt: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="提示词"
    )
    model: ImageModel = Field(
        default=ImageModel.GEMINI_FLASH_LITE,
        description="模型名称"
    )
    provider: ImageProvider = Field(
        default=ImageProvider.YI,
        description="服务提供商"
    )
    count: int = Field(
        default=1,
        ge=1,
        le=10,
        description="生成数量"
    )
    aspect_ratio: AspectRatio = Field(
        default=AspectRatio.RATIO_1_1,
        description="宽高比"
    )
    image_size: ImageSize = Field(
        default=ImageSize.SIZE_1K,
        description="图片尺寸"
    )
    optimize: bool = Field(
        default=True,
        description="是否优化提示词"
    )
    prompt_extend: bool = Field(
        default=False,
        description="是否启用智能改写（百炼专用）"
    )

    @validator('prompt')
    def validate_prompt(cls, v):
        if not v or not v.strip():
            raise ValueError('提示词不能为空')
        return v.strip()


# ==================== 图生图 ====================

class ImageToImageRequest(BaseModel):
    """图生图请求"""
    source_image: str = Field(
        ...,
        description="参考图路径或 base64 编码"
    )
    prompt: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="提示词"
    )
    model: ImageModel = Field(
        default=ImageModel.GEMINI_FLASH_LITE,
        description="模型名称"
    )
    provider: ImageProvider = Field(
        default=ImageProvider.YI,
        description="服务提供商"
    )
    count: int = Field(
        default=1,
        ge=1,
        le=10,
        description="生成数量"
    )
    aspect_ratio: AspectRatio = Field(
        default=AspectRatio.RATIO_1_1,
        description="宽高比"
    )
    image_size: ImageSize = Field(
        default=ImageSize.SIZE_1K,
        description="图片尺寸"
    )
    optimize: bool = Field(
        default=True,
        description="是否优化提示词"
    )

    @validator('prompt')
    def validate_prompt(cls, v):
        if not v or not v.strip():
            raise ValueError('提示词不能为空')
        return v.strip()

    @validator('source_image')
    def validate_source_image(cls, v):
        if not v or not v.strip():
            raise ValueError('参考图不能为空')
        return v.strip()


# ==================== 多图融合 ====================

class FuseImagesRequest(BaseModel):
    """多图融合请求"""
    image_paths: List[str] = Field(
        ...,
        min_length=2,
        max_length=14,
        description="图片路径列表"
    )
    fusion_prompt: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="融合提示词"
    )
    model: ImageModel = Field(
        default=ImageModel.GEMINI_FLASH_LITE,
        description="模型名称"
    )
    provider: ImageProvider = Field(
        default=ImageProvider.YI,
        description="服务提供商"
    )
    aspect_ratio: AspectRatio = Field(
        default=AspectRatio.RATIO_1_1,
        description="宽高比"
    )
    image_size: ImageSize = Field(
        default=ImageSize.SIZE_1K,
        description="图片尺寸"
    )

    @validator('image_paths')
    def validate_image_paths(cls, v):
        if not v or len(v) < 2:
            raise ValueError('至少需要 2 张图片')
        if len(v) > 14:
            raise ValueError('最多支持 14 张图片')
        return v


# ==================== 响应模型 ====================

class ImageInfo(BaseModel):
    """图片信息"""
    url: Optional[str] = Field(None, description="图片 URL")
    filename: Optional[str] = Field(None, description="文件名")
    path: Optional[str] = Field(None, description="本地路径")
    b64_json: Optional[str] = Field(None, description="Base64 编码")


class ImageGenerationResponse(BaseModel):
    """图片生成响应"""
    success: bool = Field(..., description="是否成功")
    images: List[ImageInfo] = Field(default_factory=list, description="生成的图片列表")
    used_prompt: Optional[str] = Field(None, description="使用的提示词")
    original_prompt: Optional[str] = Field(None, description="原始提示词")
    source_image: Optional[str] = Field(None, description="源图片路径（图生图）")
    cost: Optional[Dict[str, Any]] = Field(None, description="费用信息")
    summary: Dict[str, Any] = Field(default_factory=dict, description="摘要信息")
    error: Optional[str] = Field(None, description="错误信息")