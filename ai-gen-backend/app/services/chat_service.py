"""
聊天服务
"""
import json
from typing import Optional, List, Dict, Any, AsyncIterator

from app.services.ai_service import AIClientFactory
from app.utils.logger import get_logger
import asyncio

from app.utils.model_validator import ModelValidator

logger = get_logger("chat_service")


class ChatService:
    """聊天服务"""

    async def chat(
            self,
            messages: List[Dict[str, str]],
            model: str,
            provider: str = "yi",
            max_tokens: int = 1024,
            temperature: float = 0.7,
            stream: bool = False,
            api_key: Optional[str] = None
    ) -> Optional[str]:
        """
        执行聊天

        Args:
            messages: 对话消息列表
            model: 模型名称
            provider: 提供商
            max_tokens: 最大生成 token 数
            temperature: 温度参数
            stream: 是否流式输出
            api_key: API Key（可选）

        Returns:
            str: 生成的回复内容
        """
        try:
            # ✅ 添加验证
            validation = ModelValidator.validate_model(provider, model, "chat")
            if not validation["valid"]:
                return f"错误: {validation['error']}"
            # 获取客户端
            client = AIClientFactory.get_client(provider, api_key)

            # 调用聊天补全
            result = await client.chat_completion(
                messages=messages,
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                stream=stream
            )

            if result is None:
                logger.error(f"聊天失败: provider={provider}, model={model}")
                return None

            return result

        except Exception as e:
            logger.error(f"聊天服务异常: {e}")
            return None

    async def stream_chat(
            self,
            messages: List[Dict[str, str]],
            model: str,
            provider: str = "yi",
            max_tokens: int = 1024,
            temperature: float = 0.7,
            api_key: Optional[str] = None
    ) -> AsyncIterator[str]:
        """
        流式聊天（生成器）

        Args:
            messages: 对话消息列表
            model: 模型名称
            provider: 提供商
            max_tokens: 最大生成 token 数
            temperature: 温度参数
            api_key: API Key（可选）

        Yields:
            str: SSE 格式的流式数据
        """
        try:
            # ✅ 验证模型
            validation = ModelValidator.validate_model(provider, model, "chat")
            if not validation["valid"]:
                yield f"data: {json.dumps({'error': validation['error']})}\n\n"
                yield "data: [DONE]\n\n"
                return

            # 获取客户端
            client = AIClientFactory.get_client(provider, api_key)

            # ✅ 调用流式聊天（客户端内部处理流式）
            result = await client.chat_completion(
                messages=messages,
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                stream=True
            )

            # ✅ 如果结果为空，返回错误
            if not result:
                yield f"data: {json.dumps({'error': '没有收到回复'})}\n\n"
                yield "data: [DONE]\n\n"
                return

            # ✅ 如果结果包含错误信息
            if result.startswith("错误") or result.startswith("API 请求失败"):
                yield f"data: {json.dumps({'error': result})}\n\n"
                yield "data: [DONE]\n\n"
                return

            # ✅ 将完整内容分块输出（模拟流式）
            words = result.split()
            chunk_size = 2

            for i in range(0, len(words), chunk_size):
                chunk = " ".join(words[i:i + chunk_size])
                if chunk:
                    data = {
                        "id": f"chatcmpl-{id(self)}",
                        "choices": [{
                            "delta": {"content": chunk},
                            "index": 0
                        }],
                        "created": int(asyncio.get_event_loop().time()),
                        "model": model
                    }
                    yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
                    await asyncio.sleep(0.03)

            # ✅ 发送完成标记
            yield "data: [DONE]\n\n"

        except Exception as e:
            logger.error(f"流式聊天异常: {e}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
            yield "data: [DONE]\n\n"

    async def simple_chat(
            self,
            user_message: str,
            system_prompt: str = "你是一个乐于助人的助手",
            model: str = "deepseek-chat",
            provider: str = "yi",
            api_key: Optional[str] = None
    ) -> Optional[str]:
        """
        简单聊天（只需传入用户消息）

        Args:
            user_message: 用户消息
            system_prompt: 系统提示词
            model: 模型名称
            provider: 提供商
            api_key: API Key（可选）

        Returns:
            str: 回复内容
        """
        # ✅ 添加验证
        validation = ModelValidator.validate_model(provider, model, "chat")
        if not validation["valid"]:
            return f"错误: {validation['error']}"
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]
        return await self.chat(
            messages=messages,
            model=model,
            provider=provider,
            api_key=api_key
        )

# if __name__ == '__main__':
#     c=ChatService()
#     print(asyncio.run(c.simple_chat(user_message='agent开发需要学习什么内容?',provider='bailian',model='qwen-plus')))