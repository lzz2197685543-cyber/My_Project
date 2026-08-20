"""
API易客户端
"""
import base64
import json
import asyncio
from pathlib import Path
from typing import Optional, List, Dict, Any

import aiohttp
import aiofiles

from app.clients.base_client import BaseClient
from config.settings import settings


class YIClient(BaseClient):
    """API易客户端"""

    # ✅ API易 支持的 Gemini 图片模型
    GEMINI_IMAGE_MODELS = {
        "gemini-3.1-flash-lite-image": {
            "display_name": "Gemini 3.1 Flash Lite",
            "api_type": "generateContent",
            "supports_img2img": True,
            "type": "image"
        },
        "gemini-3.1-flash-image-preview": {
            "display_name": "Gemini 3.1 Flash",
            "api_type": "generateContent",
            "supports_img2img": True,
            "type": "image"
        },
        "gemini-2.5-flash-image": {
            "display_name": "Gemini 2.5 Flash",
            "api_type": "generateContent",
            "supports_img2img": True,
            "type": "image"
        },
        "gemini-3-pro-image-preview": {
            "display_name": "Gemini 3 Pro",
            "api_type": "generateContent",
            "supports_img2img": True,
            "type": "image"
        },
    }

    # ✅ API易 支持的 GPT-Image 模型
    GPT_IMAGE_MODELS = {
        "gpt-image-2": {
            "display_name": "GPT-Image 2",
            "api_type": "generations",
            "supports_img2img": True,
            "type": "image"
        },
        "gpt-image-2-all": {
            "display_name": "GPT-Image 2 All",
            "api_type": "generations",
            "supports_img2img": True,
            "type": "image"
        },
        "gpt-image-2-vip": {
            "display_name": "GPT-Image 2 VIP",
            "api_type": "generations",
            "supports_img2img": True,
            "type": "image"
        },
    }

    # ✅ API易 支持的聊天模型
    CHAT_MODELS = {
        # DeepSeek 系列
        "deepseek-chat": {"display_name": "DeepSeek Chat", "type": "chat"},
        "deepseek-reasoner": {"display_name": "DeepSeek Reasoner", "type": "chat"},
        "deepseek-v4-flash": {"display_name": "DeepSeek V4 Flash", "type": "chat"},
        "deepseek-v3.2": {"display_name": "DeepSeek V3.2", "type": "chat"},
        # Qwen 系列
        "qwen3.6-flash": {"display_name": "Qwen 3.6 Flash", "type": "chat"},
        "qwen3.5-flash": {"display_name": "Qwen 3.5 Flash", "type": "chat"},
        # Gemini 系列（聊天）
        "gemini-2.5-flash": {"display_name": "Gemini 2.5 Flash", "type": "chat"},
        "gemini-3.1-pro-preview": {"display_name": "Gemini 3.1 Pro", "type": "chat"},
        # GPT 系列
        "gpt-4.1-mini": {"display_name": "GPT 4.1 Mini", "type": "chat"},
        "gpt-4o-mini": {"display_name": "GPT 4o Mini", "type": "chat"},
        "gpt-5.4-pro": {"display_name": "GPT 5.4 Pro", "type": "chat"},
        # Claude 系列
        "claude-haiku-4-5-20251001": {"display_name": "Claude Haiku 4.5", "type": "chat"},
        "claude-opus-5": {"display_name": "Claude Opus 5", "type": "chat"},
    }

    # ✅ 合并所有图片模型
    ALL_IMAGE_MODELS = {**GEMINI_IMAGE_MODELS, **GPT_IMAGE_MODELS}

    # ✅ 合并所有模型
    ALL_MODELS = {**ALL_IMAGE_MODELS, **CHAT_MODELS}

    def __init__(self, api_key: Optional[str] = None):
        """
        初始化 YIClient

        Args:
            api_key: API Key，如果不传则从环境变量读取
        """
        # 获取 API Key
        api_key = api_key or settings.YI_API_KEY

        # 调用父类初始化
        super().__init__("yi", api_key)

        # 设置基础 URL
        self.base_url = settings.YI_BASE_URL

        # 日志记录
        if self.api_key:
            masked_key = f"{self.api_key[:8]}...{self.api_key[-4:]}"
            self.logger.info(f"✅ YIClient 初始化完成，API Key: {masked_key}")
        else:
            self.logger.warning("⚠️ YIClient 初始化完成，但 YI_API_KEY 未配置")

    def _get_api_key(self) -> Optional[str]:
        """获取 API Key"""
        return self.api_key or settings.YI_API_KEY

    # ==================== 模型管理方法 ====================

    @classmethod
    def get_supported_models(cls, model_type: str = "all") -> List[str]:
        """
        获取 API易 支持的模型列表

        Args:
            model_type: 模型类型 (all, image, chat)

        Returns:
            模型ID列表
        """
        if model_type == "image":
            return list(cls.ALL_IMAGE_MODELS.keys())
        elif model_type == "chat":
            return list(cls.CHAT_MODELS.keys())
        else:
            return list(cls.ALL_MODELS.keys())

    @classmethod
    def get_models_with_info(cls, model_type: str = "all") -> List[Dict[str, Any]]:
        """
        获取 API易 支持的模型列表（含详细信息）

        Args:
            model_type: 模型类型 (all, image, chat)

        Returns:
            模型信息列表
        """
        if model_type == "image":
            models = cls.ALL_IMAGE_MODELS
        elif model_type == "chat":
            models = cls.CHAT_MODELS
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
                item["api_type"] = info.get("api_type", "unknown")
                item["supports_img2img"] = info.get("supports_img2img", False)
            result.append(item)

        return result

    @classmethod
    def is_model_supported(cls, model: str) -> bool:
        """检查模型是否在 API易 支持列表中"""
        return model in cls.ALL_MODELS

    @classmethod
    def is_chat_model(cls, model: str) -> bool:
        """检查是否是聊天模型"""
        return model in cls.CHAT_MODELS

    @classmethod
    def is_image_model(cls, model: str) -> bool:
        """检查是否是图片模型"""
        return model in cls.ALL_IMAGE_MODELS

    @classmethod
    def is_gpt_image_model(cls, model: str) -> bool:
        """检查是否是 GPT-Image 模型"""
        return model in cls.GPT_IMAGE_MODELS

    @classmethod
    def is_gemini_image_model(cls, model: str) -> bool:
        """检查是否是 Gemini 图片模型"""
        return model in cls.GEMINI_IMAGE_MODELS

    @classmethod
    def supports_image_to_image(cls, model: str) -> bool:
        """检查模型是否支持图生图"""
        config = cls.ALL_IMAGE_MODELS.get(model)
        return config.get("supports_img2img", False) if config else False

    # ==================== 聊天补全 ====================

    async def chat_completion(
            self,
            messages: List[Dict[str, str]],
            model: str = "deepseek-chat",
            max_tokens: int = 1024,
            temperature: float = 0.7,
            stream: bool = False,
            **kwargs
    ) -> Optional[str]:
        """
        聊天补全

        Args:
            messages: 消息列表
            model: 模型名称
            max_tokens: 最大 token 数
            temperature: 温度参数
            stream: 是否流式输出

        Returns:
            回复内容
        """
        # 检查 API Key
        if not self.api_key:
            self.logger.error("❌ YI_API_KEY 未配置")
            return "错误：YI_API_KEY 未配置，请检查环境变量或传入 API Key"

        # ✅ 检查聊天模型
        if not self.is_chat_model(model):
            supported = ", ".join(self.get_supported_models("chat"))
            return f"错误：模型 '{model}' 不是 API易 的聊天模型。支持的聊天模型: {supported}"

        url = f"{self.base_url}/chat/completions"
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

                        data = await resp.json()
                        content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                        return content if content else "抱歉，我没有理解您的问题。"
        except asyncio.TimeoutError:
            self.logger.error("请求超时")
            return "请求超时，请稍后再试。"
        except Exception as e:
            self.logger.error(f"Chat completion failed: {e}")
            return f"请求失败: {str(e)}"

    async def _handle_stream_chat(self, session, url, headers, payload):
        """处理流式聊天"""
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
                            # ✅ 安全地获取 content，避免索引越界
                            if "choices" in chunk and chunk["choices"]:
                                delta = chunk["choices"][0].get("delta", {})
                                content = delta.get("content", "")
                                if content:
                                    full_content += content
                            elif "content" in chunk:
                                # 直接包含 content
                                content = chunk.get("content", "")
                                if content:
                                    full_content += content
                        except json.JSONDecodeError:
                            # 如果不是 JSON，可能是纯文本
                            if data_str and data_str != "[DONE]":
                                full_content += data_str
                    elif line.startswith("{"):
                        # 直接是 JSON（非 SSE 格式）
                        try:
                            chunk = json.loads(line)
                            if "choices" in chunk and chunk["choices"]:
                                delta = chunk["choices"][0].get("delta", {})
                                content = delta.get("content", "")
                                if content:
                                    full_content += content
                        except json.JSONDecodeError:
                            pass

                return full_content if full_content else "没有收到回复内容。"
        except asyncio.TimeoutError:
            self.logger.error("流式请求超时")
            return "请求超时，请稍后再试。"
        except Exception as e:
            self.logger.error(f"Stream chat failed: {e}")
            return f"流式请求失败: {str(e)}"

    # ==================== 文生图 ====================

    async def text_to_image(
            self,
            prompt: str,
            model: str = "gemini-3.1-flash-lite-image",
            count: int = 1,
            aspect_ratio: str = "1:1",
            image_size: str = "1K",
            **kwargs
    ) -> Optional[Dict[str, Any]]:
        """文生图 - ✅ 添加模型验证"""
        if not self.api_key:
            self.logger.error("❌ YI_API_KEY 未配置")
            return {"success": False, "error": "YI_API_KEY 未配置"}

        # ✅ 检查模型是否存在
        if not self.is_image_model(model):
            supported = ", ".join(self.get_supported_models("image"))
            return {
                "success": False,
                "error": f"模型 '{model}' 不在 API易 图片模型支持列表中。支持的图片模型: {supported}"
            }

        is_gpt = self.is_gpt_image_model(model)
        if is_gpt:
            return await self._text_to_image_gpt(prompt, model, count, aspect_ratio)
        else:
            return await self._text_to_image_gemini(prompt, model, aspect_ratio, image_size)

    async def _text_to_image_gemini(
            self,
            prompt: str,
            model: str,
            aspect_ratio: str,
            image_size: str
    ) -> Optional[Dict[str, Any]]:
        """Gemini 文生图"""
        url = f"https://api.apiyi.com/v1beta/models/{model}:generateContent"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        image_config = {"aspectRatio": aspect_ratio}
        if "pro" in model:
            image_config["imageSize"] = "4K" if image_size == "4K" else "2K"
        elif "lite" in model:
            image_config["imageSize"] = "1K"
        else:
            image_config["imageSize"] = image_size

        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "responseModalities": ["IMAGE"],
                "imageConfig": image_config
            }
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                        url,
                        headers=headers,
                        json=payload,
                        timeout=aiohttp.ClientTimeout(total=settings.IMAGE_TIMEOUT)
                ) as resp:
                    if resp.status != 200:
                        error_text = await resp.text()
                        self.logger.error(f"HTTP {resp.status}: {error_text[:200]}")
                        return {"success": False, "error": f"HTTP {resp.status}"}

                    data = await resp.json()

                    # 检查响应状态
                    if "error" in data:
                        return {"success": False, "error": f"API错误: {data['error']}"}

                    # 解析图片数据
                    if "candidates" in data and data["candidates"]:
                        candidate = data["candidates"][0]

                        # 检查是否有 finishReason 表示失败
                        if candidate.get("finishReason") == "SAFETY":
                            return {"success": False, "error": "内容被安全策略拦截"}

                        if "content" in candidate and "parts" in candidate["content"]:
                            parts = candidate["content"]["parts"]
                            for part in parts:
                                if "inlineData" in part:
                                    img_data = part["inlineData"].get("data")
                                    if img_data:
                                        self.logger.info(f"✅ 图片数据获取成功，长度: {len(img_data)}")
                                        return {"image_data": img_data, "success": True}
                                elif "image" in part:
                                    img_data = part["image"]
                                    if img_data:
                                        self.logger.info(f"✅ 图片数据获取成功，长度: {len(img_data)}")
                                        return {"image_data": img_data, "success": True}

                    self.logger.error(f"❌ 无法解析图片数据")
                    return {"success": False, "error": "无法解析图片数据"}

        except asyncio.TimeoutError:
            self.logger.error("文生图请求超时")
            return {"success": False, "error": "请求超时"}
        except Exception as e:
            self.logger.error(f"Text to image failed: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return {"success": False, "error": str(e)}

    async def _text_to_image_gpt(
            self,
            prompt: str,
            model: str,
            count: int,
            aspect_ratio: str
    ) -> Optional[Dict[str, Any]]:
        """GPT-Image 文生图"""
        size_map = {
            "1:1": "1024x1024",
            "16:9": "2048x1152",
            "9:16": "1152x2048",
            "3:2": "1536x1024",
            "2:3": "1024x1536",
        }
        size = size_map.get(aspect_ratio, "1024x1024")

        url = "https://api.apiyi.com/v1/images/generations"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": model,
            "prompt": prompt,
            "size": size,
            "quality": "high",
            "n": count,
            "response_format": "b64_json"
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                        url,
                        headers=headers,
                        json=payload,
                        timeout=aiohttp.ClientTimeout(total=settings.IMAGE_TIMEOUT)
                ) as resp:
                    if resp.status != 200:
                        error_text = await resp.text()
                        self.logger.error(f"HTTP {resp.status}: {error_text[:200]}")
                        return {"success": False, "error": f"HTTP {resp.status}"}

                    data = await resp.json()
                    if "data" not in data or not data["data"]:
                        return {"success": False, "error": "没有返回图片数据"}

                    images = []
                    for item in data.get("data", []):
                        images.append({"b64_json": item.get("b64_json")})
                    return {"images": images, "success": True}
        except asyncio.TimeoutError:
            self.logger.error("GPT 文生图请求超时")
            return {"success": False, "error": "请求超时"}
        except Exception as e:
            self.logger.error(f"GPT text to image failed: {e}")
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
            self.logger.error("❌ YI_API_KEY 未配置")
            return {"success": False, "error": "YI_API_KEY 未配置"}

        # ✅ 检查模型是否存在
        if not self.is_image_model(model):
            supported = ", ".join(self.get_supported_models("image"))
            return {
                "success": False,
                "error": f"模型 '{model}' 不在 API易 图片模型支持列表中。支持的图片模型: {supported}"
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

        is_gpt = self.is_gpt_image_model(model)
        if is_gpt:
            return await self._image_to_image_gpt(source_image, prompt, model, count, aspect_ratio)
        else:
            return await self._image_to_image_gemini(source_image, prompt, model, aspect_ratio, image_size)

    async def _image_to_image_gemini(
            self,
            source_image: str,
            prompt: str,
            model: str,
            aspect_ratio: str,
            image_size: str
    ) -> Optional[Dict[str, Any]]:
        """Gemini 图生图"""
        try:
            # ✅ 处理路径：如果是 /data/input/ 开头的路径，转换为完整路径
            image_path = source_image
            if source_image.startswith('/data/input/'):
                filename = source_image.replace('/data/input/', '')
                image_path = str(settings.INPUT_DIR / filename)
                self.logger.info(f"📸 转换路径: {source_image} -> {image_path}")

            # ✅ 如果路径不存在，尝试其他方式
            if not Path(image_path).exists():
                # 尝试直接作为文件名在 input_dir 中查找
                if '/' in source_image or '\\' in source_image:
                    filename = Path(source_image).name
                    image_path = str(settings.INPUT_DIR / filename)
                    self.logger.info(f"📸 尝试从文件名查找: {image_path}")

                if not Path(image_path).exists():
                    self.logger.error(f"❌ 图片文件不存在: {image_path}")
                    return {"success": False, "error": f"图片文件不存在: {source_image}"}

            # ✅ 读取图片
            async with aiofiles.open(image_path, 'rb') as f:
                image_data = await f.read()
                image_b64 = base64.b64encode(image_data).decode()
            mime_type = self._detect_mime_type(image_path)

            self.logger.info(f"📸 读取图片成功，大小: {len(image_data)} bytes, mime: {mime_type}")

            url = f"https://api.apiyi.com/v1beta/models/{model}:generateContent"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            image_config = {"aspectRatio": aspect_ratio}
            if "pro" in model:
                image_config["imageSize"] = "4K" if image_size == "4K" else "2K"
            elif "lite" in model:
                image_config["imageSize"] = "1K"
            else:
                image_config["imageSize"] = image_size

            # ✅ 修复：图生图格式 - 图片在前，文本在后
            payload = {
                "contents": [{
                    "parts": [
                        {
                            "inlineData": {
                                "mimeType": mime_type,
                                "data": image_b64
                            }
                        },
                        {"text": prompt}
                    ]
                }],
                "generationConfig": {
                    "responseModalities": ["IMAGE"],
                    "imageConfig": image_config
                }
            }

            self.logger.info(f"📸 发送图生图请求: model={model}, prompt={prompt[:50]}...")
            self.logger.info(f"📸 图片数据长度: {len(image_b64)}")

            async with aiohttp.ClientSession() as session:
                async with session.post(
                        url,
                        headers=headers,
                        json=payload,
                        timeout=aiohttp.ClientTimeout(total=settings.IMAGE_TIMEOUT)
                ) as resp:
                    if resp.status != 200:
                        error_text = await resp.text()
                        self.logger.error(f"HTTP {resp.status}: {error_text[:200]}")
                        return {"success": False, "error": f"HTTP {resp.status}"}

                    data = await resp.json()
                    self.logger.info(f"📸 图生图响应: {json.dumps(data, ensure_ascii=False)[:500]}")

                    # 检查错误
                    if "error" in data:
                        return {"success": False, "error": f"API错误: {data['error']}"}

                    # 解析图片数据
                    if "candidates" in data and data["candidates"]:
                        candidate = data["candidates"][0]

                        if candidate.get("finishReason") == "SAFETY":
                            return {"success": False, "error": "内容被安全策略拦截"}

                        # ✅ 检查是否返回了图片
                        if "content" in candidate and "parts" in candidate["content"]:
                            parts = candidate["content"]["parts"]
                            for part in parts:
                                if "inlineData" in part:
                                    img_data = part["inlineData"].get("data")
                                    if img_data:
                                        self.logger.info(f"✅ 图生图图片数据获取成功，长度: {len(img_data)}")
                                        return {"image_data": img_data, "success": True}
                                elif "image" in part:
                                    img_data = part.get("image")
                                    if img_data:
                                        self.logger.info(f"✅ 图生图图片数据获取成功，长度: {len(img_data)}")
                                        return {"image_data": img_data, "success": True}

                    # 尝试其他可能的字段
                    if "output" in data and "choices" in data["output"]:
                        for choice in data["output"]["choices"]:
                            content = choice.get("message", {}).get("content", [])
                            for item in content:
                                if "image" in item:
                                    img_data = item["image"]
                                    if img_data:
                                        self.logger.info(f"✅ 从 output 获取图片数据")
                                        return {"image_data": img_data, "success": True}

                    self.logger.error(f"❌ 无法解析图生图数据: {data}")
                    return {"success": False, "error": "无法解析图片数据"}

        except FileNotFoundError as e:
            self.logger.error(f"❌ 图片文件不存在: {image_path if 'image_path' in locals() else source_image}")
            return {"success": False, "error": f"图片文件不存在: {source_image}"}
        except Exception as e:
            self.logger.error(f"Image to image failed: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return {"success": False, "error": str(e)}

    async def _image_to_image_gpt(
            self,
            source_image: str,
            prompt: str,
            model: str,
            count: int,
            aspect_ratio: str
    ) -> Optional[Dict[str, Any]]:
        """GPT-Image 图生图"""
        try:
            size_map = {
                "1:1": "1024x1024",
                "16:9": "2048x1152",
                "9:16": "1152x2048",
                "3:2": "1536x1024",
                "2:3": "1024x1536",
            }
            size = size_map.get(aspect_ratio, "1024x1024")

            # 读取图片
            if Path(source_image).exists():
                async with aiofiles.open(source_image, 'rb') as f:
                    image_data = await f.read()
            else:
                image_data = base64.b64decode(source_image)

            url = "https://api.apiyi.com/v1/images/edits"
            headers = {"Authorization": f"Bearer {self.api_key}"}

            form_data = aiohttp.FormData()
            form_data.add_field('model', model)
            form_data.add_field('prompt', prompt)
            form_data.add_field('size', size)
            form_data.add_field('quality', 'high')
            form_data.add_field('n', str(count))
            form_data.add_field('response_format', 'b64_json')
            form_data.add_field('image', image_data, filename='image.png', content_type='image/png')

            async with aiohttp.ClientSession() as session:
                async with session.post(
                        url,
                        headers=headers,
                        data=form_data,
                        timeout=aiohttp.ClientTimeout(total=settings.IMAGE_TIMEOUT)
                ) as resp:
                    if resp.status != 200:
                        error_text = await resp.text()
                        self.logger.error(f"HTTP {resp.status}: {error_text[:200]}")
                        return {"success": False, "error": f"HTTP {resp.status}"}

                    data = await resp.json()
                    if "data" not in data or not data["data"]:
                        return {"success": False, "error": "没有返回图片数据"}

                    images = []
                    for item in data.get("data", []):
                        images.append({"b64_json": item.get("b64_json")})
                    return {"images": images, "success": True}
        except Exception as e:
            self.logger.error(f"GPT image to image failed: {e}")
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
        """多图融合 - ✅ 添加模型验证"""
        if not self.api_key:
            self.logger.error("❌ YI_API_KEY 未配置")
            return {"success": False, "error": "YI_API_KEY 未配置"}

        # ✅ 检查模型是否存在
        if not self.is_image_model(model):
            supported = ", ".join(self.get_supported_models("image"))
            return {
                "success": False,
                "error": f"模型 '{model}' 不在 API易 图片模型支持列表中。支持的图片模型: {supported}"
            }

        # ✅ 检查模型是否支持图生图（多图融合需要图生图能力）
        if not self.supports_image_to_image(model):
            supported = ", ".join([
                m for m in self.get_supported_models("image")
                if self.supports_image_to_image(m)
            ])
            return {
                "success": False,
                "error": f"模型 '{model}' 不支持多图融合（需要图生图能力）。支持图生图的模型: {supported}"
            }

        is_gpt = self.is_gpt_image_model(model)
        if is_gpt:
            return await self._fuse_images_gpt(image_paths, fusion_prompt, model, aspect_ratio)
        else:
            return await self._fuse_images_gemini(image_paths, fusion_prompt, model, aspect_ratio, image_size)

    async def _fuse_images_gemini(
            self,
            image_paths: List[str],
            fusion_prompt: str,
            model: str,
            aspect_ratio: str,
            image_size: str
    ) -> Optional[Dict[str, Any]]:
        """Gemini 多图融合"""
        try:
            parts = [{"text": fusion_prompt}]

            for path in image_paths:
                if not Path(path).exists():
                    return {"success": False, "error": f"图片不存在: {path}"}

                async with aiofiles.open(path, 'rb') as f:
                    image_data = await f.read()
                    image_b64 = base64.b64encode(image_data).decode()
                    parts.append({
                        "inlineData": {
                            "mimeType": self._detect_mime_type(path),
                            "data": image_b64
                        }
                    })

            url = f"https://api.apiyi.com/v1beta/models/{model}:generateContent"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            image_config = {"aspectRatio": aspect_ratio}
            if "pro" in model:
                image_config["imageSize"] = "4K" if image_size == "4K" else "2K"
            elif "lite" in model:
                image_config["imageSize"] = "1K"
            else:
                image_config["imageSize"] = image_size

            payload = {
                "contents": [{"parts": parts}],
                "generationConfig": {
                    "responseModalities": ["IMAGE"],
                    "imageConfig": image_config
                }
            }

            timeout_seconds = 120 + len(image_paths) * 10

            async with aiohttp.ClientSession() as session:
                async with session.post(
                        url,
                        headers=headers,
                        json=payload,
                        timeout=aiohttp.ClientTimeout(total=timeout_seconds)
                ) as resp:
                    if resp.status != 200:
                        error_text = await resp.text()
                        self.logger.error(f"HTTP {resp.status}: {error_text[:200]}")
                        return {"success": False, "error": f"HTTP {resp.status}"}

                    data = await resp.json()

                    # 检查错误
                    if "error" in data:
                        return {"success": False, "error": f"API错误: {data['error']}"}

                    # 解析图片数据
                    if "candidates" in data and data["candidates"]:
                        candidate = data["candidates"][0]

                        if candidate.get("finishReason") == "SAFETY":
                            return {"success": False, "error": "内容被安全策略拦截"}

                        if "content" in candidate and "parts" in candidate["content"]:
                            parts_data = candidate["content"]["parts"]
                            for part in parts_data:
                                if "inlineData" in part:
                                    img_data = part["inlineData"].get("data")
                                    if img_data:
                                        self.logger.info(f"✅ 融合图片数据获取成功，长度: {len(img_data)}")
                                        return {"image_data": img_data, "success": True}
                                elif "image" in part:
                                    img_data = part["image"]
                                    if img_data:
                                        self.logger.info(f"✅ 融合图片数据获取成功，长度: {len(img_data)}")
                                        return {"image_data": img_data, "success": True}

                    # 尝试其他可能的字段
                    if "output" in data and "choices" in data["output"]:
                        for choice in data["output"]["choices"]:
                            content = choice.get("message", {}).get("content", [])
                            for item in content:
                                if "image" in item:
                                    img_data = item["image"]
                                    if img_data:
                                        return {"image_data": img_data, "success": True}

                    self.logger.error(f"❌ 无法解析融合数据")
                    return {"success": False, "error": "无法解析图片数据"}

        except Exception as e:
            self.logger.error(f"Fuse images failed: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return {"success": False, "error": str(e)}

    async def _fuse_images_gpt(
            self,
            image_paths: List[str],
            fusion_prompt: str,
            model: str,
            aspect_ratio: str
    ) -> Optional[Dict[str, Any]]:
        """GPT-Image 多图融合"""
        try:
            size_map = {
                "1:1": "1024x1024",
                "16:9": "2048x1152",
                "9:16": "1152x2048",
                "3:2": "1536x1024",
                "2:3": "1024x1536",
            }
            size = size_map.get(aspect_ratio, "1024x1024")

            form_data = aiohttp.FormData()
            form_data.add_field('model', model)
            form_data.add_field('prompt', fusion_prompt)
            form_data.add_field('size', size)
            form_data.add_field('quality', 'high')
            form_data.add_field('n', '1')
            form_data.add_field('response_format', 'b64_json')

            for i, path in enumerate(image_paths):
                if not Path(path).exists():
                    return {"success": False, "error": f"图片不存在: {path}"}

                async with aiofiles.open(path, 'rb') as f:
                    image_data = await f.read()
                field_name = f"image.{i}" if i > 0 else "image"
                form_data.add_field(
                    field_name,
                    image_data,
                    filename=Path(path).name,
                    content_type=self._detect_mime_type(path)
                )

            url = "https://api.apiyi.com/v1/images/edits"
            headers = {"Authorization": f"Bearer {self.api_key}"}

            timeout_seconds = 120 + len(image_paths) * 15

            async with aiohttp.ClientSession() as session:
                async with session.post(
                        url,
                        headers=headers,
                        data=form_data,
                        timeout=aiohttp.ClientTimeout(total=timeout_seconds)
                ) as resp:
                    if resp.status != 200:
                        error_text = await resp.text()
                        self.logger.error(f"HTTP {resp.status}: {error_text[:200]}")
                        return {"success": False, "error": f"HTTP {resp.status}"}

                    data = await resp.json()
                    if "data" not in data or not data["data"]:
                        return {"success": False, "error": "没有返回图片数据"}

                    images = []
                    for item in data.get("data", []):
                        images.append({"b64_json": item.get("b64_json")})
                    return {"images": images, "success": True}
        except Exception as e:
            self.logger.error(f"GPT fuse images failed: {e}")
            return {"success": False, "error": str(e)}


if __name__ == '__main__':
    y = YIClient()

    # print(asyncio.run(y.chat_completion([{'role':'system','content':'你是一个聊天助手'},{"role": "user", "content": "你好，请介绍一下自己"}])))
    print(asyncio.run(y.image_to_image(
        source_image='D:/AI_GEN/ai-gen-backend/data/input/14.jpg',
        prompt='帮我根据这张图片生成动漫的图片',
        model='gemini-3.1-flash-lite-image'
    )))
