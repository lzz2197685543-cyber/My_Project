"""
聊天相关数据模型
"""
from typing import Optional, List, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field, validator


class ProviderType(str, Enum):
    """提供商类型"""
    YI = "yi"
    BAILIAN = "bailian"


class ChatRequest(BaseModel):
    """聊天请求"""
    messages: List[Dict[str, str]] = Field(
        ...,
        min_length=1,
        description="对话消息列表，至少包含1条消息"
    )
    model: str = Field(
        default="deepseek-chat",
        description="模型名称"
    )
    provider: ProviderType = Field(
        default=ProviderType.YI,
        description="服务提供商"
    )
    max_tokens: int = Field(
        default=1024,
        ge=1,
        le=8192,
        description="最大生成 token 数"
    )
    temperature: float = Field(
        default=0.7,
        ge=0,
        le=2,
        description="温度参数，控制随机性"
    )
    stream: bool = Field(
        default=False,
        description="是否流式输出"
    )

    @validator('messages')
    def validate_messages(cls, v):
        """验证消息格式"""
        if not v:
            raise ValueError('messages 不能为空')
        for msg in v:
            if 'role' not in msg or 'content' not in msg:
                raise ValueError('每条消息必须包含 role 和 content 字段')
            if msg['role'] not in ['system', 'user', 'assistant']:
                raise ValueError('role 必须是 system, user, 或 assistant')
        return v


class ChatResponse(BaseModel):
    """聊天响应"""
    content: str = Field(..., description="回复内容")
    model: str = Field(..., description="使用的模型")
    usage: Optional[Dict[str, int]] = Field(
        default=None,
        description="Token 使用情况"
    )


# ==================== 兼容 OpenAI 格式 ====================

class ChatCompletionRequest(BaseModel):
    """OpenAI 兼容格式请求"""
    messages: List[Dict[str, str]] = Field(..., description="对话消息")
    model: str = Field(..., description="模型名称")
    max_tokens: Optional[int] = Field(1024, ge=1, le=8192)
    temperature: Optional[float] = Field(0.7, ge=0, le=2)
    stream: Optional[bool] = Field(False)


class ChatCompletionResponse(BaseModel):
    """OpenAI 兼容格式响应"""
    id: str = Field(..., description="请求 ID")
    object: str = Field("chat.completion", description="对象类型")
    created: int = Field(..., description="创建时间戳")
    model: str = Field(..., description="使用的模型")
    choices: List[Dict[str, Any]] = Field(..., description="选择列表")
    usage: Optional[Dict[str, int]] = Field(None, description="Token 使用情况")