"""
AI 客户端工厂
"""
from typing import Optional

from app.clients.base_client import BaseClient
from app.clients.yi_client import YIClient
from app.clients.bailian_client import BailianClient
from app.utils.logger import get_logger

logger = get_logger("ai_service")


class AIClientFactory:
    """AI 客户端工厂 - 单例模式管理客户端实例"""

    _clients: dict = {}

    @classmethod
    def get_client(cls, provider: str, api_key: Optional[str] = None) -> BaseClient:
        """
        获取客户端实例（单例）

        Args:
            provider: 提供商名称 (yi, bailian)
            api_key: API Key（可选）

        Returns:
            BaseClient: 客户端实例

        Raises:
            ValueError: 不支持的提供商
        """
        # 生成缓存键
        cache_key = f"{provider}:{api_key[:8] if api_key else 'default'}"

        # 如果已存在，返回缓存的实例
        if cache_key in cls._clients:
            return cls._clients[cache_key]

        # 创建新实例
        logger.info(f"🔄 创建新的客户端: provider={provider}")

        if provider == "yi":
            client = YIClient(api_key)
        elif provider == "bailian":
            client = BailianClient(api_key)
        else:
            raise ValueError(f"不支持的提供商: {provider}")

        # 缓存实例
        cls._clients[cache_key] = client
        return client

    @classmethod
    def clear_cache(cls):
        """清除所有缓存的客户端实例"""
        cls._clients.clear()
        logger.info("✅ 客户端缓存已清除")

    @classmethod
    def get_available_providers(cls) -> list:
        """获取所有可用的提供商"""
        return ["yi", "bailian"]

    @classmethod
    def get_models_for_provider(cls, provider: str) -> list:
        """
        获取指定提供商支持的模型列表

        Args:
            provider: 提供商名称

        Returns:
            list: 模型列表
        """
        models = {
            "yi": [
                # Gemini 系列
                {"id": "gemini-3.1-flash-lite-image", "name": "Gemini 3.1 Flash Lite", "type": "image"},
                {"id": "gemini-3.1-flash-image-preview", "name": "Gemini 3.1 Flash", "type": "image"},
                {"id": "gemini-2.5-flash-image", "name": "Gemini 2.5 Flash", "type": "image"},
                {"id": "gemini-3-pro-image-preview", "name": "Gemini 3 Pro", "type": "image"},
                # GPT-Image 系列
                {"id": "gpt-image-2", "name": "GPT-Image 2", "type": "image"},
                {"id": "gpt-image-2-all", "name": "GPT-Image 2 All", "type": "image"},
                {"id": "gpt-image-2-vip", "name": "GPT-Image 2 VIP", "type": "image"},
                # Chat 模型
                {"id": "deepseek-chat", "name": "DeepSeek Chat", "type": "chat"},
                {"id": "deepseek-reasoner", "name": "DeepSeek Reasoner", "type": "chat"},
                {"id": "deepseek-v4-flash", "name": "DeepSeek V4 Flash", "type": "chat"},
                {"id": "deepseek-v3.2", "name": "DeepSeek V3.2", "type": "chat"},
                {"id": "qwen3.6-flash", "name": "Qwen 3.6 Flash", "type": "chat"},
                {"id": "gemini-2.5-flash", "name": "Gemini 2.5 Flash", "type": "chat"},
                {"id": "gpt-4.1-mini", "name": "GPT 4.1 Mini", "type": "chat"},
                {"id": "claude-haiku-4-5-20251001", "name": "Claude Haiku 4.5", "type": "chat"},
                {"id": "qwen3.5-flash", "name": "Qwen 3.5 Flash", "type": "chat"},
                {"id": "gpt-4o-mini", "name": "GPT 4o Mini", "type": "chat"},
                {"id": "gpt-5.4-pro", "name": "GPT 5.4 Pro", "type": "chat"},
                {"id": "claude-opus-5", "name": "Claude Opus 5", "type": "chat"},
                {"id": "gemini-3.1-pro-preview", "name": "Gemini 3.1 Pro", "type": "chat"}
            ],
            "bailian": [
                # 百炼图片模型
                {"id": "z-image-turbo", "name": "Z-Image-Turbo", "type": "image"},
                {"id": "wan2.7-image-pro", "name": "万相 2.7 Pro", "type": "image"},
                {"id": "wan2.7-image", "name": "万相 2.7", "type": "image"},
                {"id": "qwen-image-3.0-pro", "name": "千问 Image 3.0 Pro", "type": "image"},
                {"id": "qwen-image-3.0", "name": "千问 Image 3.0", "type": "image"},
                {"id": "qwen-image-2.0-pro", "name": "千问 Image 2.0 Pro", "type": "image"},
                {"id": "qwen-image-2.0", "name": "千问 Image 2.0", "type": "image"},
                # Chat 模型
                {"id": "qwen3.8-max", "name": "Qwen 3.8 Max", "type": "chat"},
                {"id": "qwen3.7-max", "name": "Qwen 3.7 Max", "type": "chat"},
                {"id": "qwen3.6-plus", "name": "Qwen 3.6 Plus", "type": "chat"},
                {"id": "qwen3.7-plus", "name": "Qwen 3.7 Plus", "type": "chat"},
                {"id": "qwen3.6-flash", "name": "Qwen 3.6 Flash", "type": "chat"},
                {"id": "qwen3.7-flash", "name": "Qwen 3.7 Flash", "type": "chat"},
                {"id": "qwen-plus", "name": "Qwen Plus", "type": "chat"},
                {"id": "qwen-turbo", "name": "Qwen Turbo", "type": "chat"},
                {"id": "qwen-flash", "name": "Qwen Flash", "type": "chat"},
                {"id": "deepseek-v4-pro", "name": "DeepSeek V4 Pro", "type": "chat"},
                {"id": "deepseek-v4-flash", "name": "DeepSeek V4 Flash", "type": "chat"},
                {"id": "deepseek-r1", "name": "DeepSeek R1", "type": "chat"},
                {"id": "kimi-k2.7-code", "name": "Kimi K2.7 Code", "type": "chat"},
                {"id": "glm-5.2", "name": "GLM 5.2", "type": "chat"},
                {"id": "MiniMax-M2.5", "name": "MiniMax M2.5", "type": "chat"},
                {"id": "mimo-v2.5-pro", "name": "MiMo V2.5 Pro", "type": "chat"},
            ]
        }
        return models.get(provider, [])