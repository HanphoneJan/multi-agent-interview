"""Integration test for non-realtime interview with Qwen3-Omni"""
import asyncio
import os
import sys

# Add app to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


async def test_qwen3_omni_http_service():
    """Test Qwen3-Omni HTTP service connection"""
    print("=" * 60)
    print("Test 1: Qwen3-Omni HTTP Service")
    print("=" * 60)

    try:
        from app.services.qwen3_omni_http_service import Qwen3OmniHTTPService

        service = Qwen3OmniHTTPService()
        print(f"✓ Service initialized")
        print(f"  - Model: {service.model}")
        print(f"  - Base URL: {service.base_url}")
        print(f"  - Available voices: {service.VOICES}")

        # Test building system prompt
        prompt = service.build_interview_system_prompt(
            scenario_name="后端开发工程师面试",
            scenario_description="考察候选人的后端开发能力",
            is_technical=True
        )
        print(f"✓ System prompt generated ({len(prompt)} chars)")

        return True

    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_qwen_vl_service():
    """Test Qwen-VL service"""
    print("\n" + "=" * 60)
    print("Test 2: Qwen-VL Service")
    print("=" * 60)

    try:
        from app.services.qwen_vl_service import QwenVLService

        service = QwenVLService()
        print(f"✓ Service initialized")
        print(f"  - Model: {service.model}")
        print(f"  - Base URL: {service.base_url}")

        return True

    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_oss_service():
    """Test OSS service"""
    print("\n" + "=" * 60)
    print("Test 3: OSS Service")
    print("=" * 60)

    try:
        from app.services.oss_service import OSSService

        service = OSSService()
        print(f"✓ Service initialized")
        print(f"  - Enabled: {service.enabled}")
        print(f"  - Bucket: {service.bucket_name if service.enabled else 'N/A'}")
        print(f"  - Endpoint: {service.endpoint if service.enabled else 'N/A'}")

        # Test local file save (when OSS not configured)
        test_data = b"test video content"
        result = await service.upload_file(
            file_data=test_data,
            filename="test.webm",
            folder="test"
        )
        print(f"✓ File upload test passed")
        print(f"  - URL: {result['file_url'][:50]}...")
        print(f"  - Size: {result['size']} bytes")

        return True

    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_chat_with_omni():
    """Test actual chat with Qwen3-Omni (requires API key)"""
    print("\n" + "=" * 60)
    print("Test 4: Qwen3-Omni Chat (requires API key)")
    print("=" * 60)

    try:
        from app.services.qwen3_omni_http_service import Qwen3OmniHTTPService

        service = Qwen3OmniHTTPService()

        messages = [
            {"role": "system", "content": "你是专业的技术面试官。请简短问候候选人。"},
            {"role": "user", "content": "你好，我准备好了。"}
        ]

        print("Sending chat request...")
        text_chunks = []
        audio_chunks = []

        async for chunk in service.chat(messages, voice="Cherry", stream=True):
            if chunk.type == "text":
                text_chunks.append(chunk.content)
                print(f"[Text] {chunk.content}", end="", flush=True)
            elif chunk.type == "audio":
                audio_chunks.append(chunk.audio_data)
                print(f"[Audio chunk: {len(chunk.audio_data) if chunk.audio_data else 0} bytes]", end="\r")

        full_text = "".join(text_chunks)
        print(f"\n\n✓ Chat completed")
        print(f"  - Response length: {len(full_text)} chars")
        print(f"  - Audio chunks: {len(audio_chunks)}")

        return True

    except Exception as e:
        print(f"✗ Test failed: {e}")
        print("  (This is expected if DASHSCOPE_API_KEY is not set)")
        return False


async def run_all_tests():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("Non-Realtime Interview Integration Tests")
    print("=" * 60)

    results = []

    # Test 1: Qwen3-Omni HTTP Service
    results.append(("Qwen3-Omni HTTP Service", await test_qwen3_omni_http_service()))

    # Test 2: Qwen-VL Service
    results.append(("Qwen-VL Service", await test_qwen_vl_service()))

    # Test 3: OSS Service
    results.append(("OSS Service", await test_oss_service()))

    # Test 4: Chat with Omni (optional, requires API key)
    # Uncomment to test with actual API
    # results.append(("Qwen3-Omni Chat", await test_chat_with_omni()))

    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    for name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{status}: {name}")

    passed_count = sum(1 for _, p in results if p)
    print(f"\nTotal: {passed_count}/{len(results)} tests passed")


if __name__ == "__main__":
    asyncio.run(run_all_tests())
