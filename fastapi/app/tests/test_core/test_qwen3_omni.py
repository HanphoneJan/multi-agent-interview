"""Qwen3-Omni Realtime API 测试

测试内容:
1. 客户端连接和初始化
2. 音频/视频发送
3. 事件接收处理
4. 错误处理
"""

import pytest
import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.mark.asyncio
class TestQwen3OmniRealtimeClient:
    """测试 Qwen3-Omni Realtime 客户端"""

    async def test_client_initialization(self):
        """测试客户端初始化"""
        from app.core.qwen3_omni_realtime import Qwen3OmniRealtimeClient, RealtimeConfig, ConversationState

        config = RealtimeConfig(
            voice="Chelsie",
            enable_audio=True,
        )
        client = Qwen3OmniRealtimeClient(config)

        assert client.config.voice == "Chelsie"
        assert client.config.enable_audio is True
        assert client.state == ConversationState.IDLE
        assert client.session_id is None
        assert not client.is_connected()

    async def test_default_system_prompt(self):
        """测试默认系统提示词"""
        from app.core.qwen3_omni_realtime import Qwen3OmniRealtimeClient

        client = Qwen3OmniRealtimeClient()
        prompt = client._default_system_prompt()

        assert "技术面试官" in prompt
        assert "语音" in prompt
        assert "面试流程" in prompt

    @pytest.mark.skip(reason="需要真实的 DashScope API Key，使用 --run-integration 运行")
    async def test_connect_to_dashscope(self):
        """测试连接 DashScope API (集成测试)"""
        from app.core.qwen3_omni_realtime import Qwen3OmniRealtimeClient, RealtimeConfig

        config = RealtimeConfig(voice="Chelsie")
        client = Qwen3OmniRealtimeClient(config)

        try:
            success = await client.connect("你是AI面试官，请用中文交流。")
            assert success is True
            assert client.is_connected()
            assert client.session_id is not None
        finally:
            await client.disconnect()

    async def test_connect_without_api_key(self):
        """测试未配置 API Key 时的错误处理"""
        from app.core.qwen3_omni_realtime import Qwen3OmniRealtimeClient

        with patch("app.core.qwen3_omni_realtime.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(
                QWEN_API_KEY="",
                DASHSCOPE_API_KEY=""
            )

            client = Qwen3OmniRealtimeClient()
            with pytest.raises(ValueError, match="未配置"):
                await client.connect()

    async def test_send_audio_not_connected(self):
        """测试未连接时发送音频应抛出错误"""
        from app.core.qwen3_omni_realtime import Qwen3OmniRealtimeClient

        client = Qwen3OmniRealtimeClient()
        with pytest.raises(RuntimeError, match="未连接"):
            await client.send_audio(b"fake_pcm_data")

    async def test_send_video_not_connected(self):
        """测试未连接时发送视频应抛出错误"""
        from app.core.qwen3_omni_realtime import Qwen3OmniRealtimeClient

        client = Qwen3OmniRealtimeClient()
        with pytest.raises(RuntimeError, match="未连接"):
            await client.send_video_frame("base64_image_data")


@pytest.mark.asyncio
class TestQwen3OmniClientManager:
    """测试客户端管理功能"""

    async def test_get_or_create_client(self):
        """测试获取或创建客户端"""
        from app.core.qwen3_omni_realtime import (
            get_or_create_client, close_client, _clients,
            Qwen3OmniRealtimeClient, RealtimeConfig
        )

        # Mock 客户端连接
        with patch.object(Qwen3OmniRealtimeClient, "connect", return_value=True):
            with patch.object(Qwen3OmniRealtimeClient, "is_connected", return_value=True):
                client = await get_or_create_client("test_session_123", "系统提示词")
                assert "test_session_123" in _clients
                assert _clients["test_session_123"] == client

                # 再次获取应该返回同一个客户端
                client2 = await get_or_create_client("test_session_123", "系统提示词")
                assert client == client2

        # 清理
        await close_client("test_session_123")
        assert "test_session_123" not in _clients

    async def test_close_all_clients(self):
        """测试关闭所有客户端"""
        from app.core.qwen3_omni_realtime import (
            close_all_clients, _clients,
            Qwen3OmniRealtimeClient
        )

        # Mock 多个客户端
        mock_client1 = MagicMock()
        mock_client1.disconnect = AsyncMock()
        mock_client2 = MagicMock()
        mock_client2.disconnect = AsyncMock()

        _clients["session1"] = mock_client1
        _clients["session2"] = mock_client2

        await close_all_clients()

        assert len(_clients) == 0
        mock_client1.disconnect.assert_called_once()
        mock_client2.disconnect.assert_called_once()


@pytest.mark.asyncio
class TestRealtimeConfig:
    """测试配置类"""

    def test_default_config(self):
        """测试默认配置"""
        from app.core.qwen3_omni_realtime import RealtimeConfig

        config = RealtimeConfig()
        assert config.model == "qwen3-omni-30b-a3b-instruct"
        assert config.voice == "Chelsie"
        assert config.enable_audio is True
        assert config.input_sample_rate == 16000
        assert config.output_sample_rate == 24000

    def test_custom_config(self):
        """测试自定义配置"""
        from app.core.qwen3_omni_realtime import RealtimeConfig

        config = RealtimeConfig(
            model="qwen3-omni-flash-realtime",
            voice="Cherry",
            enable_audio=False,
            input_sample_rate=48000,
        )
        assert config.model == "qwen3-omni-flash-realtime"
        assert config.voice == "Cherry"
        assert config.enable_audio is False
        assert config.input_sample_rate == 48000


@pytest.mark.asyncio
class TestConversationState:
    """测试对话状态"""

    def test_state_values(self):
        """测试状态值定义"""
        from app.core.qwen3_omni_realtime import ConversationState

        assert ConversationState.IDLE.value == "idle"
        assert ConversationState.CONNECTING.value == "connecting"
        assert ConversationState.LISTENING.value == "listening"
        assert ConversationState.THINKING.value == "thinking"
        assert ConversationState.SPEAKING.value == "speaking"
        assert ConversationState.PAUSED.value == "paused"
        assert ConversationState.ERROR.value == "error"


# 手动运行测试的入口
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
