"""
图片生成服务
"""
import base64
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any

import aiofiles

from app.services.ai_service import AIClientFactory
from app.utils.model_validator import ModelValidator
from config.settings import settings
from app.utils.logger import get_logger

logger = get_logger("image_service")


class ImageService:
    """图片生成服务"""

    def __init__(self):
        self.output_dir = settings.OUTPUT_DIR

    # ==================== 文生图 ====================

    async def text_to_image(
            self,
            prompt: str,
            model: str,
            provider: str = "yi",
            count: int = 1,
            aspect_ratio: str = "1:1",
            image_size: str = "1K",
            optimize: bool = True,
            prompt_extend: bool = False,
            api_key: Optional[str] = None,
            save_to_file: bool = True
    ) -> Dict[str, Any]:
        """
        文生图

        Args:
            prompt: 提示词
            model: 模型名称
            provider: 提供商
            count: 生成数量
            aspect_ratio: 宽高比
            image_size: 图片尺寸
            optimize: 是否优化提示词
            prompt_extend: 是否启用智能改写（百炼）
            api_key: API Key
            save_to_file: 是否保存到文件

        Returns:
            Dict: 生成结果
        """
        # ✅ 验证模型是否被支持
        validation = ModelValidator.validate_model(provider, model, "image")
        if not validation["valid"]:
            return {
                "success": False,
                "error": validation["error"],
                "used_prompt": prompt,
                "original_prompt": prompt,
                "images": [],
                "summary": {
                    "total": count,
                    "successful": 0,
                    "failed": count
                }
            }

        # 优化提示词
        used_prompt = prompt
        if optimize:
            used_prompt = await self._optimize_prompt(
                prompt=prompt,
                provider=provider,
                api_key=api_key
            )

        # 获取客户端
        client = AIClientFactory.get_client(provider, api_key)

        # 调用文生图 API
        result = await client.text_to_image(
            prompt=used_prompt,
            model=model,
            count=count,
            aspect_ratio=aspect_ratio,
            image_size=image_size,
            prompt_extend=prompt_extend
        )

        if not result or not result.get("success"):
            return {
                "success": False,
                "error": result.get("error", "生成失败"),
                "used_prompt": used_prompt,
                "original_prompt": prompt,
                "images": [],
                "summary": {
                    "total": count,
                    "successful": 0,
                    "failed": count
                }
            }

        # 处理结果
        images = []
        output_dir = None

        if save_to_file:
            # 创建输出目录
            output_dir = self.output_dir / "text_to_image" / datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"📁 输出目录: {output_dir}")

            # 检查是否有 image_data（Gemini 返回格式）
            if "image_data" in result and result.get("image_data"):
                filename = f"generated_01.png"
                filepath = output_dir / filename
                try:
                    async with aiofiles.open(filepath, 'wb') as f:
                        await f.write(base64.b64decode(result["image_data"]))
                    images.append({
                        "filename": filename,
                        "path": str(filepath),
                        "url": f"/output/text_to_image/{output_dir.name}/{filename}"
                    })
                    logger.info(f"✅ 图片已保存: {filepath}")
                except Exception as e:
                    logger.error(f"保存图片失败: {e}")

            # 处理 images 列表（GPT-Image 返回格式）
            for idx, img_data in enumerate(result.get("images", [])):
                # 如果已经有图片（来自 image_data），索引从 2 开始
                filename = f"generated_{idx + 2:02d}.png" if images else f"generated_{idx + 1:02d}.png"
                filepath = output_dir / filename

                if "b64_json" in img_data:
                    try:
                        async with aiofiles.open(filepath, 'wb') as f:
                            await f.write(base64.b64decode(img_data["b64_json"]))
                        images.append({
                            "filename": filename,
                            "path": str(filepath),
                            "url": f"/output/text_to_image/{output_dir.name}/{filename}"
                        })
                        logger.info(f"✅ 图片已保存: {filepath}")
                    except Exception as e:
                        logger.error(f"保存图片失败: {e}")
                        images.append(img_data)
                elif "url" in img_data:
                    import aiohttp
                    try:
                        async with aiohttp.ClientSession() as session:
                            async with session.get(img_data["url"]) as resp:
                                if resp.status == 200:
                                    image_bytes = await resp.read()
                                    async with aiofiles.open(filepath, 'wb') as f:
                                        await f.write(image_bytes)
                                    images.append({
                                        "filename": filename,
                                        "path": str(filepath),
                                        "url": f"/output/text_to_image/{output_dir.name}/{filename}"
                                    })
                                    logger.info(f"✅ 图片已下载: {filepath}")
                                else:
                                    logger.error(f"下载图片失败: HTTP {resp.status}")
                                    images.append({"url": img_data["url"], "filename": filename})
                    except Exception as e:
                        logger.error(f"下载图片失败: {e}")
                        images.append({"url": img_data["url"], "filename": filename})
                else:
                    # 其他格式，直接添加
                    images.append(img_data)
        else:
            # 不保存到文件，直接返回原始数据
            if "image_data" in result and result.get("image_data"):
                images.append({"b64_json": result["image_data"]})
            # 添加 images 列表中的数据
            images.extend(result.get("images", []))

        # 检查是否成功生成了图片
        if not images:
            return {
                "success": False,
                "error": "没有生成任何图片",
                "used_prompt": used_prompt,
                "original_prompt": prompt,
                "images": [],
                "summary": {
                    "total": count,
                    "successful": 0,
                    "failed": count
                }
            }

        # 返回成功结果
        return {
            "success": True,
            "images": images,
            "used_prompt": used_prompt,
            "original_prompt": prompt,
            "summary": {
                "total": count,
                "successful": len(images),
                "failed": count - len(images),
                "output_dir": str(output_dir) if save_to_file and output_dir else None
            }
        }

    # ==================== 图生图 ====================

    async def image_to_image(
            self,
            source_image: str,
            prompt: str,
            model: str,
            provider: str = "yi",
            count: int = 1,
            aspect_ratio: str = "1:1",
            image_size: str = "1K",
            optimize: bool = True,
            prompt_extend: bool = False,
            api_key: Optional[str] = None,
            save_to_file: bool = True
    ) -> Dict[str, Any]:
        """
        图生图

        Args:
            source_image: 源图片路径或 base64
            prompt: 提示词
            model: 模型名称
            provider: 提供商
            count: 生成数量
            aspect_ratio: 宽高比
            image_size: 图片尺寸
            optimize: 是否优化提示词
            prompt_extend: 是否启用智能改写（百炼）
            api_key: API Key
            save_to_file: 是否保存到文件

        Returns:
            Dict: 生成结果
        """
        # ✅ 验证模型是否被支持
        validation = ModelValidator.validate_model(provider, model, "image")
        if not validation["valid"]:
            return {
                "success": False,
                "error": validation["error"],
                "used_prompt": prompt,
                "original_prompt": prompt,
                "source_image": source_image,
                "images": [],
                "summary": {
                    "total": count,
                    "successful": 0,
                    "failed": count
                }
            }

        # 验证源图片
        if isinstance(source_image, str) and not source_image.startswith("data:") and not Path(source_image).exists():
            # 如果不是 base64 且文件不存在
            if not source_image.startswith("/") and len(source_image) < 100:
                return {
                    "success": False,
                    "error": f"图片不存在: {source_image}",
                    "images": [],
                    "summary": {
                        "total": count,
                        "successful": 0,
                        "failed": count
                    }
                }

        # 优化提示词
        used_prompt = prompt
        if optimize:
            used_prompt = await self._optimize_prompt(
                prompt=prompt,
                provider=provider,
                api_key=api_key
            )

        # 获取客户端
        client = AIClientFactory.get_client(provider, api_key)

        # 调用图生图 API
        result = await client.image_to_image(
            source_image=source_image,
            prompt=used_prompt,
            model=model,
            count=count,
            aspect_ratio=aspect_ratio,
            image_size=image_size,
            prompt_extend=prompt_extend
        )

        if not result or not result.get("success"):
            return {
                "success": False,
                "error": result.get("error", "生成失败"),
                "used_prompt": used_prompt,
                "original_prompt": prompt,
                "source_image": source_image,
                "images": [],
                "summary": {
                    "total": count,
                    "successful": 0,
                    "failed": count
                }
            }

        # 处理结果
        images = []
        output_dir = None

        if save_to_file:
            # 创建输出目录
            output_dir = self.output_dir / "image_to_image" / datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"📁 输出目录: {output_dir}")

            # 检查是否有 image_data（Gemini 返回格式）
            if "image_data" in result and result.get("image_data"):
                filename = f"generated_01.png"
                filepath = output_dir / filename
                try:
                    async with aiofiles.open(filepath, 'wb') as f:
                        await f.write(base64.b64decode(result["image_data"]))
                    images.append({
                        "filename": filename,
                        "path": str(filepath),
                        "url": f"/output/image_to_image/{output_dir.name}/{filename}"
                    })
                    logger.info(f"✅ 图片已保存: {filepath}")
                except Exception as e:
                    logger.error(f"保存图片失败: {e}")

            # 处理 images 列表（GPT-Image 返回格式）
            for idx, img_data in enumerate(result.get("images", [])):
                # 如果已经有图片（来自 image_data），索引从 2 开始
                filename = f"generated_{idx + 2:02d}.png" if images else f"generated_{idx + 1:02d}.png"
                filepath = output_dir / filename

                if "b64_json" in img_data:
                    try:
                        async with aiofiles.open(filepath, 'wb') as f:
                            await f.write(base64.b64decode(img_data["b64_json"]))
                        images.append({
                            "filename": filename,
                            "path": str(filepath),
                            "url": f"/output/image_to_image/{output_dir.name}/{filename}"
                        })
                        logger.info(f"✅ 图片已保存: {filepath}")
                    except Exception as e:
                        logger.error(f"保存图片失败: {e}")
                        images.append(img_data)
                elif "url" in img_data:
                    import aiohttp
                    try:
                        async with aiohttp.ClientSession() as session:
                            async with session.get(img_data["url"]) as resp:
                                if resp.status == 200:
                                    image_bytes = await resp.read()
                                    async with aiofiles.open(filepath, 'wb') as f:
                                        await f.write(image_bytes)
                                    images.append({
                                        "filename": filename,
                                        "path": str(filepath),
                                        "url": f"/output/image_to_image/{output_dir.name}/{filename}"
                                    })
                                    logger.info(f"✅ 图片已下载: {filepath}")
                                else:
                                    logger.error(f"下载图片失败: HTTP {resp.status}")
                                    images.append({"url": img_data["url"], "filename": filename})
                    except Exception as e:
                        logger.error(f"下载图片失败: {e}")
                        images.append({"url": img_data["url"], "filename": filename})
                else:
                    # 其他格式，直接添加
                    images.append(img_data)
        else:
            # 不保存到文件，直接返回原始数据
            if "image_data" in result and result.get("image_data"):
                images.append({"b64_json": result["image_data"]})
            # 添加 images 列表中的数据
            images.extend(result.get("images", []))

        # 检查是否成功生成了图片
        if not images:
            return {
                "success": False,
                "error": "没有生成任何图片",
                "used_prompt": used_prompt,
                "original_prompt": prompt,
                "source_image": source_image,
                "images": [],
                "summary": {
                    "total": count,
                    "successful": 0,
                    "failed": count
                }
            }

        # 返回成功结果
        return {
            "success": True,
            "images": images,
            "used_prompt": used_prompt,
            "original_prompt": prompt,
            "source_image": source_image,
            "summary": {
                "total": count,
                "successful": len(images),
                "failed": count - len(images),
                "output_dir": str(output_dir) if save_to_file and output_dir else None
            }
        }

    # ==================== 多图融合 ====================

    async def fuse_images(
            self,
            image_paths: List[str],
            fusion_prompt: str,
            model: str,
            provider: str = "yi",
            aspect_ratio: str = "1:1",
            image_size: str = "1K",
            optimize: bool = True,
            api_key: Optional[str] = None,
            save_to_file: bool = True
    ) -> Dict[str, Any]:
        """
        多图融合

        Args:
            image_paths: 图片路径列表
            fusion_prompt: 融合提示词
            model: 模型名称
            provider: 提供商
            aspect_ratio: 宽高比
            image_size: 图片尺寸
            optimize: 是否优化提示词
            api_key: API Key
            save_to_file: 是否保存到文件

        Returns:
            Dict: 融合结果
        """
        # ✅ 验证模型是否被支持
        validation = ModelValidator.validate_model(provider, model, "image")
        if not validation["valid"]:
            return {
                "success": False,
                "error": validation["error"],
                "used_prompt": fusion_prompt,
                "original_prompt": fusion_prompt,
                "images": [],
                "summary": {
                    "total": len(image_paths),
                    "successful": 0,
                    "failed": len(image_paths)
                }
            }

        # 验证图片路径
        for path in image_paths:
            if not Path(path).exists():
                return {
                    "success": False,
                    "error": f"图片不存在: {path}",
                    "images": [],
                    "summary": {
                        "total": len(image_paths),
                        "successful": 0,
                        "failed": len(image_paths)
                    }
                }

        # 优化提示词
        used_prompt = fusion_prompt
        if optimize:
            used_prompt = await self._optimize_prompt(
                prompt=fusion_prompt,
                provider=provider,
                api_key=api_key
            )

        # 获取客户端
        client = AIClientFactory.get_client(provider, api_key)

        # 调用多图融合 API
        result = await client.fuse_images(
            image_paths=image_paths,
            fusion_prompt=used_prompt,
            model=model,
            aspect_ratio=aspect_ratio,
            image_size=image_size
        )

        if not result or not result.get("success"):
            return {
                "success": False,
                "error": result.get("error", "融合失败"),
                "used_prompt": used_prompt,
                "original_prompt": fusion_prompt,
                "images": [],
                "summary": {
                    "total": len(image_paths),
                    "successful": 0,
                    "failed": len(image_paths)
                }
            }

        # 处理结果
        images = []
        output_dir = None

        if save_to_file:
            output_dir = self.output_dir / "fused" / datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"📁 输出目录: {output_dir}")

            # 检查是否有 image_data（Gemini 返回格式）
            if "image_data" in result and result.get("image_data"):
                filename = f"fused_01.png"
                filepath = output_dir / filename
                try:
                    async with aiofiles.open(filepath, 'wb') as f:
                        await f.write(base64.b64decode(result["image_data"]))
                    images.append({
                        "filename": filename,
                        "path": str(filepath),
                        "url": f"/output/fused/{output_dir.name}/{filename}"
                    })
                    logger.info(f"✅ 图片已保存: {filepath}")
                except Exception as e:
                    logger.error(f"保存图片失败: {e}")

            # 处理 images 列表（GPT-Image 返回格式）
            for idx, img_data in enumerate(result.get("images", [])):
                filename = f"fused_{idx + 2:02d}.png" if images else f"fused_{idx + 1:02d}.png"
                filepath = output_dir / filename

                if "b64_json" in img_data:
                    try:
                        async with aiofiles.open(filepath, 'wb') as f:
                            await f.write(base64.b64decode(img_data["b64_json"]))
                        images.append({
                            "filename": filename,
                            "path": str(filepath),
                            "url": f"/output/fused/{output_dir.name}/{filename}"
                        })
                        logger.info(f"✅ 图片已保存: {filepath}")
                    except Exception as e:
                        logger.error(f"保存图片失败: {e}")
                        images.append(img_data)
                elif "url" in img_data:
                    import aiohttp
                    try:
                        async with aiohttp.ClientSession() as session:
                            async with session.get(img_data["url"]) as resp:
                                if resp.status == 200:
                                    image_bytes = await resp.read()
                                    async with aiofiles.open(filepath, 'wb') as f:
                                        await f.write(image_bytes)
                                    images.append({
                                        "filename": filename,
                                        "path": str(filepath),
                                        "url": f"/output/fused/{output_dir.name}/{filename}"
                                    })
                                    logger.info(f"✅ 图片已下载: {filepath}")
                                else:
                                    logger.error(f"下载图片失败: HTTP {resp.status}")
                                    images.append({"url": img_data["url"], "filename": filename})
                    except Exception as e:
                        logger.error(f"下载图片失败: {e}")
                        images.append({"url": img_data["url"], "filename": filename})
                else:
                    images.append(img_data)
        else:
            # 不保存到文件
            if "image_data" in result and result.get("image_data"):
                images.append({"b64_json": result["image_data"]})
            images.extend(result.get("images", []))

        if not images:
            return {
                "success": False,
                "error": "没有生成任何图片",
                "used_prompt": used_prompt,
                "original_prompt": fusion_prompt,
                "images": [],
                "summary": {
                    "total": len(image_paths),
                    "successful": 0,
                    "failed": len(image_paths)
                }
            }

        return {
            "success": True,
            "images": images,
            "used_prompt": used_prompt,
            "original_prompt": fusion_prompt,
            "summary": {
                "total": len(image_paths),
                "successful": len(images),
                "failed": len(image_paths) - len(images),
                "output_dir": str(output_dir) if save_to_file and output_dir else None
            }
        }

    # ==================== 辅助方法 ====================

    async def _optimize_prompt(
            self,
            prompt: str,
            provider: str,
            api_key: Optional[str] = None
    ) -> str:
        """
        优化提示词

        Args:
            prompt: 原始提示词
            provider: 提供商
            api_key: API Key

        Returns:
            str: 优化后的提示词
        """
        system_prompt = """你是专业的图像生成提示词优化专家。

        将用户输入的简单提示词，优化为更详细、更专业、更具表现力的图像生成提示词。

        **优化策略（根据提示词内容自适应）：**
        1. **主体强化**：明确核心对象及其关键特征
        2. **环境构建**：补充合适的背景或空间设定（如适用）
        3. **风格确立**：匹配并强化艺术风格（写实/插画/动漫/3D等）
        4. **视觉细节**：添加色彩、材质、光影、构图等描述
        5. **情绪氛围**：增强氛围感和叙事性

        **重要约束：**
        - 完全保留用户的核心意图
        - 不添加与主题无关的元素
        - 语言与原始提示词保持一致
        - 仅输出优化后的提示词，无解释、无前缀

      """

        try:
            # 获取聊天客户端
            client = AIClientFactory.get_client(provider, api_key)

            # 选择聊天模型
            if provider == "yi":
                chat_model = "deepseek-chat"
            elif provider == "bailian":
                chat_model = "qwen3.8-max"
            else:
                chat_model = "deepseek-chat"

            # 检查模型是否支持聊天
            validation = ModelValidator.validate_model(provider, chat_model, "chat")
            if not validation["valid"]:
                logger.warning(f"⚠️ 聊天模型 {chat_model} 不被 {provider} 支持，跳过优化")
                return prompt

            result = await client.chat_completion(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"请优化以下提示词：\n{prompt}"}
                ],
                model=chat_model,
                max_tokens=500,
                temperature=0.7
            )

            if result and not result.startswith("错误") and not result.startswith("API 请求失败"):
                logger.info(f"✅ 提示词优化完成: {prompt[:30]}... -> {result[:50]}...")
                return result.strip()
            else:
                logger.warning(f"⚠️ 提示词优化失败，使用原始提示词")
                return prompt

        except Exception as e:
            logger.warning(f"⚠️ 提示词优化异常: {e}，使用原始提示词")
            return prompt


