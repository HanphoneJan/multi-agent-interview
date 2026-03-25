"""
WebSocket 端点连接测试

测试 WebSocket 端点是否正确注册和可连接
"""

import asyncio
import json
import websockets


async def test_websocket_endpoint():
    """测试本地 WebSocket 端点"""

    ws_url = "ws://localhost:8000/api/v1/ws/interview/realtime/test-session-123?token=invalid-token"

    print("=" * 60)
    print("WebSocket 端点连接测试")
    print("=" * 60)
    print(f"连接到: {ws_url}")

    try:
        async with websockets.connect(ws_url) as websocket:
            print("[OK] WebSocket 连接建立成功!")

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
                print(f"收到: {json.dumps(data, indent=2, ensure_ascii=False)}")

                if data.get("type") == "connected":
                    print("\n[OK] WebSocket 端点工作正常!")
                    return True
                elif data.get("type") == "error":
                    print(f"\n响应类型: {data.get('type')}")
                    print(f"消息: {data.get('error', 'Unknown')}")
                    return True  # 端点工作，只是认证失败

            except asyncio.TimeoutError:
                print("\n[!] 等待响应超时，但连接已建立")
                return True

    except websockets.exceptions.InvalidStatus as e:
        if e.response.status_code == 403:
            print(f"\n[OK] 端点响应 403 (Token 无效) - 端点工作正常!")
            return True
        else:
            print(f"\n[X] HTTP 错误: {e.response.status_code}")
            return False
    except ConnectionRefusedError:
        print("\n[X] 无法连接到服务器")
        print("   请确保服务已启动: uv run uvicorn app.main:app --reload")
        return False
    except Exception as e:
        print(f"\n[X] 错误: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    success = await test_websocket_endpoint()

    print("\n" + "=" * 60)
    if success:
        print("[OK] WebSocket 端点测试通过!")
    else:
        print("[X] WebSocket 端点测试失败")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
