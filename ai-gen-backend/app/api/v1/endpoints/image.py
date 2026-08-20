"""
图片生成 API 端点
"""
from typing import Optional, List
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from pathlib import Path
import time
import uuid

from app.api.v1.schemas.image import (
    TextToImageRequest,
    ImageToImageRequest,
    FuseImagesRequest,
    ImageGenerationResponse,
    ImageInfo
)
from app.api.v1.schemas.common import Response
from app.services.image_service import ImageService
from app.core.dependencies import get_image_service, get_api_key_from_header, check_rate_limit
from config.settings import settings
from app.utils.logger import get_logger

logger = get_logger("image_endpoint")
router = APIRouter(prefix="/images", tags=["Image"])


@router.post("/text-to-image", response_model=Response[ImageGenerationResponse])
async def text_to_image(
        request: TextToImageRequest,
        image_service: ImageService = Depends(get_image_service),
        api_key: Optional[str] = Depends(get_api_key_from_header),
        _: str = Depends(check_rate_limit)
):
    """
    文生图接口

    - **prompt**: 提示词
    - **model**: 模型名称
    - **provider**: 提供商 (yi/bailian)
    - **count**: 生成数量 (1-10)
    - **aspect_ratio**: 宽高比 (1:1, 16:9, 9:16, 3:2, 2:3, 4:3, 3:4, 21:9)
    - **image_size**: 图片尺寸 (1K, 2K, 4K)
    - **optimize**: 是否优化提示词
    - **prompt_extend**: 是否启用智能改写（百炼专用）
    """
    try:
        result = await image_service.text_to_image(
            prompt=request.prompt,
            model=request.model.value,
            provider=request.provider.value,
            count=request.count,
            aspect_ratio=request.aspect_ratio.value,
            image_size=request.image_size.value,
            optimize=request.optimize,
            prompt_extend=request.prompt_extend,
            api_key=api_key,
            save_to_file=True
        )

        if not result.get("success"):
            return Response.error(result.get("error", "生成失败"), 500)

        # 转换图片数据为 ImageInfo
        images = [
            ImageInfo(
                filename=img.get("filename"),
                path=img.get("path"),
                url=img.get("url")
            )
            for img in result.get("images", [])
        ]

        return Response.success(
            data=ImageGenerationResponse(
                success=True,
                images=images,
                used_prompt=result.get("used_prompt"),
                original_prompt=result.get("original_prompt"),
                summary=result.get("summary", {})
            )
        )

    except Exception as e:
        logger.error(f"文生图异常: {e}")
        return Response.error(f"文生图请求异常: {str(e)}", 500)


@router.post("/image-to-image", response_model=Response[ImageGenerationResponse])
async def image_to_image(
        request: ImageToImageRequest,
        image_service: ImageService = Depends(get_image_service),
        api_key: Optional[str] = Depends(get_api_key_from_header),
        _: str = Depends(check_rate_limit)
):
    """
    图生图接口

    - **source_image**: 源图片路径或 base64 编码
    - **prompt**: 提示词
    - **model**: 模型名称
    - **provider**: 提供商
    - **count**: 生成数量 (1-10)
    - **aspect_ratio**: 宽高比
    - **image_size**: 图片尺寸
    - **optimize**: 是否优化提示词
    """
    try:
        result = await image_service.image_to_image(
            source_image=request.source_image,
            prompt=request.prompt,
            model=request.model.value,
            provider=request.provider.value,
            count=request.count,
            aspect_ratio=request.aspect_ratio.value,
            image_size=request.image_size.value,
            optimize=request.optimize,
            api_key=api_key,
            save_to_file=True
        )

        if not result.get("success"):
            return Response.error(result.get("error", "生成失败"), 500)

        images = [
            ImageInfo(
                filename=img.get("filename"),
                path=img.get("path"),
                url=img.get("url")
            )
            for img in result.get("images", [])
        ]

        return Response.success(
            data=ImageGenerationResponse(
                success=True,
                images=images,
                used_prompt=result.get("used_prompt"),
                original_prompt=result.get("original_prompt"),
                source_image=result.get("source_image"),
                summary=result.get("summary", {})
            )
        )

    except Exception as e:
        logger.error(f"图生图异常: {e}")
        return Response.error(f"图生图请求异常: {str(e)}", 500)


@router.post("/fuse", response_model=Response[ImageGenerationResponse])
async def fuse_images(
        request: FuseImagesRequest,
        image_service: ImageService = Depends(get_image_service),
        api_key: Optional[str] = Depends(get_api_key_from_header),
        _: str = Depends(check_rate_limit)
):
    """
    多图融合接口

    - **image_paths**: 图片路径列表 (2-14张)
    - **fusion_prompt**: 融合提示词
    - **model**: 模型名称
    - **provider**: 提供商
    - **aspect_ratio**: 宽高比
    - **image_size**: 图片尺寸
    """
    try:
        result = await image_service.fuse_images(
            image_paths=request.image_paths,
            fusion_prompt=request.fusion_prompt,
            model=request.model.value,
            provider=request.provider.value,
            aspect_ratio=request.aspect_ratio.value,
            image_size=request.image_size.value,
            api_key=api_key,
            save_to_file=True
        )

        if not result.get("success"):
            return Response.error(result.get("error", "融合失败"), 500)

        images = [
            ImageInfo(
                filename=img.get("filename"),
                path=img.get("path"),
                url=img.get("url")
            )
            for img in result.get("images", [])
        ]

        return Response.success(
            data=ImageGenerationResponse(
                success=True,
                images=images,
                used_prompt=result.get("used_prompt"),
                original_prompt=result.get("original_prompt"),
                summary=result.get("summary", {})
            )
        )

    except Exception as e:
        logger.error(f"多图融合异常: {e}")
        return Response.error(f"多图融合请求异常: {str(e)}", 500)


@router.post("/upload")
async def upload_image(
        file: UploadFile = File(..., description="图片文件"),
        _: str = Depends(check_rate_limit)
):
    """
    上传图片接口

    支持的格式: PNG, JPG, JPEG, GIF, WEBP, BMP
    """
    try:
        # 验证文件类型
        allowed_types = [
            "image/png", "image/jpeg", "image/jpg",
            "image/gif", "image/webp", "image/bmp"
        ]

        if file.content_type not in allowed_types:
            return Response.error(
                f"不支持的文件类型: {file.content_type}。支持的格式: PNG, JPG, JPEG, GIF, WEBP, BMP",
                400
            )

        # 生成文件名
        original_name = file.filename or "image.png"
        suffix = Path(original_name).suffix
        filename = f"{int(time.time())}_{uuid.uuid4().hex[:8]}{suffix}"

        # 保存文件
        input_dir = settings.INPUT_DIR
        input_dir.mkdir(parents=True, exist_ok=True)
        filepath = input_dir / filename

        content = await file.read()

        # 验证文件大小 (限制 20MB)
        if len(content) > 20 * 1024 * 1024:
            return Response.error("文件大小超过 20MB 限制", 400)

        with open(filepath, 'wb') as f:
            f.write(content)

        return Response.success({
            "filename": filename,
            "path": str(filepath),
            "content_type": file.content_type,
            "size": len(content)
        })

    except Exception as e:
        logger.error(f"上传图片异常: {e}")
        return Response.error(f"上传图片失败: {str(e)}", 500)