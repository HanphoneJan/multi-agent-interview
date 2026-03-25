"""Tests for LLM conversation context (Redis-backed)."""
import pytest
from unittest.mock import AsyncMock, patch

from app.core.llm_context import get_messages, append_message, clear_context


@pytest.mark.asyncio
async def test_get_messages_empty():
    """When key is missing, get_messages returns []."""
    with patch("app.core.llm_context.cache") as mock_cache:
        mock_cache.get = AsyncMock(return_value=None)
        out = await get_messages("s1")
        assert out == []
        mock_cache.get.assert_called_once()


@pytest.mark.asyncio
async def test_get_messages_returns_list():
    """get_messages parses JSON list and returns list of dicts."""
    with patch("app.core.llm_context.cache") as mock_cache:
        mock_cache.get = AsyncMock(return_value='[{"role":"assistant","content":"Hi"},{"role":"user","content":"Hello"}]')
        out = await get_messages("s1")
        assert len(out) == 2
        assert out[0]["role"] == "assistant" and out[0]["content"] == "Hi"
        assert out[1]["role"] == "user" and out[1]["content"] == "Hello"


@pytest.mark.asyncio
async def test_append_message():
    """append_message gets list, appends one message, sets with TTL."""
    with patch("app.core.llm_context.cache") as mock_cache:
        mock_cache.get = AsyncMock(return_value='[{"role":"assistant","content":"Q1"}]')
        mock_cache.set = AsyncMock()
        await append_message("s1", "user", "A1")
        mock_cache.get.assert_called_once()
        mock_cache.set.assert_called_once()
        call_arg = mock_cache.set.call_args[0][1]
        assert isinstance(call_arg, list)
        assert len(call_arg) == 2
        assert call_arg[1]["role"] == "user" and call_arg[1]["content"] == "A1"


@pytest.mark.asyncio
async def test_clear_context():
    """clear_context deletes the key."""
    with patch("app.core.llm_context.cache") as mock_cache:
        mock_cache.delete = AsyncMock()
        await clear_context("s1")
        mock_cache.delete.assert_called_once()
        assert "s1" in mock_cache.delete.call_args[0][0]
