"""Small clients for OpenAI-compatible chat APIs."""

from __future__ import annotations

from typing import Any, Iterable

from ._optional import require


def _messages(user_message: str, system_prompt: str | None) -> list[dict[str, str]]:
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": user_message})
    return messages


def ask_ai(
    user_message: str,
    *,
    api_key: str,
    model: str,
    base_url: str | None = None,
    system_prompt: str | None = None,
    **options: Any,
) -> str:
    """Make one chat call and close the client automatically."""
    with AIClient(api_key, model=model, base_url=base_url) as ai:
        return ai.simple_chat(user_message, system_prompt=system_prompt, **options)


async def ask_ai_async(
    user_message: str,
    *,
    api_key: str,
    model: str,
    base_url: str | None = None,
    system_prompt: str | None = None,
    **options: Any,
) -> str:
    """Async one-shot chat helper; the client is closed before returning."""
    async with AsyncAIClient(api_key, model=model, base_url=base_url) as ai:
        return await ai.simple_chat(user_message, system_prompt=system_prompt, **options)


class AIClient:
    """Synchronous chat helper; credentials and provider settings are passed in."""

    def __init__(
        self,
        api_key: str,
        *,
        model: str,
        base_url: str | None = None,
        timeout: float = 60,
        client: Any = None,
    ):
        if not api_key or not api_key.strip():
            raise ValueError("api_key is required")
        if not model or not model.strip():
            raise ValueError("model is required")
        self.model = model
        if client is None:
            sdk = require("openai", "ai")
            client = sdk.OpenAI(api_key=api_key, base_url=base_url, timeout=timeout)
        self._client = client

    def chat(self, messages: Iterable[dict[str, str]], *, model: str | None = None, **options: Any) -> str:
        response = self._client.chat.completions.create(
            model=model or self.model,
            messages=list(messages),
            **options,
        )
        content = response.choices[0].message.content
        if content is None:
            raise ValueError("The model returned no text content")
        return content

    def simple_chat(
        self,
        user_message: str,
        *,
        system_prompt: str | None = None,
        model: str | None = None,
        **options: Any,
    ) -> str:
        return self.chat(_messages(user_message, system_prompt), model=model, **options)

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "AIClient":
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()


class AsyncAIClient:
    """Asynchronous equivalent of :class:`AIClient`."""

    def __init__(
        self,
        api_key: str,
        *,
        model: str,
        base_url: str | None = None,
        timeout: float = 60,
        client: Any = None,
    ):
        if not api_key or not api_key.strip():
            raise ValueError("api_key is required")
        if not model or not model.strip():
            raise ValueError("model is required")
        self.model = model
        if client is None:
            sdk = require("openai", "ai")
            client = sdk.AsyncOpenAI(api_key=api_key, base_url=base_url, timeout=timeout)
        self._client = client

    async def chat(self, messages: Iterable[dict[str, str]], *, model: str | None = None, **options: Any) -> str:
        response = await self._client.chat.completions.create(
            model=model or self.model,
            messages=list(messages),
            **options,
        )
        content = response.choices[0].message.content
        if content is None:
            raise ValueError("The model returned no text content")
        return content

    async def simple_chat(
        self,
        user_message: str,
        *,
        system_prompt: str | None = None,
        model: str | None = None,
        **options: Any,
    ) -> str:
        return await self.chat(_messages(user_message, system_prompt), model=model, **options)

    async def aclose(self) -> None:
        await self._client.close()

    async def __aenter__(self) -> "AsyncAIClient":
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.aclose()
