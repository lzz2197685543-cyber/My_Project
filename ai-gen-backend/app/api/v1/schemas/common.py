"""
通用响应模型
"""
from typing import Optional, Any, Generic, TypeVar
from datetime import datetime
from pydantic import BaseModel, Field

T = TypeVar('T')


class Response(BaseModel, Generic[T]):
    """统一响应格式"""
    code: int = Field(200, description="状态码")
    message: str = Field("success", description="消息")
    data: Optional[T] = Field(None, description="数据")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat(), # 👈 默认工厂
                           description="时间戳")

    @classmethod
    def success(cls, data: Any = None, message: str = "success") -> "Response":
        """创建成功响应"""
        return cls(code=200, message=message, data=data)

    @classmethod
    def error(cls, message: str = "error", code: int = 400, data: Any = None) -> "Response":
        """创建错误响应"""
        return cls(code=code, message=message, data=data)


class PaginatedResponse(BaseModel, Generic[T]):
    """分页响应"""
    items: list[T] = Field(..., description="数据列表")
    total: int = Field(..., description="总数")
    page: int = Field(1, description="当前页码")
    page_size: int = Field(20, description="每页数量")
    total_pages: int = Field(..., description="总页数")



