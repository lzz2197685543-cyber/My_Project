"""
依赖注入模块
"""
from typing import Optional
from fastapi import Request, HTTPException

from app.services.chat_service import ChatService
from app.services.image_service import ImageService
from app.services.ai_service import AIClientFactory
from config.settings import settings
from app.utils.logger import get_logger

logger = get_logger("dependencies")

# ==================== 服务实例（单例） ====================

_chat_service: Optional[ChatService] = None
_image_service: Optional[ImageService] = None


def get_chat_service() -> ChatService:
    """获取聊天服务实例（单例）"""
    global _chat_service
    if _chat_service is None:
        _chat_service = ChatService()
        logger.info("✅ ChatService 初始化完成")
    return _chat_service


def get_image_service() -> ImageService:
    """获取图片服务实例（单例）"""
    global _image_service
    if _image_service is None:
        _image_service = ImageService()
        logger.info("✅ ImageService 初始化完成")
    return _image_service


# ==================== API Key 提取 ====================

async def get_api_key_from_header(request: Request) -> Optional[str]:
    """
    从请求头提取 API Key

    优先级: X-API-Key > Authorization Bearer
    """
    # 方式1: X-API-Key
    api_key = request.headers.get("X-API-Key")
    if api_key:
        logger.debug("✅ 从 X-API-Key 头获取 API Key")
        return api_key

    # 方式2: Authorization: Bearer <token>
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        api_key = auth_header[7:]  # 去掉 "Bearer "
        logger.debug("✅ 从 Authorization 头获取 API Key")
        return api_key

    return None


async def get_provider_api_key(
        request: Request,
        provider: str,
        api_key: Optional[str] = None
) -> Optional[str]:
    """
    获取指定提供商的 API Key

    优先级: 传入参数 > 请求头 > 环境变量
    """
    if api_key:
        return api_key

    # 从请求头获取
    header_key = await get_api_key_from_header(request)
    if header_key:
        return header_key

    # 从环境变量获取
    if provider == "yi":
        return settings.YI_API_KEY
    elif provider == "bailian":
        return settings.BAILIAN_API_KEY

    return None


# ==================== 速率限制 ====================

from collections import defaultdict
import time

_rate_limit_cache: dict = defaultdict(list)


async def check_rate_limit(request: Request):
    """
    检查速率限制

    限制: 每分钟 60 次请求
    """
    client_ip = request.client.host if request.client else "unknown"
    now = time.time()

    # 清理 1 分钟前的记录
    _rate_limit_cache[client_ip] = [
        t for t in _rate_limit_cache[client_ip]
        if now - t < 60
    ]

    # 限制每分钟 60 次
    if len(_rate_limit_cache[client_ip]) >= 60:
        raise HTTPException(status_code=429, detail="请求过于频繁，请稍后再试")

    _rate_limit_cache[client_ip].append(now)
    return client_ip
