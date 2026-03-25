"""Qwen 通义千问 LLM 客户端 (DashScope API)

替代讯飞星火，用于 RAG 推荐、回答评估等 LLM 场景。
"""
import json
from typing import Any, AsyncGenerator

import httpx

from app.config import get_settings
from app.core.constants import QWEN_DEFAULT_MODEL, QWEN_HTTP_TIMEOUT
from app.utils.log_helper import get_logger

logger = get_logger("core.qwen")

# DashScope OpenAI 兼容模式（支持真正的 SSE 流式）
DASHSCOPE_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
GENERATION_URL = f"{DASHSCOPE_BASE_URL}/chat/completions"


async def qwen_chat(
    messages: list[dict[str, str]],
    model: str = QWEN_DEFAULT_MODEL,
    api_key: str | None = None,
) -> str:
    """
    调用 Qwen 对话接口（OpenAI 兼容模式）。

    Args:
        messages: [{"role": "system|user|assistant", "content": "..."}]
        model: 模型名，如 qwen-plus, qwen-turbo
        api_key: API Key，默认从 QWEN_API_KEY 读取

    Returns:
        助手回复文本

    Raises:
        ValueError: API Key 未配置或调用失败
    """
    settings = get_settings()
    key = api_key or getattr(settings, "QWEN_API_KEY", None) or ""
    if not key:
        raise ValueError("请配置 QWEN_API_KEY 环境变量")

    # OpenAI 兼容格式的请求体
    payload = {
        "model": model,
        "messages": messages,
        "stream": False,
        "temperature": 0.7,
    }

    async with httpx.AsyncClient(timeout=QWEN_HTTP_TIMEOUT) as client:
        resp = await client.post(
            GENERATION_URL,
            headers={
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
            },
            json=payload,
        )

    if resp.status_code != 200:
        logger.error(f"Qwen API error: {resp.status_code} {resp.text}")
        raise ValueError(f"Qwen API 调用失败: {resp.status_code}")

    data = resp.json()
    choices = data.get("choices", [])
    if choices:
        return choices[0].get("message", {}).get("content", "")
    return ""


async def qwen_chat_json(
    messages: list[dict[str, str]],
    model: str = QWEN_DEFAULT_MODEL,
) -> dict[str, Any]:
    """
    调用 Qwen 并解析 JSON 回复（用于 RAG 等结构化输出）。
    若回复含 ```json ... ``` 代码块，则提取并解析。
    """
    content = await qwen_chat(messages, model)
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
        logger.warning(f"Qwen JSON parse failed: {e}, raw: {content[:200]}")
        return {"raw": content}


async def qwen_chat_stream(
    messages: list[dict[str, str]],
    model: str = QWEN_DEFAULT_MODEL,
    api_key: str | None = None,
) -> AsyncGenerator[str, None]:
    """
    调用 Qwen 对话接口（OpenAI 兼容模式），真正的 SSE 流式返回结果。

    Args:
        messages: [{"role": "system|user|assistant", "content": "..."}]
        model: 模型名，如 qwen-plus, qwen-turbo
        api_key: API Key，默认从 QWEN_API_KEY 读取

    Yields:
        逐 token 流式返回的文本片段

    Raises:
        ValueError: API Key 未配置或调用失败
    """
    settings = get_settings()
    key = api_key or getattr(settings, "QWEN_API_KEY", None) or ""
    if not key:
        raise ValueError("请配置 QWEN_API_KEY 环境变量")

    # OpenAI 兼容格式的请求体
    payload = {
        "model": model,
        "messages": messages,
        "stream": True,  # 启用 SSE 流式
        "temperature": 0.7,
    }

    logger.info(f"Starting Qwen OpenAI-compatible stream: model={model}")

    async with httpx.AsyncClient(timeout=QWEN_HTTP_TIMEOUT) as client:
        async with client.stream(
            "POST",
            GENERATION_URL,
            headers={
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
            },
            json=payload,
        ) as resp:
            if resp.status_code != 200:
                error_text = await resp.aread()
                logger.error(f"Qwen API error: {resp.status_code} {error_text}")
                raise ValueError(f"Qwen API 调用失败: {resp.status_code}")

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
                    logger.info(f"Stream completed, total chunks: {chunk_count}")
                    break

                try:
                    data = json.loads(data_str)
                except json.JSONDecodeError:
                    continue

                # OpenAI 格式的响应解析
                choices = data.get("choices", [])
                if not choices:
                    continue

                delta = choices[0].get("delta", {})
                content = delta.get("content", "")

                if content:
                    chunk_count += 1
                    yield content

            logger.info(f"Stream finished, total chunks: {chunk_count}")
