"""
自定义异常和异常处理器
"""
from typing import Optional, Any, Dict
from datetime import datetime
from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from app.utils.logger import get_logger

logger = get_logger("exceptions")


# ==================== 自定义异常类 ====================

class APIException(Exception):
    """API 基础异常"""

    def __init__(
            self,
            code: int = 500,
            message: str = "服务器内部错误",
            data: Optional[Any] = None,
            details: Optional[Dict] = None
    ):
        self.code = code
        self.message = message
        self.data = data
        self.details = details or {}
        super().__init__(self.message)


class AuthenticationError(APIException):
    """认证错误"""

    def __init__(self, message: str = "认证失败，请提供有效的 API Key"):
        super().__init__(code=401, message=message)


class ProviderError(APIException):
    """提供商错误"""

    def __init__(self, provider: str, message: str, code: int = 503):
        super().__init__(
            code=code,
            message=f"提供商 '{provider}' 服务错误: {message}",
            details={"provider": provider}
        )


class ModelNotFoundError(APIException):
    """模型不存在"""

    def __init__(self, model: str, provider: str):
        super().__init__(
            code=404,
            message=f"模型 '{model}' 在提供商 '{provider}' 中不存在",
            details={"model": model, "provider": provider}
        )


class RateLimitError(APIException):
    """速率限制错误"""

    def __init__(self, message: str = "请求过于频繁，请稍后再试"):
        super().__init__(code=429, message=message)


class ImageGenerationError(APIException):
    """图片生成错误"""

    def __init__(self, message: str, code: int = 500):
        super().__init__(code=code, message=message)


class ChatCompletionError(APIException):
    """聊天补全错误"""

    def __init__(self, message: str, code: int = 500):
        super().__init__(code=code, message=message)


# ==================== 异常处理器 ====================

async def api_exception_handler(request: Request, exc: APIException):
    """API 异常处理器"""
    logger.error(f"API 异常: {exc.message}, 详情: {exc.details}")
    return JSONResponse(
        status_code=exc.code,
        content={
            "code": exc.code,
            "message": exc.message,
            "data": exc.data,
            "details": exc.details,
            "timestamp": datetime.now().isoformat()
        }
    )


async def http_exception_handler(request: Request, exc: HTTPException):
    """HTTP 异常处理器"""
    logger.warning(f"HTTP 异常: {exc.status_code} - {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "code": exc.status_code,
            "message": str(exc.detail),
            "data": None,
            "details": {},
            "timestamp": datetime.now().isoformat()
        }
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """验证异常处理器"""
    errors = []
    for error in exc.errors():
        errors.append({
            "field": ".".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "type": error["type"]
        })

    logger.warning(f"验证失败: {errors}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "code": 422,
            "message": "请求参数验证失败",
            "data": None,
            "details": {"errors": errors},
            "timestamp": datetime.now().isoformat()
        }
    )


async def general_exception_handler(request: Request, exc: Exception):
    """通用异常处理器"""
    import traceback
    logger.error(f"未捕获的异常: {traceback.format_exc()}")
    return JSONResponse(
        status_code=500,
        content={
            "code": 500,
            "message": "服务器内部错误",
            "data": None,
            "details": {"error": str(exc) if exc else "未知错误"},
            "timestamp": datetime.now().isoformat()
        }
    )


def register_exception_handlers(app):
    """注册异常处理器"""
    app.add_exception_handler(APIException, api_exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)
    logger.info("✅ 异常处理器注册完成")
    return app