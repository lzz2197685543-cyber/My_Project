"""
API 客户端基类
"""
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any

from app.utils.logger import get_logger


class BaseClient(ABC):
    """AI 客户端基类"""

    def __init__(self, provider: str, api_key: Optional[str] = None):
        """
        初始化客户端

        Args:
            provider: 提供商名称 (yi, bailian)
            api_key: API 密钥
        """
        self.provider = provider
        self.api_key = api_key
        self.logger = get_logger(f"client_{provider}")

    @abstractmethod
    def _get_api_key(self) -> Optional[str]:
        """获取 API Key"""
        pass

    @abstractmethod
    async def chat_completion(
            self,
            messages: List[Dict[str, str]],
            model: str,
            max_tokens: int = 1024,
            temperature: float = 0.7,
            stream: bool = False,
            **kwargs
    ) -> Optional[str]:
        """
        聊天补全

        Args:
            messages: 对话消息列表
            model: 模型名称
            max_tokens: 最大生成 token 数
            temperature: 温度参数
            stream: 是否流式输出

        Returns:
            生成的回复内容
        """
        pass

    @abstractmethod
    async def text_to_image(
            self,
            prompt: str,
            model: str,
            count: int = 1,
            aspect_ratio: str = "1:1",
            image_size: str = "1K",
            **kwargs
    ) -> Optional[Dict[str, Any]]:
        """
        文生图

        Args:
            prompt: 提示词
            model: 模型名称
            count: 生成数量
            aspect_ratio: 宽高比
            image_size: 图片尺寸

        Returns:
            生成结果
        """
        pass

    @abstractmethod
    async def image_to_image(
            self,
            source_image: str,
            prompt: str,
            model: str,
            count: int = 1,
            aspect_ratio: str = "1:1",
            image_size: str = "1K",
            **kwargs
    ) -> Optional[Dict[str, Any]]:
        """
        图生图

        Args:
            source_image: 源图片路径或 base64
            prompt: 提示词
            model: 模型名称
            count: 生成数量
            aspect_ratio: 宽高比
            image_size: 图片尺寸

        Returns:
            生成结果
        """
        pass

    @abstractmethod
    async def fuse_images(
            self,
            image_paths: List[str],
            fusion_prompt: str,
            model: str,
            aspect_ratio: str = "1:1",
            image_size: str = "1K",
            **kwargs
    ) -> Optional[Dict[str, Any]]:
        """
        多图融合

        Args:
            image_paths: 图片路径列表
            fusion_prompt: 融合提示词
            model: 模型名称
            aspect_ratio: 宽高比
            image_size: 图片尺寸

        Returns:
            融合结果
        """
        pass

    @staticmethod
    def _detect_mime_type(file_path: str) -> str:
        """检测文件 MIME 类型"""
        from pathlib import Path
        suffix = Path(file_path).suffix.lower()
        mime_map = {
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.gif': 'image/gif',
            '.webp': 'image/webp',
            '.bmp': 'image/bmp',
            '.tiff': 'image/tiff'
        }
        return mime_map.get(suffix, 'image/png')