"""OpenAI 兼容 API 客户端

支持真正的 SSE 流式输出，兼容多家国内厂商（智谱、月之暗面、百度、阿里等）
"""
import json
from typing import AsyncGenerator, Optional

import httpx

from app.config import get_settings
from app.core.constants import QWEN_HTTP_TIMEOUT
from app.utils.log_helper import get_logger

logger = get_logger("core.openai")

# 默认配置
DEFAULT_OPENAI_MODEL = "gpt-4o-mini"
DEFAULT_OPENAI_BASE_URL = "https://api.openai.com/v1"


async def openai_chat_stream(
    messages: list[dict[str, str]],
    model: Optional[str] = None,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
) -> AsyncGenerator[str, None]:
    """
    调用 OpenAI 兼容接口，真正的 SSE 流式返回结果。

    Args:
        messages: [{"role": "system|user|assistant", "content": "..."}]
        model: 模型名，如 gpt-4o-mini, glm-4, kimi-latest
        api_key: API Key，默认从 OPENAI_API_KEY 或 QWEN_API_KEY 读取
        base_url: API 基础 URL，默认从 OPENAI_BASE_URL 读取

    Yields:
        逐字/逐 token 流式返回的文本片段

    Raises:
        ValueError: API Key 未配置或调用失败
    """
    settings = get_settings()

    # 获取配置（支持环境变量）
    key = api_key or getattr(settings, "OPENAI_API_KEY", None) or getattr(settings, "QWEN_API_KEY", None) or ""
    url = base_url or getattr(settings, "OPENAI_BASE_URL", None) or DEFAULT_OPENAI_BASE_URL
    model_name = model or getattr(settings, "OPENAI_MODEL", None) or DEFAULT_OPENAI_MODEL

    if not key:
        raise ValueError("请配置 OPENAI_API_KEY 或 QWEN_API_KEY 环境变量")

    chat_url = f"{url.rstrip('/')}/chat/completions"

    payload = {
        "model": model_name,
        "messages": messages,
        "stream": True,  # 关键：启用流式
        "temperature": 0.7,
    }

    logger.info(f"Starting OpenAI stream: model={model_name}, url={chat_url}, messages={len(messages)}")

    async with httpx.AsyncClient(timeout=QWEN_HTTP_TIMEOUT) as client:
        async with client.stream(
            "POST",
            chat_url,
            headers={
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
            },
            json=payload,
        ) as resp:
            if resp.status_code != 200:
                error_text = await resp.aread()
                logger.error(f"OpenAI API error: {resp.status_code} {error_text}")
                raise ValueError(f"OpenAI API 调用失败: {resp.status_code}")

            chunk_count = 0
            async for line in resp.aiter_lines():
                line = line.strip()
                if not line:
                    continue

                # SSE 格式: data: {...}
                if not line.startswith("data:"):
                    continue

                data_str = line[5:].strip()
                if data_str == "[DONE]":
                    logger.info(f"Stream completed with [DONE], total chunks: {chunk_count}")
                    break

                try:
                    data = json.loads(data_str)
                except json.JSONDecodeError:
                    continue

                # 解析 OpenAI 流式格式
                choices = data.get("choices", [])
                if not choices:
                    continue

                delta = choices[0].get("delta", {})
                content = delta.get("content", "")

                if content:
                    chunk_count += 1
                    yield content

            logger.info(f"Stream finished, total chunks: {chunk_count}")


async def openai_chat(
    messages: list[dict[str, str]],
    model: Optional[str] = None,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
) -> str:
    """
    调用 OpenAI 兼容接口，非流式返回完整结果。
    """
    settings = get_settings()

    key = api_key or getattr(settings, "OPENAI_API_KEY", None) or getattr(settings, "QWEN_API_KEY", None) or ""
    url = base_url or getattr(settings, "OPENAI_BASE_URL", None) or DEFAULT_OPENAI_BASE_URL
    model_name = model or getattr(settings, "OPENAI_MODEL", None) or DEFAULT_OPENAI_MODEL

    if not key:
        raise ValueError("请配置 OPENAI_API_KEY 或 QWEN_API_KEY 环境变量")

    chat_url = f"{url.rstrip('/')}/chat/completions"

    payload = {
        "model": model_name,
        "messages": messages,
        "stream": False,
        "temperature": 0.7,
    }

    async with httpx.AsyncClient(timeout=QWEN_HTTP_TIMEOUT) as client:
        resp = await client.post(
            chat_url,
            headers={
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
            },
            json=payload,
        )

    if resp.status_code != 200:
        logger.error(f"OpenAI API error: {resp.status_code} {resp.text}")
        raise ValueError(f"OpenAI API 调用失败: {resp.status_code}")

    data = resp.json()
    choices = data.get("choices", [])
    if choices:
        return choices[0].get("message", {}).get("content", "")
    return ""
