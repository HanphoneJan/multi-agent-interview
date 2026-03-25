"""Test script for Qwen3-Omni HTTP Service"""
import asyncio
import os
import sys

# Add app to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

print(f"DASHSCOPE_API_KEY: {'已配置' if os.getenv('DASHSCOPE_API_KEY') else '未配置'}")

from app.services.qwen3_omni_http_service import Qwen3OmniHTTPService


async def test_qwen3_omni_http():
    """Test Qwen3-Omni HTTP API"""
    print("=" * 60)
    print("Testing Qwen3-Omni HTTP Service")
    print("=" * 60)

    # Initialize service
    service = Qwen3OmniHTTPService()

    # Test 1: Simple chat
    print("\n[Test 1] Simple chat with text output")
    print("-" * 60)

    messages = [
        {"role": "system", "content": "你是专业的技术面试官，正在面试一位软件工程师候选人。"},
        {"role": "user", "content": "请介绍一下你的项目经验。"}
    ]

    print("Sending request...")
    text_chunks = []
    audio_chunks = []

    try:
        async for chunk in service.chat(messages, voice="Cherry", stream=True):
            if chunk.type == "text":
                text_chunks.append(chunk.content)
                print(f"[Text] {chunk.content}", end="", flush=True)
            elif chunk.type == "audio":
                audio_chunks.append(chunk.audio_data)
                print(f"[Audio chunk: {len(chunk.audio_data)} bytes]", end="\r")
            elif chunk.type == "usage":
                print(f"\n[Usage] {chunk.usage}")

        full_text = "".join(text_chunks)
        print(f"\n\nFull response ({len(full_text)} chars):")
        print(full_text)
        print(f"\nAudio chunks: {len(audio_chunks)}")

    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()

    # Test 2: Interview scenario
    print("\n" + "=" * 60)
    print("[Test 2] Interview scenario")
    print("-" * 60)

    system_prompt = service.build_interview_system_prompt(
        scenario_name="后端开发工程师面试",
        scenario_description="考察候选人的后端开发能力、系统设计能力和问题解决能力",
        is_technical=True
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": "你好，我准备好了。"}
    ]

    print("System prompt:")
    print(system_prompt[:200] + "...")
    print("\nSending interview request...")

    try:
        async for chunk in service.chat(messages, voice="Cherry", stream=True):
            if chunk.type == "text":
                print(chunk.content, end="", flush=True)
        print("\n")
    except Exception as e:
        print(f"\nError: {e}")

    print("=" * 60)
    print("Test completed!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_qwen3_omni_http())
