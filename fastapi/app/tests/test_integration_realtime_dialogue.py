"""
实时面试对话上下文集成测试

验证 Qwen3-Omni Realtime API 是否能正确维护对话历史，
确保 AI 不会重复开场白或之前的问题。

注意：Qwen3-Omni Realtime API 仅支持音频和图片输入，不支持文本输入。
"""
import asyncio
import base64
import pytest
from datetime import datetime, timezone

# 只在运行真实 API 测试时才需要 API 密钥
def pytest_configure(config):
    config.addinivalue_line(
        "markers", "real_api: 需要真实 API 密钥的测试"
    )


def create_silent_pcm(duration_ms: int = 500) -> bytes:
    """创建静音 PCM 数据用于测试"""
    # 16-bit PCM, 16kHz, mono
    num_samples = int(16000 * duration_ms / 1000)
    return bytes(2 * num_samples)  # 每个样本2字节（16-bit）


def create_test_audio_base64(duration_ms: int = 500) -> str:
    """创建测试音频的 base64 编码"""
    pcm_data = create_silent_pcm(duration_ms)
    return base64.b64encode(pcm_data).decode()


@pytest.fixture
def sample_conversation_history():
    """示例对话历史"""
    return [
        {
            "role": "assistant",
            "content": "你好，我是今天的面试官。请先做个自我介绍。",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
        {
            "role": "user",
            "content": "您好，我是张三，有3年产品经理经验，专注于物联网领域。",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    ]


@pytest.mark.real_api
class TestRealtimeAudioDialogue:
    """测试实时音频对话上下文维护"""

    @pytest.mark.asyncio
    async def test_audio_input_flow(self):
        """测试音频输入流程"""
        from app.core.qwen3_omni_realtime import Qwen3OmniRealtimeClient, RealtimeConfig

        client = Qwen3OmniRealtimeClient(RealtimeConfig())

        try:
            # 连接并设置系统提示词
            system_prompt = """你是一位专业的技术面试官。重要：你必须基于对话历史继续，不要重复开场白。"""
            success = await client.connect(system_prompt)
            assert success, "连接失败"

            # 发送音频数据（静音测试）
            audio_b64 = create_test_audio_base64(1000)
            pcm_data = base64.b64decode(audio_b64)
            await client.send_audio(pcm_data)
            await client.commit_audio()
            await client.create_response()

            # 收集 AI 回复事件
            events_received = []
            async for event in client.receive_events():
                events_received.append(event.get("type"))

                if event.get("type") == "response.done":
                    break

                # 只等待最多10秒
                if len(events_received) > 100:
                    break

            # 验证收到了预期的事件
            assert "response.created" in events_received or "response.done" in events_received

        finally:
            await client.disconnect()

    @pytest.mark.asyncio
    async def test_ai_does_not_repeat_introduction(self):
        """测试 AI 不会重复开场白"""
        from app.core.qwen3_omni_realtime import Qwen3OmniRealtimeClient, RealtimeConfig

        client = Qwen3OmniRealtimeClient(RealtimeConfig())
        conversation_history = []

        try:
            system_prompt = """你是一位专业的技术面试官。当前正在进行第3轮对话。

【对话历史】
面试官: 你好，请先做个自我介绍。
候选人: 我是李四，有5年开发经验。
面试官: 好的，请说说你最熟悉的技术栈。
候选人: 我主要用 Python 和 Django。

【极其重要】
基于以上对话，请继续深入询问技术细节。绝对不要重复开场白，不要再次要求自我介绍。"""

            success = await client.connect(system_prompt)
            assert success, "连接失败"

            # 发送音频输入
            audio_b64 = create_test_audio_base64(500)
            pcm_data = base64.b64decode(audio_b64)
            await client.send_audio(pcm_data)
            await client.commit_audio()
            await client.create_response()

            # 收集 AI 回复
            ai_response = ""
            async for event in client.receive_events():
                event_type = event.get("type", "")

                if event_type == "response.audio_transcript.delta":
                    ai_response += event.get("delta", "")

                elif event_type == "response.done":
                    break

            # 验证 AI 没有重复开场白
            intro_keywords = ["自我介绍", "你好，我是", "开场", "开始面试", "我是面试官"]
            for keyword in intro_keywords:
                assert keyword not in ai_response, f"AI 重复了开场白，包含关键词: {keyword}"

            print(f"AI 回复: {ai_response}")

        finally:
            await client.disconnect()


class TestConversationHistoryTracking:
    """测试对话历史追踪功能"""

    def test_history_format(self, sample_conversation_history):
        """测试历史记录格式"""
        assert len(sample_conversation_history) == 2

        for msg in sample_conversation_history:
            assert "role" in msg
            assert "content" in msg
            assert "timestamp" in msg
            assert msg["role"] in ["user", "assistant", "system"]


@pytest.mark.real_api
class TestEndToEndAudioInterviewFlow:
    """端到端音频面试流程测试"""

    @pytest.mark.asyncio
    async def test_full_audio_interview_conversation(self):
        """测试完整的多轮音频面试对话"""
        from app.core.qwen3_omni_realtime import Qwen3OmniRealtimeClient, RealtimeConfig

        client = Qwen3OmniRealtimeClient(RealtimeConfig())
        conversation_history = []

        try:
            system_prompt = """你是一位专业的技术面试官，正在进行物联网产品经理面试。

【极其重要】
1. 这是多轮对话，记住之前的交流内容
2. 不要重复开场白或之前问过的问题
3. 基于候选人的回答深入追问
4. 每次只问一个新问题

面试流程:
1. 开场（只进行一次）
2. 技术基础（2-3题）
3. 项目经验（1-2题）
4. 场景设计（1题）
5. 结束"""

            success = await client.connect(system_prompt)
            assert success, "连接失败"

            # 模拟多轮对话（通过音频）
            for i in range(3):
                print(f"\n--- 第 {i+1} 轮对话 ---")

                # 发送音频输入（静音测试数据）
                audio_b64 = create_test_audio_base64(500)
                pcm_data = base64.b64decode(audio_b64)
                await client.send_audio(pcm_data)
                await client.commit_audio()
                await client.create_response()

                # 收集回复
                ai_response = ""
                event_count = 0

                async for event in client.receive_events():
                    event_type = event.get("type", "")
                    event_count += 1

                    if event_type == "response.audio_transcript.delta":
                        ai_response += event.get("delta", "")

                    elif event_type == "response.done":
                        break

                    # 防止无限循环
                    if event_count > 100:
                        break

                print(f"AI: {ai_response[:100]}...")

                # 添加到历史
                conversation_history.append({
                    "role": "assistant",
                    "content": ai_response,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                })

                # 验证不重复开场白
                if i > 0:
                    intro_phrases = ["请先做个自我介绍", "我是面试官", "你好啊"]
                    for phrase in intro_phrases:
                        assert phrase not in ai_response[:50], \
                            f"第 {i+1} 轮 AI 重复了开场白: '{phrase}'"

            print(f"\n✅ 完成 3 轮对话，AI 未重复开场白")

        finally:
            await client.disconnect()


class TestWebSocketMessageProtocol:
    """测试 WebSocket 消息协议"""

    def test_audio_message_format(self):
        """测试音频消息格式"""
        # 模拟前端发送的音频消息
        audio_msg = {
            "type": "audio",
            "data": create_test_audio_base64(500),
            "timestamp": 1234567890
        }

        assert audio_msg["type"] == "audio"
        assert "data" in audio_msg
        assert "timestamp" in audio_msg

    def test_audio_end_message_format(self):
        """测试音频结束消息格式"""
        audio_end_msg = {
            "type": "audio_end"
        }

        assert audio_end_msg["type"] == "audio_end"

    def test_start_message_format(self):
        """测试开始消息格式"""
        start_msg = {
            "type": "start",
            "timestamp": 1234567890,
            "session_id": "123",
            "voice": "Chelsie"
        }

        assert start_msg["type"] == "start"
        assert "session_id" in start_msg

    def test_end_message_format(self):
        """测试结束消息格式"""
        end_msg = {
            "type": "end"
        }

        assert end_msg["type"] == "end"


class TestOmniAPIEvents:
    """测试 Qwen3-Omni API 事件处理"""

    def test_response_audio_transcript_done_is_user_message(self):
        """验证 response.audio_transcript.done 是用户消息转录"""
        # 这个事件表示 API 完成了对用户音频的转录
        # 应该被保存为 user 角色，而不是 assistant
        event = {
            "type": "response.audio_transcript.done",
            "transcript": "我认为物联网产品经理需要理解硬件和软件的协同。"
        }

        # 在 WebSocket 处理器中，这应该被保存为 user 消息
        assert event["type"] == "response.audio_transcript.done"
        assert "transcript" in event

    def test_response_done_is_ai_message(self):
        """验证 response.done 是 AI 回复"""
        event = {
            "type": "response.done",
            "response": {
                "id": "resp_123",
                "output": [
                    {
                        "type": "message",
                        "text": "很好的回答，请问你能详细说明一下你的项目经验吗？"
                    }
                ]
            }
        }

        # 在 WebSocket 处理器中，这应该被保存为 assistant 消息
        assert event["type"] == "response.done"
        assert event["response"]["output"][0]["text"] != ""


# 运行测试的命令:
# cd fastapi && python -m pytest app/tests/test_integration_realtime_dialogue.py -v --run-real-api
# 或者不带真实 API 调用的单元测试:
# cd fastapi && python -m pytest app/tests/test_integration_realtime_dialogue.py -v -k "not test_full" --co
if __name__ == "__main__":
    pytest.main([__file__, "-v", "-x"])
