"""
Qwen3-Omni Realtime API 测试脚本

测试内容:
1. WebSocket 连接建立
2. 发送音频数据
3. 接收 AI 响应
"""

import asyncio
import json
import os
import websockets
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY")
# 根据文档使用正确的 WebSocket URL
DASHSCOPE_REALTIME_URL = "wss://dashscope.aliyuncs.com/api-ws/v1/realtime?model=qwen3-omni-flash-realtime"


async def test_qwen3_omni_connection():
    """测试 Qwen3-Omni Realtime API 连接"""

    print("=" * 60)
    print("Qwen3-Omni Realtime API 连接测试")
    print("=" * 60)

    if not DASHSCOPE_API_KEY:
        print("[X] 错误: DASHSCOPE_API_KEY 未配置")
        return False

    print(f"[OK] API Key 已配置: {DASHSCOPE_API_KEY[:8]}...")

    # WebSocket URL 已包含模型参数，使用 header 认证
    ws_url = DASHSCOPE_REALTIME_URL

    print(f"\n正在连接: {ws_url}")

    try:
        async with websockets.connect(
            ws_url,
            subprotocols=["json"],
            additional_headers={
                "Authorization": f"Bearer {DASHSCOPE_API_KEY}"
            },
            ping_interval=20,
            ping_timeout=10
        ) as websocket:
            print("[OK] WebSocket 连接成功!")

            # 发送 session.update 初始化 (根据文档配置)
            session_config = {
                "type": "session.update",
                "session": {
                    "modalities": ["text", "audio"],  # 输出文本和音频
                    "voice": "Cherry",  # 文档示例音色
                    "input_audio_format": "pcm16",  # 文档: pcm16
                    "output_audio_format": "pcm24",  # Flash模型: pcm24
                    "instructions": "你是AI面试官，负责与用户进行语音面试。请用中文交流。",
                    "turn_detection": {
                        "type": "server_vad",
                        "threshold": 0.5,
                        "silence_duration_ms": 800
                    }
                }
            }

            print("\n发送 session.update...")
            await websocket.send(json.dumps(session_config))

            # 等待响应
            response = await asyncio.wait_for(
                websocket.recv(),
                timeout=10.0
            )
            data = json.loads(response)
            print(f"收到响应: {data}")

            if data.get("type") == "session.updated":
                print("[OK] Session 初始化成功!")
                session = data.get("session", {})
                print(f"  - Model: {session.get('model', 'N/A')}")
                print(f"  - Voice: {session.get('voice', 'N/A')}")
            else:
                print(f"[!] 未预期的响应类型: {data.get('type')}")

            # 测试对话
            print("\n测试对话...")
            conversation_item = {
                "type": "conversation.item.create",
                "item": {
                    "type": "message",
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "你好，请用一句话介绍自己"
                        }
                    ]
                }
            }

            await websocket.send(json.dumps(conversation_item))
            print("[OK] 发送对话消息")

            # 请求响应
            response_request = {
                "type": "response.create"
            }
            await websocket.send(json.dumps(response_request))
            print("[OK] 请求 AI 响应")

            # 接收 AI 响应
            print("\n等待 AI 响应...")
            response_count = 0
            audio_chunks = 0
            text_received = ""

            try:
                while True:
                    msg = await asyncio.wait_for(
                        websocket.recv(),
                        timeout=15.0
                    )
                    data = json.loads(msg)
                    msg_type = data.get("type", "unknown")

                    if msg_type == "response.audio.delta":
                        audio_chunks += 1
                        if audio_chunks == 1:
                            print("[OK] 收到音频流 (streaming...)")
                    elif msg_type == "response.audio_transcript.delta":
                        delta = data.get("delta", "")
                        text_received += delta
                    elif msg_type == "response.audio.done":
                        print(f"[OK] 音频传输完成 ({audio_chunks} chunks)")
                    elif msg_type == "response.done":
                        print("[OK] 响应完成")
                        response_count += 1
                        if response_count >= 1:
                            break
                    elif msg_type == "error":
                        print(f"[X] 错误: {data.get('error', 'Unknown')}")
                        break
                    else:
                        print(f"  消息: {msg_type}")

            except asyncio.TimeoutError:
                print("[!] 响应超时，但连接正常")

            print(f"\n收到的文本: {text_received or '(无)'}")

            # 关闭连接
            print("\n关闭连接...")
            await websocket.close()
            print("[OK] 测试完成!")

            return True

    except websockets.exceptions.WebSocketException as e:
        print(f"[X] WebSocket 错误: {e}")
        return False
    except Exception as e:
        print(f"[X] 错误: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_local_websocket_endpoint():
    """测试本地 WebSocket 端点"""

    print("\n" + "=" * 60)
    print("本地 WebSocket 端点测试")
    print("=" * 60)

    local_ws_url = "ws://localhost:8000/api/v1/ws/interview/realtime/test-session-123?token=test-token"

    print(f"连接到: {local_ws_url}")

    try:
        async with websockets.connect(local_ws_url) as websocket:
            print("[OK] 本地 WebSocket 连接成功!")

            # 发送开始消息
            start_msg = {
                "type": "start",
                "timestamp": 1234567890
            }
            await websocket.send(json.dumps(start_msg))
            print("[OK] 发送 start 消息")

            # 等待响应
            try:
                response = await asyncio.wait_for(
                    websocket.recv(),
                    timeout=5.0
                )
                data = json.loads(response)
                print(f"收到: {data}")

                if data.get("type") == "connected":
                    print("[OK] 后端连接成功!")
                    return True
                elif data.get("type") == "error":
                    print(f"[X] 后端错误: {data.get('error')}")
                    return False

            except asyncio.TimeoutError:
                print("[!] 等待响应超时")
                return False

    except ConnectionRefusedError:
        print("[X] 无法连接到本地服务器，请确保服务已启动:")
        print("   uv run uvicorn app.main:app --reload")
        return False
    except Exception as e:
        print(f"[X] 错误: {e}")
        return False


async def main():
    """主测试函数"""

    print("\nQwen3-Omni Realtime API 测试\n")

    # 测试1: 直接连接 DashScope API
    print("\n" + "=" * 60)
    print("测试 1: DashScope Realtime API 直连测试")
    print("=" * 60)

    success = await test_qwen3_omni_connection()

    if success:
        print("\n[OK] DashScope API 测试通过!")
    else:
        print("\n[X] DashScope API 测试失败")

    # 测试2: 本地 WebSocket 端点
    print("\n" + "=" * 60)
    print("测试 2: 本地 WebSocket 端点测试")
    print("=" * 60)

    local_success = await test_local_websocket_endpoint()

    # 总结
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    print(f"DashScope API 连接: {'[OK] 通过' if success else '[X] 失败'}")
    print(f"本地 WebSocket 端点: {'[OK] 通过' if local_success else '[X] 失败'}")

    if success and local_success:
        print("\n[OK] 所有测试通过!")
    else:
        print("\n[!] 部分测试失败，请检查配置")


if __name__ == "__main__":
    asyncio.run(main())