if __name__ == '__main__':
    i = ImageService()

    print("=" * 70)
    print("🧪 图片服务测试")
    print("=" * 70)

    # 测试文生图 - 百炼
    # print("\n📸 测试百炼文生图:")
    print(asyncio.run(i.text_to_image(
        prompt='帮我生成一张小猫戴着头盔骑着公路车在海边的自拍视角的图片',
        model='z-image-turbo',
        provider='bailian'
    )))

    # 测试图生图 - API易（正确用法）
    # print("\n📸 测试 API易 图生图:")
    # print(asyncio.run(i.image_to_image(
    #     source_image='D:/AI_GEN/ai-gen-backend/data/input/14.jpg',
    #     prompt='帮我根据这张图片生成动漫的图片',
    #     model='gemini-3.1-flash-lite-image',
    #     provider='yi'
    # )))

    # 测试图生图 - 百炼（正确用法）
    # print("\n📸 测试百炼图生图:")
    # print(asyncio.run(i.image_to_image(
    #     source_image='D:/AI_GEN/ai-gen-backend/data/input/14.jpg',
    #     prompt='帮我根据这张图片生成动漫的图片',
    #     model='wan2.7-image-pro',
    #     provider='bailian'
    # )))

    # ❌ 测试不支持的模型组合 - 会被提前拦截
    print("\n❌ 测试不支持的模型组合（应该返回错误）:")
    result = asyncio.run(i.image_to_image(
        source_image='D:/AI_GEN/ai-gen-backend/data/input/14.jpg',
        prompt='帮我根据这张图片生成动漫的图片',
        model='gemini-3.1-flash-lite-image',  # ❌ 百炼不支持 Gemini
        provider='bailian'
    ))
    print(f"结果: success={result['success']}")
    if not result['success']:
        print(f"错误: {result['error']}")

    # ✅ 测试正确的模型组合
    # print("\n✅ 测试正确的模型组合:")
    # result = asyncio.run(i.image_to_image(
    #     source_image='D:/AI_GEN/ai-gen-backend/data/input/14.jpg',
    #     prompt='帮我根据这张图片生成动漫的图片',
    #     model='gemini-3.1-flash-lite-image',  # ✅ API易 支持 Gemini
    #     provider='yi'
    # ))
    # print(f"结果: success={result['success']}")
    # if not result['success']:
    #     print(f"错误: {result['error']}")