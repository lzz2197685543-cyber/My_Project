"""
百炼客户端
"""
import base64
import asyncio
import json
from pathlib import Path
from typing import Optional, List, Dict, Any

import aiohttp
import aiofiles

from app.clients.base_client import BaseClient
from config.settings import settings


class BailianClient(BaseClient):
    """百炼客户端"""

    # 百炼 API 地址
    BAILIAN_IMAGE_URL = "https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation"

    # ✅ 百炼支持的聊天模型列表
    BAILIAN_CHAT_MODELS = {
        # Qwen 系列
        "qwen3.8-max": {"display_name": "Qwen 3.8 Max", "type": "chat"},
        "qwen3.7-max": {"display_name": "Qwen 3.7 Max", "type": "chat"},
        "qwen3.6-plus": {"display_name": "Qwen 3.6 Plus", "type": "chat"},
        "qwen3.7-plus": {"display_name": "Qwen 3.7 Plus", "type": "chat"},
        "qwen3.6-flash": {"display_name": "Qwen 3.6 Flash", "type": "chat"},
        "qwen3.7-flash": {"display_name": "Qwen 3.7 Flash", "type": "chat"},
        "qwen-plus": {"display_name": "Qwen Plus", "type": "chat"},
        "qwen-turbo": {"display_name": "Qwen Turbo", "type": "chat"},
        "qwen-flash": {"display_name": "Qwen Flash", "type": "chat"},
        # DeepSeek 系列
        "deepseek-v4-pro": {"display_name": "DeepSeek V4 Pro", "type": "chat"},
        "deepseek-v4-flash": {"display_name": "DeepSeek V4 Flash", "type": "chat"},
        "deepseek-r1": {"display_name": "DeepSeek R1", "type": "chat"},
        # Kimi 系列
        "kimi-k2.7-code": {"display_name": "Kimi K2.7 Code", "type": "chat"},
        # GLM 系列
        "glm-5.2": {"display_name": "GLM 5.2", "type": "chat"},
        # MiniMax 系列
        "MiniMax-M2.5": {"display_name": "MiniMax M2.5", "type": "chat"},
        # MiMo 系列
        "mimo-v2.5-pro": {"display_name": "MiMo V2.5 Pro", "type": "chat"},
    }

    # ✅ 百炼支持的图片模型列表
    BAILIAN_IMAGE_MODELS = {
        # 文生图 + 图生图
        "wan2.7-image-pro": {
            "display_name": "万相2.7-Pro",
            "supports_text2img": True,
            "supports_img2img": True,
            "type": "image"
        },
        "wan2.7-image": {
            "display_name": "万相2.7",
            "supports_text2img": True,
            "supports_img2img": True,
            "type": "image"
        },
        "qwen-image-3.0-pro": {
            "display_name": "千问-Image-3.0-Pro",
            "supports_text2img": True,
            "supports_img2img": True,
            "type": "image"
        },
        "qwen-image-3.0": {
            "display_name": "千问-Image-3.0",
            "supports_text2img": True,
            "supports_img2img": True,
            "type": "image"
        },
        "qwen-image-2.0-pro": {
            "display_name": "千问-Image-2.0-Pro",
            "supports_text2img": True,
            "supports_img2img": True,
            "type": "image"
        },
        # 只支持文生图
        "z-image-turbo": {
            "display_name": "Z-Image-Turbo",
            "supports_text2img": True,
            "supports_img2img": False,
            "type": "image"
        },
        "qwen-image-2.0": {
            "display_name": "千问-Image-2.0",
            "supports_text2img": True,
            "supports_img2img": False,
            "type": "image"
        },
    }

    # ✅ 合并所有模型
    ALL_MODELS = {**BAILIAN_CHAT_MODELS, **BAILIAN_IMAGE_MODELS}

    def __init__(self, api_key: Optional[str] = None):
        """
        初始化 BailianClient

        Args:
            api_key: API Key，如果不传则从环境变量读取
        """
        # 获取 API Key
        api_key = api_key or settings.BAILIAN_API_KEY

        # 调用父类初始化
        super().__init__("bailian", api_key)

        # 设置基础 URL
        self.chat_url = settings.BAILIAN_BASE_URL

        # 日志记录
        if self.api_key:
            masked_key = f"{self.api_key[:8]}...{self.api_key[-4:]}"
            self.logger.info(f"✅ BailianClient 初始化完成，API Key: {masked_key}")
        else:
            self.logger.warning("⚠️ BailianClient 初始化完成，但 BAILIAN_API_KEY 未配置")

    def _get_api_key(self) -> Optional[str]:
        """获取 API Key"""
        return self.api_key or settings.BAILIAN_API_KEY

    # ==================== 模型管理方法 ====================

    @classmethod
    def get_supported_models(cls, model_type: str = "all") -> List[str]:
        """
        获取百炼支持的模型列表

        Args:
            model_type: 模型类型 (all, chat, image)

        Returns:
            模型ID列表
        """
        if model_type == "chat":
            return list(cls.BAILIAN_CHAT_MODELS.keys())
        elif model_type == "image":
            return list(cls.BAILIAN_IMAGE_MODELS.keys())
        else:
            return list(cls.ALL_MODELS.keys())

    @classmethod
    def get_models_with_info(cls, model_type: str = "all") -> List[Dict[str, Any]]:
        """
        获取百炼支持的模型列表（含详细信息）

        Args:
            model_type: 模型类型 (all, chat, image)

        Returns:
            模型信息列表
        """
        if model_type == "chat":
            models = cls.BAILIAN_CHAT_MODELS
        elif model_type == "image":
            models = cls.BAILIAN_IMAGE_MODELS
        else:
            models = cls.ALL_MODELS

        result = []
        for model_id, info in models.items():
            item = {
                "id": model_id,
                "display_name": info.get("display_name", model_id),
                "type": info.get("type", "unknown"),
            }
            # 图片模型额外信息
            if info.get("type") == "image":
                item["supports_text2img"] = info.get("supports_text2img", False)
                item["supports_img2img"] = info.get("supports_img2img", False)
            result.append(item)

        return result

    @classmethod
    def is_model_supported(cls, model: str) -> bool:
        """检查模型是否在百炼支持列表中"""
        return model in cls.ALL_MODELS

    @classmethod
    def is_chat_model(cls, model: str) -> bool:
        """检查是否是聊天模型"""
        return model in cls.BAILIAN_CHAT_MODELS

    @classmethod
    def is_image_model(cls, model: str) -> bool:
        """检查是否是图片模型"""
        return model in cls.BAILIAN_IMAGE_MODELS

    @classmethod
    def supports_text_to_image(cls, model: str) -> bool:
        """检查模型是否支持文生图"""
        config = cls.BAILIAN_IMAGE_MODELS.get(model)
        return config.get("supports_text2img", False) if config else False

    @classmethod
    def supports_image_to_image(cls, model: str) -> bool:
        """检查模型是否支持图生图"""
        config = cls.BAILIAN_IMAGE_MODELS.get(model)
        return config.get("supports_img2img", False) if config else False

    # ==================== 聊天补全 ====================

    async def chat_completion(
            self,
            messages: List[Dict[str, str]],
            model: str = "qwen3.8-max",
            max_tokens: int = 1024,
            temperature: float = 0.7,
            stream: bool = False,
            **kwargs
    ) -> Optional[str]:
        """
        聊天补全
        """
        if not self.api_key:
            self.logger.error("❌ BAILIAN_API_KEY 未配置")
            return "错误：BAILIAN_API_KEY 未配置，请检查环境变量"

        # 检查是否是聊天模型
        if not self.is_chat_model(model):
            supported = ", ".join(self.get_supported_models("chat"))
            return f"错误：模型 '{model}' 不是百炼的聊天模型。支持的聊天模型: {supported}"

        url = f"{self.chat_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": stream
        }

        try:
            async with aiohttp.ClientSession() as session:
                if stream:
                    return await self._handle_stream_chat(session, url, headers, payload)
                else:
                    async with session.post(url, headers=headers, json=payload, timeout=60) as resp:
                        if resp.status != 200:
                            error_text = await resp.text()
                            self.logger.error(f"HTTP {resp.status}: {error_text[:200]}")
                            return f"API 请求失败 (HTTP {resp.status})"

                        # 检查 Content-Type
                        content_type = resp.headers.get('Content-Type', '')
                        if 'text/event-stream' in content_type:
                            return await self._handle_stream_response(resp)

                        data = await resp.json()
                        # ✅ 安全获取 content
                        if "choices" in data and data["choices"]:
                            content = data["choices"][0].get("message", {}).get("content", "")
                        else:
                            content = data.get("content", "")
                        return content if content else "抱歉，我没有理解您的问题。"
        except asyncio.TimeoutError:
            self.logger.error("请求超时")
            return "请求超时，请稍后再试。"
        except Exception as e:
            self.logger.error(f"Bailian chat failed: {e}")
            return f"请求失败: {str(e)}"

    async def _handle_stream_chat(self, session, url, headers, payload):
        """处理流式聊天（百炼）"""
        try:
            async with session.post(url, headers=headers, json=payload, timeout=60) as resp:
                if resp.status != 200:
                    error_text = await resp.text()
                    self.logger.error(f"HTTP {resp.status}: {error_text[:200]}")
                    return f"API 请求失败 (HTTP {resp.status})"

                full_content = ""
                async for line in resp.content:
                    line = line.decode().strip()
                    if not line:
                        continue

                    if line.startswith("data: "):
                        data_str = line[6:]
                        if data_str == "[DONE]":
                            break
                        try:
                            chunk = json.loads(data_str)
                            # ✅ 安全获取 content
                            if "choices" in chunk and chunk["choices"]:
                                delta = chunk["choices"][0].get("delta", {})
                                content = delta.get("content", "")
                                if content:
                                    full_content += content
                            elif "content" in chunk:
                                content = chunk.get("content", "")
                                if content:
                                    full_content += content
                        except json.JSONDecodeError:
                            if data_str and data_str != "[DONE]":
                                full_content += data_str

                return full_content if full_content else "没有收到回复内容。"
        except asyncio.TimeoutError:
            self.logger.error("流式请求超时")
            return "请求超时，请稍后再试。"
        except Exception as e:
            self.logger.error(f"Stream chat failed: {e}")
            return f"流式请求失败: {str(e)}"

    async def _handle_stream_response(self, resp):
        """处理流式响应（当 stream=False 但返回流式时）"""
        try:
            full_content = ""
            async for line in resp.content:
                line = line.decode().strip()
                if not line:
                    continue

                if line.startswith("data: "):
                    data_str = line[6:]
                    if data_str == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data_str)
                        if "choices" in chunk and chunk["choices"]:
                            delta = chunk["choices"][0].get("delta", {})
                            content = delta.get("content", "")
                            if content:
                                full_content += content
                    except json.JSONDecodeError:
                        pass

            return full_content if full_content else "没有收到回复内容。"
        except Exception as e:
            self.logger.error(f"处理流式响应失败: {e}")
            return f"处理流式响应失败: {str(e)}"

    # ==================== 文生图 ====================

    async def text_to_image(
            self,
            prompt: str,
            model: str = "z-image-turbo",
            count: int = 1,
            aspect_ratio: str = "1:1",
            image_size: str = "1K",
            **kwargs
    ) -> Optional[Dict[str, Any]]:
        """文生图 - ✅ 添加模型验证"""
        if not self.api_key:
            self.logger.error("❌ BAILIAN_API_KEY 未配置")
            return {"success": False, "error": "BAILIAN_API_KEY 未配置"}

        # ✅ 检查模型是否存在
        if not self.is_model_supported(model):
            supported = ", ".join(self.get_supported_models("all"))
            return {
                "success": False,
                "error": f"模型 '{model}' 不在百炼支持列表中。支持的模型: {supported}"
            }

        # ✅ 检查是否是图片模型
        if not self.is_image_model(model):
            chat_models = ", ".join(self.get_supported_models("chat"))
            image_models = ", ".join(self.get_supported_models("image"))
            return {
                "success": False,
                "error": f"模型 '{model}' 是聊天模型，不支持文生图。\n聊天模型: {chat_models}\n图片模型: {image_models}"
            }

        # ✅ 检查模型是否支持文生图
        if not self.supports_text_to_image(model):
            supported = ", ".join([
                m for m in self.get_supported_models("image")
                if self.supports_text_to_image(m)
            ])
            return {
                "success": False,
                "error": f"模型 '{model}' 不支持文生图功能。支持文生图的模型: {supported}"
            }

        # 获取尺寸
        size = self._get_size_for_aspect(aspect_ratio, image_size)
        prompt_extend = kwargs.get("prompt_extend", False)

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        payload = {
            "model": model,
            "input": {
                "messages": [
                    {
                        "role": "user",
                        "content": [{"text": prompt}]
                    }
                ]
            },
            "parameters": {
                "size": size,
                "prompt_extend": prompt_extend,
                "n": count
            }
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                        self.BAILIAN_IMAGE_URL,
                        headers=headers,
                        json=payload,
                        timeout=aiohttp.ClientTimeout(total=settings.IMAGE_TIMEOUT)
                ) as resp:
                    if resp.status != 200:
                        error_text = await resp.text()
                        self.logger.error(f"HTTP {resp.status}: {error_text[:200]}")
                        return {"success": False, "error": f"HTTP {resp.status}: {error_text[:200]}"}

                    data = await resp.json()

                    images = []
                    if "output" in data and "choices" in data["output"]:
                        for choice in data["output"]["choices"]:
                            content = choice.get("message", {}).get("content", [])
                            for item in content:
                                if "image" in item:
                                    images.append({"url": item["image"]})

                    if not images:
                        return {"success": False, "error": "没有返回图片数据"}

                    return {"images": images, "success": True}
        except asyncio.TimeoutError:
            self.logger.error("文生图请求超时")
            return {"success": False, "error": "请求超时"}
        except Exception as e:
            self.logger.error(f"Bailian text to image failed: {e}")
            return {"success": False, "error": str(e)}

    # ==================== 图生图 ====================

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
        """图生图 - ✅ 添加模型验证"""
        if not self.api_key:
            self.logger.error("❌ BAILIAN_API_KEY 未配置")
            return {"success": False, "error": "BAILIAN_API_KEY 未配置"}

        # ✅ 检查模型是否存在
        if not self.is_model_supported(model):
            supported = ", ".join(self.get_supported_models("all"))
            return {
                "success": False,
                "error": f"模型 '{model}' 不在百炼支持列表中。支持的模型: {supported}"
            }

        # ✅ 检查是否是图片模型
        if not self.is_image_model(model):
            chat_models = ", ".join(self.get_supported_models("chat"))
            image_models = ", ".join(self.get_supported_models("image"))
            return {
                "success": False,
                "error": f"模型 '{model}' 是聊天模型，不支持图生图。\n聊天模型: {chat_models}\n图片模型: {image_models}"
            }

        # ✅ 检查模型是否支持图生图
        if not self.supports_image_to_image(model):
            supported = ", ".join([
                m for m in self.get_supported_models("image")
                if self.supports_image_to_image(m)
            ])
            return {
                "success": False,
                "error": f"模型 '{model}' 不支持图生图功能。支持图生图的模型: {supported}"
            }

        try:
            # 读取图片
            if Path(source_image).exists():
                async with aiofiles.open(source_image, 'rb') as f:
                    image_data = await f.read()
                    image_b64 = base64.b64encode(image_data).decode()
                mime_type = self._detect_mime_type(source_image)
            else:
                image_b64 = source_image
                mime_type = "image/png"

            # 获取尺寸
            size = self._get_size_for_aspect(aspect_ratio, image_size)
            prompt_extend = kwargs.get("prompt_extend", False)

            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }

            payload = {
                "model": model,
                "input": {
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {"image": f"data:{mime_type};base64,{image_b64}"},
                                {"text": prompt}
                            ]
                        }
                    ]
                },
                "parameters": {
                    "size": size,
                    "prompt_extend": prompt_extend,
                    "n": count
                }
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                        self.BAILIAN_IMAGE_URL,
                        headers=headers,
                        json=payload,
                        timeout=aiohttp.ClientTimeout(total=settings.IMAGE_TIMEOUT)
                ) as resp:
                    if resp.status != 200:
                        error_text = await resp.text()
                        self.logger.error(f"HTTP {resp.status}: {error_text[:200]}")
                        return {"success": False, "error": f"HTTP {resp.status}: {error_text[:200]}"}

                    data = await resp.json()

                    images = []
                    if "output" in data and "choices" in data["output"]:
                        for choice in data["output"]["choices"]:
                            content = choice.get("message", {}).get("content", [])
                            for item in content:
                                if "image" in item:
                                    images.append({"url": item["image"]})

                    if not images:
                        return {"success": False, "error": "没有返回图片数据"}

                    return {"images": images, "success": True}
        except FileNotFoundError:
            self.logger.error(f"图片文件不存在: {source_image}")
            return {"success": False, "error": f"图片文件不存在: {source_image}"}
        except Exception as e:
            self.logger.error(f"Bailian image to image failed: {e}")
            return {"success": False, "error": str(e)}

    # ==================== 多图融合 ====================

    async def fuse_images(
            self,
            image_paths: List[str],
            fusion_prompt: str,
            model: str,
            aspect_ratio: str = "1:1",
            image_size: str = "1K",
            **kwargs
    ) -> Optional[Dict[str, Any]]:
        """多图融合 - 百炼不支持真正的多图融合"""
        return {
            "success": False,
            "error": "百炼不支持真正的多图融合功能。请使用 API易 (yi) 提供商的 Gemini 或 GPT-Image 模型。"
        }

    # ==================== 辅助方法 ====================

    def _get_size_for_aspect(self, aspect_ratio: str, image_size: str) -> str:
        """根据宽高比和尺寸获取分辨率"""
        sizes = {
            "1:1": ["1024*1024", "2048*2048"],
            "16:9": ["1280*720", "1920*1080"],
            "9:16": ["720*1280", "1080*1920"],
            "3:2": ["1248*832", "1536*1024"],
            "2:3": ["832*1248", "1024*1536"],
            "4:3": ["1152*864", "1440*1080"],
            "3:4": ["864*1152", "1080*1440"],
            "21:9": ["1680*720", "2560*1080"]
        }
        size_list = sizes.get(aspect_ratio, ["1024*1024"])
        return size_list[1] if image_size == "2K" and len(size_list) > 1 else size_list[0]

    @staticmethod
    def _detect_mime_type(file_path: str) -> str:
        """检测文件MIME类型"""
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


if __name__ == '__main__':
    b = BailianClient()

    # 测试获取模型列表
    # print("=" * 60)
    # print("百炼支持的聊天模型:")
    # print("=" * 60)
    # for model in b.get_models_with_info("chat"):
    #     print(f"  - {model['id']}: {model['display_name']}")
    #
    # print("\n" + "=" * 60)
    # print("百炼支持的图片模型:")
    # print("=" * 60)
    # for model in b.get_models_with_info("image"):
    #     print(f"  - {model['id']}: {model['display_name']}")
    #     print(f"    文生图: {'✅' if model.get('supports_text2img') else '❌'}")
    #     print(f"    图生图: {'✅' if model.get('supports_img2img') else '❌'}")
    #
    # # 测试聊天
    # print("\n" + "=" * 60)
    # print("测试聊天:")
    # print("=" * 60)
    # print(asyncio.run(b.chat_completion(
    #     messages=[{"role": "user", "content": "你好，请介绍一下自己"}],
    #     model="qwen3.8-max"
    # )))
    print(asyncio.run(b.image_to_image(
        source_image='D:/AI_GEN/ai-gen-backend/data/input/14.jpg',
        prompt='帮我根据这张图片生成动漫的图片',
        model='qwen-image-2.0-pro'
    )))