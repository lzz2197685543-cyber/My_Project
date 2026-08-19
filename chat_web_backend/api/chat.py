from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from services.deepseek import deepseek_service

router = APIRouter(prefix="/api/chat", tags=["chat"])


class ChatRequest(BaseModel):
    model: str = "deepseek-v4-flash"
    message: str
    system_prompt: Optional[str] = "你是一个乐于助人的助手"
    max_tokens: Optional[int] = 1024
    temperature: Optional[float] = 0.7


class ChatResponse(BaseModel):
    success: bool
    content: Optional[str] = None
    error: Optional[str] = None
    usage: Optional[dict] = None


@router.post("/", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    result = await deepseek_service.chat(
        model=request.model,
        user_message=request.message,
        system_prompt=request.system_prompt,
        max_tokens=request.max_tokens,
        temperature=request.temperature
    )

    if not result["success"]:
        raise HTTPException(status_code=500, detail=result["error"])

    return ChatResponse(
        success=True,
        content=result["content"],
        usage=result.get("usage")
    )


@router.get("/models")
async def get_models():
    # 返回可用的模型列表
    return {
        "models": [
            "deepseek-v4-flash",
            "deepseek-chat",
            "deepseek-coder"
        ]
    }