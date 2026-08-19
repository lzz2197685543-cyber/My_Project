from openai import AsyncOpenAI
from config.config import settings


class DeepSeekService:
    def __init__(self):
        self.client = AsyncOpenAI(
            api_key=settings.DEEPSEEK_API_KEY,
            base_url=settings.DEEPSEEK_BASE_URL
        )

    async def chat(
            self,
            model: str,
            user_message: str,
            system_prompt: str = "你是一个乐于助人的助手",
            max_tokens: int = 1024,
            temperature: float = 0.7
    ):
        try:
            response = await self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
                max_tokens=max_tokens,
                temperature=temperature,
                stream=False
            )
            return {
                "success": True,
                "content": response.choices[0].message.content,
                "usage": response.usage.model_dump() if hasattr(response, 'usage') else None
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }


# 单例
deepseek_service = DeepSeekService()