"""Unified LLM Client

使用 openai SDK（OpenAI 兼容格式），支持通过环境变量配置 endpoint、API key、model。
所有非实时音视频、非 TTS 的 LLM 调用应通过此客户端。

Fallback 链:
  API Key: LLM_API_KEY -> DASHSCOPE_API_KEY -> QWEN_API_KEY -> OPENAI_API_KEY
  Base URL: LLM_BASE_URL -> DASHSCOPE_BASE_URL -> OPENAI_BASE_URL -> https://api.openai.com/v1
  Model: LLM_MODEL -> OPENAI_MODEL -> gpt-4o-mini
"""
import json
import os
from typing import AsyncGenerator, Optional

from openai import AsyncOpenAI

from app.config import get_settings
from app.utils.log_helper import get_logger

logger = get_logger("core.llm")

DEFAULT_LLM_MODEL = "gpt-4o-mini"
DEFAULT_LLM_BASE_URL = "https://api.openai.com/v1"


def _resolve_api_key(settings) -> str:
    """按优先级解析 API Key"""
    return (
        settings.LLM_API_KEY
        or settings.DASHSCOPE_API_KEY
        or settings.QWEN_API_KEY
        or settings.OPENAI_API_KEY
        or os.getenv("LLM_API_KEY", "")
        or os.getenv("DASHSCOPE_API_KEY", "")
        or os.getenv("QWEN_API_KEY", "")
        or os.getenv("OPENAI_API_KEY", "")
    )


def _resolve_base_url(settings) -> str:
    """按优先级解析 Base URL"""
    return (
        settings.LLM_BASE_URL
        or settings.DASHSCOPE_BASE_URL
        or settings.OPENAI_BASE_URL
        or DEFAULT_LLM_BASE_URL
    )


def _resolve_model(settings, override: Optional[str] = None) -> str:
    """按优先级解析 Model"""
    return override or settings.LLM_MODEL or settings.OPENAI_MODEL or DEFAULT_LLM_MODEL


class UnifiedLLMClient:
    """统一 LLM 客户端，使用 OpenAI 兼容 API"""

    def __init__(self):
        settings = get_settings()
        self.api_key = _resolve_api_key(settings)
        self.base_url = _resolve_base_url(settings)
        self.model = _resolve_model(settings)
        self.temperature = settings.LLM_TEMPERATURE
        self.max_tokens = settings.LLM_MAX_TOKENS

        if not self.api_key:
            logger.warning("No LLM API key configured. LLM calls will fail.")

        self._client: Optional[AsyncOpenAI] = None

    @property
    def client(self) -> AsyncOpenAI:
        """Lazy-init AsyncOpenAI client"""
        if self._client is None:
            self._client = AsyncOpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
            )
        return self._client

    def is_configured(self) -> bool:
        """检查是否已配置 API key"""
        return bool(self.api_key)

    async def chat(
        self,
        messages: list[dict[str, str]],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stream: bool = False,
    ) -> str:
        """非流式对话，返回完整文本"""
        if not self.api_key:
            raise ValueError(
                "No LLM API key configured. Set LLM_API_KEY or one of the fallback keys."
            )

        model_name = model or self.model
        temp = temperature if temperature is not None else self.temperature
        max_tok = max_tokens if max_tokens is not None else self.max_tokens

        logger.info(f"LLM chat: model={model_name}, messages={len(messages)}")

        response = await self.client.chat.completions.create(
            model=model_name,
            messages=messages,  # type: ignore[arg-type]
            temperature=temp,
            max_tokens=max_tok,
            stream=False,
        )

        content = response.choices[0].message.content or ""
        return content

    async def chat_stream(
        self,
        messages: list[dict[str, str]],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> AsyncGenerator[str, None]:
        """流式对话，逐 token 返回"""
        if not self.api_key:
            raise ValueError("No LLM API key configured.")

        model_name = model or self.model
        temp = temperature if temperature is not None else self.temperature
        max_tok = max_tokens if max_tokens is not None else self.max_tokens

        logger.info(f"LLM chat stream: model={model_name}, messages={len(messages)}")

        response = await self.client.chat.completions.create(
            model=model_name,
            messages=messages,  # type: ignore[arg-type]
            temperature=temp,
            max_tokens=max_tok,
            stream=True,
        )

        async for chunk in response:
            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta
            if delta.content:
                yield delta.content

    async def chat_json(
        self,
        messages: list[dict[str, str]],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> dict:
        """对话并解析 JSON 回复（自动提取 ```json 代码块）"""
        content = await self.chat(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=False,
        )
        content = content.strip()

        # 提取 ```json ... ``` 中的内容
        if "```json" in content:
            start = content.find("```json") + 7
            end = content.find("```", start)
            if end > start:
                content = content[start:end].strip()

        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            logger.warning(f"LLM JSON parse failed: {e}, raw: {content[:200]}")
            return {"raw": content}


# Singleton instance
_llm_client: Optional[UnifiedLLMClient] = None


def get_llm_client() -> UnifiedLLMClient:
    """获取单例 UnifiedLLMClient"""
    global _llm_client
    if _llm_client is None:
        _llm_client = UnifiedLLMClient()
    return _llm_client


# 模块级快捷函数
async def llm_chat(
    messages: list[dict[str, str]],
    model: Optional[str] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
) -> str:
    """非流式对话快捷函数"""
    return await get_llm_client().chat(
        messages=messages, model=model, temperature=temperature, max_tokens=max_tokens
    )


async def llm_chat_stream(
    messages: list[dict[str, str]],
    model: Optional[str] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
) -> AsyncGenerator[str, None]:
    """流式对话快捷函数"""
    async for chunk in get_llm_client().chat_stream(
        messages=messages, model=model, temperature=temperature, max_tokens=max_tokens
    ):
        yield chunk


async def llm_chat_json(
    messages: list[dict[str, str]],
    model: Optional[str] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
) -> dict:
    """JSON 对话快捷函数"""
    return await get_llm_client().chat_json(
        messages=messages, model=model, temperature=temperature, max_tokens=max_tokens
    )
