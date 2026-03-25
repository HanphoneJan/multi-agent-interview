"""LLM conversation context for interview sessions (Redis-backed).

Stores messages list per session for multi-turn dialogue and LLM memory.
Key: interview:llm_ctx:{session_id}
Value: JSON array of {"role": "user"|"assistant"|"system", "content": "..."}
"""
import json
from typing import Any

from app.core.cache import cache
from app.core.constants import INTERVIEW_LLM_CTX_TTL
from app.utils.log_helper import get_logger

logger = get_logger("core.llm_context")


def _key(session_id: str) -> str:
    return f"interview:llm_ctx:{session_id}"


async def get_messages(session_id: str) -> list[dict[str, str]]:
    """Get conversation messages for a session. Returns [] if missing or invalid."""
    try:
        raw = await cache.get(_key(session_id))
        if not raw:
            return []
        data = json.loads(raw)
        if not isinstance(data, list):
            return []
        return [{"role": str(m.get("role", "user")), "content": str(m.get("content", ""))} for m in data]
    except (json.JSONDecodeError, TypeError) as e:
        logger.warning("llm_context get_messages parse error: %s", e)
        return []


async def append_message(session_id: str, role: str, content: str) -> None:
    """Append one message and refresh TTL."""
    messages = await get_messages(session_id)
    messages.append({"role": role, "content": content or ""})
    await cache.set(_key(session_id), messages, ex=INTERVIEW_LLM_CTX_TTL)


async def clear_context(session_id: str) -> None:
    """Remove conversation context for the session."""
    await cache.delete(_key(session_id))
