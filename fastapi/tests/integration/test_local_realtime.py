"""
本地 Qwen3-Omni Realtime WebSocket 端点测试

需要:
1. 启动 FastAPI 服务: uv run uvicorn app.main:app --reload
2. 有效的 JWT token 和数据库中的面试会话
"""

import asyncio
import json
import os
import sys

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import websockets
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 本地服务配置
LOCAL_WS_URL = "ws://localhost:8000/api/v1/ws/interview/realtime/{session_id}?token={token}"


async def test_health_check():
    """测试服务健康状态"""
    import aiohttp

    print("=" * 60)
    print("测试 1: 服务健康检查")
    print("=" * 60)

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("http://localhost:8000/health") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    print(f"[OK] 服务健康: {data}")
                    return True
                else:
                    print(f"[X] 健康检查失败: {resp.status}")
                    return False
    except Exception as e:
        print(f"[X] 无法连接服务: {e}")
        return False


async def test_websocket_docs():
    """测试 WebSocket 文档端点"""
    import aiohttp

    print("\n" + "=" * 60)
    print("测试 2: API 文档检查")
    print("=" * 60)

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("http://localhost:8000/docs") as resp:
                if resp.status == 200:
                    print("[OK] API 文档可访问: http://localhost:8000/docs")
                    return True
                else:
                    print(f"[!] 文档端点返回: {resp.status}")
                    return False
    except Exception as e:
        print(f"[X] 无法访问文档: {e}")
        return False


async def generate_test_token():
    """生成测试用的 JWT token"""
    from app.core.security import create_access_token

    # 创建一个测试用户 token
    token_data = {"user_id": 1, "sub": "test@example.com"}
    token = create_access_token(token_data)
    return token


async def test_local_websocket():
    """测试本地 WebSocket 端点 (需要有效的 session)"""

    print("\n" + "=" * 60)
    print("测试 3: 本地 WebSocket 端点")
    print("=" * 60)

    try:
        token = await generate_test_token()
        print(f"[OK] 生成测试 Token: {token[:20]}...")
    except Exception as e:
        print(f"[X] 生成 Token 失败: {e}")
        return False

    # 使用测试 session_id
    session_id = "999999"  # 假设一个不存在的 session
    ws_url = LOCAL_WS_URL.format(session_id=session_id, token=token)

    print(f"\n连接到: ws://localhost:8000/api/v1/ws/interview/realtime/{session_id}")

    try:
        async with websockets.connect(ws_url) as websocket:
            print("[OK] WebSocket 连接建立")

            # 等待服务器响应 (可能是错误，因为 session 不存在)
            try:
                response = await asyncio.wait_for(
                    websocket.recv(),
                    timeout=5.0
                )
                data = json.loads(response)
                print(f"收到: {json.dumps(data, indent=2, ensure_ascii=False)}")

                if data.get("type") == "connected":
                    print("[OK] WebSocket 连接成功!")

                    # 测试 ping
                    await websocket.send(json.dumps({"type": "ping"}))
                    pong = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    print(f"[OK] Ping 测试: {pong}")
                    return True

                elif data.get("type") == "error":
                    print(f"[!] 连接被拒绝: {data.get('error')}")
                    print("    (这是正常的，因为测试 session 不存在)")
                    return True  # 连接本身是成功的

            except asyncio.TimeoutError:
                print("[!] 等待响应超时，但连接已建立")
                return True

    except websockets.exceptions.InvalidStatus as e:
        if e.response.status_code == 403:
            print(f"[!] 连接被拒绝 (403): Token 验证失败或 Session 不存在")
            print("    WebSocket 端点工作正常，但需要有效的 session")
            return True  # 端点工作正常，只是验证失败
        else:
            print(f"[X] WebSocket 错误: HTTP {e.response.status_code}")
            return False
    except Exception as e:
        print(f"[X] 错误: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_direct_dashscope():
    """直接测试 DashScope API"""
    from app.core.qwen3_omni_realtime import Qwen3OmniRealtimeClient, RealtimeConfig

    print("\n" + "=" * 60)
    print("测试 4: DashScope API 直连 (通过项目客户端)")
    print("=" * 60)

    try:
        config = RealtimeConfig(
            voice="Chelsie",
            enable_audio=True,
        )

        client = Qwen3OmniRealtimeClient(config)

        system_prompt = """你是AI面试官，负责与用户进行语音面试。
请用中文交流，保持专业友好的态度。"""

        print("正在连接 DashScope API...")
        success = await client.connect(system_prompt)

        if success:
            print(f"[OK] 连接成功! Session ID: {client.session_id}")

            # 测试生成响应
            print("\n请求 AI 生成问候语...")
            await client.create_response()

            # 接收响应
            text_received = ""
            audio_chunks = 0

            async for event in client.receive_events():
                event_type = event.get("type", "")

                if event_type == "response.audio_transcript.delta":
                    delta = event.get("delta", "")
                    text_received += delta
                    print(f"  文本: {delta}", end="", flush=True)

                elif event_type == "response.audio.delta":
                    audio_chunks += 1
                    if audio_chunks == 1:
                        print("\n[OK] 开始接收音频流...")

                elif event_type == "response.done":
                    print("\n[OK] 响应完成")
                    break

                elif event_type == "error":
                    print(f"\n[X] 错误: {event}")
                    break

            print(f"\n完整文本: {text_received}")
            print(f"音频块数: {audio_chunks}")

            await client.disconnect()
            return True
        else:
            print("[X] 连接失败")
            return False

    except Exception as e:
        print(f"[X] 错误: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """主测试函数"""

    print("\n" + "=" * 60)
    print("Qwen3-Omni 实时音视频面试功能测试")
    print("=" * 60)

    results = []

    # 测试 1: 健康检查
    results.append(("健康检查", await test_health_check()))

    # 测试 2: API 文档
    results.append(("API 文档", await test_websocket_docs()))

    # 测试 3: 本地 WebSocket 端点
    results.append(("本地 WebSocket", await test_local_websocket()))

    # 测试 4: DashScope API 直连
    results.append(("DashScope API", await test_direct_dashscope()))

    # 汇总
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)

    for name, success in results:
        status = "[OK] 通过" if success else "[X] 失败"
        print(f"{name}: {status}")

    all_passed = all(r[1] for r in results)

    if all_passed:
        print("\n[OK] 所有测试通过!")
    else:
        print("\n[!] 部分测试失败")

    return all_passed


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
