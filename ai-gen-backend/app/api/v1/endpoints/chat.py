"""
聊天 API 端点
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse, JSONResponse
import json
import time

from app.api.v1.schemas.chat import ChatRequest, ChatResponse
from app.api.v1.schemas.common import Response
from app.services.chat_service import ChatService
from app.core.dependencies import get_chat_service, get_api_key_from_header, check_rate_limit
from app.utils.logger import get_logger  # ✅ 添加 logger 导入

logger = get_logger("chat_endpoint")  # ✅ 创建 logger 实例

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("/completions", response_model=Response[ChatResponse])
async def chat_completions(
        request: ChatRequest,
        chat_service: ChatService = Depends(get_chat_service),
        api_key: Optional[str] = Depends(get_api_key_from_header),
        _: str = Depends(check_rate_limit)
):
    """
    聊天补全接口

    - **messages**: 对话消息列表，包含 role 和 content
    - **model**: 模型名称 (默认: deepseek-chat)
    - **provider**: 提供商 (yi/bailian)
    - **max_tokens**: 最大生成 token 数 (1-8192)
    - **temperature**: 温度参数 (0-2)
    - **stream**: 是否流式输出
    """
    try:
        result = await chat_service.chat(
            messages=request.messages,
            model=request.model,
            provider=request.provider.value,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            stream=request.stream,
            api_key=api_key
        )

        if result is None:
            return Response.error("聊天请求失败，请稍后重试", 500)

        # 检查是否返回了错误信息
        if result.startswith("错误") or result.startswith("API 错误") or result.startswith("请求失败"):
            return Response.error(result, 500)

        return Response.success(
            data=ChatResponse(content=result, model=request.model)
        )

    except Exception as e:
        logger.error(f"聊天补全异常: {e}")  # ✅ 添加日志
        return Response.error(f"聊天请求异常: {str(e)}", 500)


@router.post("/stream")
async def chat_stream(
        request: ChatRequest,
        chat_service: ChatService = Depends(get_chat_service),
        api_key: Optional[str] = Depends(get_api_key_from_header),
        _: str = Depends(check_rate_limit)
):
    """
    流式聊天接口
    """
    async def generate():
        try:
            async for chunk in chat_service.stream_chat(
                messages=request.messages,
                model=request.model,
                provider=request.provider.value,
                max_tokens=request.max_tokens,
                temperature=request.temperature,
                api_key=api_key
            ):
                yield chunk
        except Exception as e:
            logger.error(f"流式生成异常: {e}")  # ✅ logger 现在可用
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
            yield "data: [DONE]\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )