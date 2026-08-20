"""
模型验证工具
统一管理各提供商支持的模型
"""
from typing import List, Dict, Any, Optional
from app.clients.yi_client import YIClient
from app.clients.bailian_client import BailianClient


class ModelValidator:
    """模型验证器 - 统一管理模型验证"""

    # 提供商配置
    PROVIDER_CONFIG = {
        "yi": {
            "name": "API易",
            "client_class": YIClient,
            "image_models": list(YIClient.ALL_IMAGE_MODELS.keys()),
            "chat_models": list(YIClient.CHAT_MODELS.keys()),
            "all_models": list(YIClient.ALL_MODELS.keys()),
        },
        "bailian": {
            "name": "百炼",
            "client_class": BailianClient,
            "image_models": list(BailianClient.BAILIAN_IMAGE_MODELS.keys()),
            "chat_models": list(BailianClient.BAILIAN_CHAT_MODELS.keys()),
            "all_models": list(BailianClient.ALL_MODELS.keys()),
        }
    }

    # ==================== 提供商信息 ====================

    @classmethod
    def get_providers(cls) -> List[str]:
        """获取所有提供商"""
        return list(cls.PROVIDER_CONFIG.keys())

    @classmethod
    def get_provider_name(cls, provider: str) -> str:
        """获取提供商名称"""
        config = cls.PROVIDER_CONFIG.get(provider)
        return config.get("name", provider) if config else provider

    @classmethod
    def get_provider_info(cls, provider: str) -> Optional[Dict[str, Any]]:
        """获取提供商完整信息"""
        config = cls.PROVIDER_CONFIG.get(provider)
        if not config:
            return None
        return {
            "id": provider,
            "name": config.get("name"),
            "image_models_count": len(config.get("image_models", [])),
            "chat_models_count": len(config.get("chat_models", [])),
            "total_models": len(config.get("all_models", [])),
        }

    # ==================== 获取模型列表 ====================

    @classmethod
    def get_supported_models(
        cls,
        provider: str,
        model_type: str = "all"
    ) -> List[str]:
        """
        获取指定提供商支持的模型ID列表

        Args:
            provider: 提供商名称 (yi, bailian)
            model_type: 模型类型 (all, image, chat)

        Returns:
            模型ID列表
        """
        config = cls.PROVIDER_CONFIG.get(provider)
        if not config:
            return []

        if model_type == "all":
            return config.get("all_models", [])
        elif model_type == "image":
            return config.get("image_models", [])
        elif model_type == "chat":
            return config.get("chat_models", [])
        else:
            return []

    @classmethod
    def get_models_with_info(
        cls,
        provider: str,
        model_type: str = "all"
    ) -> List[Dict[str, Any]]:
        """
        获取指定提供商支持的模型列表（含详细信息）

        Args:
            provider: 提供商名称 (yi, bailian)
            model_type: 模型类型 (all, image, chat)

        Returns:
            模型信息列表
        """
        if provider == "yi":
            return cls._get_yi_models(model_type)
        elif provider == "bailian":
            return cls._get_bailian_models(model_type)
        else:
            return []

    @classmethod
    def _get_yi_models(cls, model_type: str = "all") -> List[Dict[str, Any]]:
        """获取 API易 模型列表"""
        result = []

        if model_type in ["all", "image"]:
            for model_id, info in YIClient.ALL_IMAGE_MODELS.items():
                item = {
                    "id": model_id,
                    "display_name": info.get("display_name", model_id),
                    "type": info.get("type", "image"),
                    "provider": "yi",
                    "provider_name": "API易",
                    "api_type": info.get("api_type", "unknown"),
                    "supports_img2img": info.get("supports_img2img", False),
                }
                result.append(item)

        if model_type in ["all", "chat"]:
            for model_id, info in YIClient.CHAT_MODELS.items():
                item = {
                    "id": model_id,
                    "display_name": info.get("display_name", model_id),
                    "type": info.get("type", "chat"),
                    "provider": "yi",
                    "provider_name": "API易",
                }
                result.append(item)

        return result

    @classmethod
    def _get_bailian_models(cls, model_type: str = "all") -> List[Dict[str, Any]]:
        """获取百炼模型列表"""
        result = []

        if model_type in ["all", "image"]:
            for model_id, info in BailianClient.BAILIAN_IMAGE_MODELS.items():
                item = {
                    "id": model_id,
                    "display_name": info.get("display_name", model_id),
                    "type": info.get("type", "image"),
                    "provider": "bailian",
                    "provider_name": "百炼",
                    "supports_text2img": info.get("supports_text2img", False),
                    "supports_img2img": info.get("supports_img2img", False),
                }
                result.append(item)

        if model_type in ["all", "chat"]:
            for model_id, info in BailianClient.BAILIAN_CHAT_MODELS.items():
                item = {
                    "id": model_id,
                    "display_name": info.get("display_name", model_id),
                    "type": info.get("type", "chat"),
                    "provider": "bailian",
                    "provider_name": "百炼",
                }
                result.append(item)

        return result

    # ==================== 模型验证 ====================

    @classmethod
    def is_model_supported(cls, provider: str, model: str) -> bool:
        """
        检查模型是否被指定提供商支持

        Args:
            provider: 提供商名称
            model: 模型名称

        Returns:
            True 如果支持，否则 False
        """
        if provider not in cls.PROVIDER_CONFIG:
            return False

        all_models = cls.PROVIDER_CONFIG[provider].get("all_models", [])
        return model in all_models

    @classmethod
    def is_chat_model(cls, provider: str, model: str) -> bool:
        """检查是否是指定提供商的聊天模型"""
        if provider not in cls.PROVIDER_CONFIG:
            return False
        return model in cls.PROVIDER_CONFIG[provider].get("chat_models", [])

    @classmethod
    def is_image_model(cls, provider: str, model: str) -> bool:
        """检查是否是指定提供商的图片模型"""
        if provider not in cls.PROVIDER_CONFIG:
            return False
        return model in cls.PROVIDER_CONFIG[provider].get("image_models", [])

    @classmethod
    def get_model_type(cls, provider: str, model: str) -> Optional[str]:
        """
        获取模型类型

        Args:
            provider: 提供商名称
            model: 模型名称

        Returns:
            "chat", "image" 或 None
        """
        if cls.is_chat_model(provider, model):
            return "chat"
        elif cls.is_image_model(provider, model):
            return "image"
        return None

    @classmethod
    def get_model_info(cls, provider: str, model: str) -> Optional[Dict[str, Any]]:
        """
        获取模型详细信息

        Args:
            provider: 提供商名称
            model: 模型名称

        Returns:
            模型信息字典，如果不支持则返回 None
        """
        if provider == "yi":
            if model in YIClient.ALL_IMAGE_MODELS:
                return {
                    "provider": "yi",
                    "provider_name": "API易",
                    "model": model,
                    "type": "image",
                    **YIClient.ALL_IMAGE_MODELS[model]
                }
            elif model in YIClient.CHAT_MODELS:
                return {
                    "provider": "yi",
                    "provider_name": "API易",
                    "model": model,
                    "type": "chat",
                    **YIClient.CHAT_MODELS[model]
                }
        elif provider == "bailian":
            if model in BailianClient.BAILIAN_IMAGE_MODELS:
                return {
                    "provider": "bailian",
                    "provider_name": "百炼",
                    "model": model,
                    "type": "image",
                    **BailianClient.BAILIAN_IMAGE_MODELS[model]
                }
            elif model in BailianClient.BAILIAN_CHAT_MODELS:
                return {
                    "provider": "bailian",
                    "provider_name": "百炼",
                    "model": model,
                    "type": "chat",
                    **BailianClient.BAILIAN_CHAT_MODELS[model]
                }

        return None

    @classmethod
    def validate_model(
        cls,
        provider: str,
        model: str,
        model_type: str = "all"
    ) -> Dict[str, Any]:
        """
        验证模型是否被支持

        Args:
            provider: 提供商名称 (yi, bailian)
            model: 模型名称
            model_type: 模型类型 (all, image, chat)

        Returns:
            {
                "valid": bool,
                "error": Optional[str],
                "supported_models": List[str],
                "provider_name": str,
                "model_type": str
            }
        """
        provider_name = cls.get_provider_name(provider)

        # 检查提供商是否存在
        if provider not in cls.PROVIDER_CONFIG:
            return {
                "valid": False,
                "error": f"不支持的提供商: '{provider}'。支持的提供商: {cls.get_providers()}",
                "supported_models": [],
                "provider_name": provider,
                "model_type": "unknown"
            }

        # 获取支持的模型
        supported = cls.get_supported_models(provider, model_type)

        # 检查模型是否被支持
        if not cls.is_model_supported(provider, model):
            # 获取模型实际类型
            actual_type = cls.get_model_type(provider, model)

            if actual_type and model_type != "all" and actual_type != model_type:
                # 模型存在但类型不匹配
                return {
                    "valid": False,
                    "error": f"模型 '{model}' 是 {actual_type} 模型，但请求的是 {model_type} 模型。\n"
                             f"支持的 {model_type} 模型: {supported}",
                    "supported_models": supported,
                    "provider_name": provider_name,
                    "model_type": actual_type
                }
            else:
                # 模型不存在
                all_supported = cls.get_supported_models(provider, "all")
                return {
                    "valid": False,
                    "error": f"模型 '{model}' 不被提供商 '{provider_name}' 支持。\n"
                             f"支持的模型: {all_supported}",
                    "supported_models": all_supported,
                    "provider_name": provider_name,
                    "model_type": None
                }

        return {
            "valid": True,
            "error": None,
            "supported_models": supported,
            "provider_name": provider_name,
            "model_type": cls.get_model_type(provider, model)
        }

    # ==================== 统计和对比 ====================

    @classmethod
    def get_model_comparison(cls) -> Dict[str, Any]:
        """
        获取所有提供商模型的对比信息
        """
        comparison = {}

        for provider in cls.get_providers():
            config = cls.PROVIDER_CONFIG.get(provider)
            if not config:
                continue

            comparison[provider] = {
                "id": provider,
                "name": config.get("name"),
                "image_models": config.get("image_models", []),
                "chat_models": config.get("chat_models", []),
                "image_count": len(config.get("image_models", [])),
                "chat_count": len(config.get("chat_models", [])),
                "total_models": len(config.get("all_models", [])),
            }

        return comparison

    @classmethod
    def search_model(cls, keyword: str) -> List[Dict[str, Any]]:
        """
        在所有提供商中搜索模型

        Args:
            keyword: 搜索关键词

        Returns:
            匹配的模型列表
        """
        results = []

        for provider in cls.get_providers():
            models = cls.get_models_with_info(provider, "all")
            for model in models:
                if (keyword.lower() in model["id"].lower() or
                    keyword.lower() in model["display_name"].lower()):
                    results.append(model)

        return results


# ==================== 使用示例 ====================

if __name__ == "__main__":
    print("=" * 70)
    print("🧪 模型验证工具测试")
    print("=" * 70)

    # 1. 获取提供商信息
    print("\n📋 提供商列表:")
    for provider in ModelValidator.get_providers():
        info = ModelValidator.get_provider_info(provider)
        print(f"  - {info['name']} ({info['id']})")
        print(f"    图片模型: {info['image_models_count']} 个")
        print(f"    聊天模型: {info['chat_models_count']} 个")
        print(f"    总计: {info['total_models']} 个")

    # 2. 获取 API易 所有模型
    print("\n" + "=" * 70)
    print("📸 API易 图片模型:")
    print("=" * 70)
    for model in ModelValidator.get_models_with_info("yi", "image"):
        print(f"  - {model['id']}: {model['display_name']}")
        print(f"    图生图: {'✅' if model.get('supports_img2img') else '❌'}")

    print("\n💬 API易 聊天模型:")
    for model in ModelValidator.get_models_with_info("yi", "chat"):
        print(f"  - {model['id']}: {model['display_name']}")

    # 3. 获取百炼所有模型
    print("\n" + "=" * 70)
    print("📸 百炼 图片模型:")
    print("=" * 70)
    for model in ModelValidator.get_models_with_info("bailian", "image"):
        print(f"  - {model['id']}: {model['display_name']}")
        print(f"    文生图: {'✅' if model.get('supports_text2img') else '❌'}")
        print(f"    图生图: {'✅' if model.get('supports_img2img') else '❌'}")

    print("\n💬 百炼 聊天模型:")
    for model in ModelValidator.get_models_with_info("bailian", "chat"):
        print(f"  - {model['id']}: {model['display_name']}")

    # 4. 模型验证测试
    print("\n" + "=" * 70)
    print("🔍 模型验证测试")
    print("=" * 70)

    test_cases = [
        ("yi", "gemini-3.1-flash-lite-image", "image"),
        ("yi", "deepseek-chat", "chat"),
        ("bailian", "qwen3.8-max", "chat"),
        ("bailian", "wan2.7-image-pro", "image"),
        ("bailian", "gemini-3.1-flash-lite-image", "image"),  # ❌ 不支持
        ("yi", "qwen3.8-max", "chat"),  # ❌ API易 不支持 qwen3.8-max
        ("yi", "gemini-3.1-flash-lite-image", "chat"),  # ❌ 类型不匹配
    ]

    for provider, model, model_type in test_cases:
        result = ModelValidator.validate_model(provider, model, model_type)
        status = "✅" if result["valid"] else "❌"
        print(f"\n{status} {provider}/{model} ({model_type}):")
        if result["valid"]:
            print(f"   类型: {result['model_type']}")
        else:
            print(f"   错误: {result['error']}")

    # 5. 搜索模型
    print("\n" + "=" * 70)
    print("🔎 搜索模型 (关键词: 'gemini')")
    print("=" * 70)
    results = ModelValidator.search_model("gemini")
    for model in results:
        print(f"  - [{model['provider_name']}] {model['id']}: {model['display_name']}")

    # 6. 模型对比
    print("\n" + "=" * 70)
    print("📊 模型对比")
    print("=" * 70)
    comparison = ModelValidator.get_model_comparison()
    for provider, info in comparison.items():
        print(f"\n{info['name']}:")
        print(f"  图片模型: {info['image_count']} 个")
        print(f"  聊天模型: {info['chat_count']} 个")
        print(f"  总计: {info['total_models']} 个")