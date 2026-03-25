"""Direct test for Qwen3-Omni HTTP API without full app initialization"""
import asyncio
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("=" * 60)
print("Direct Qwen3-Omni HTTP API Test")
print("=" * 60)

# Check API key
api_key = os.getenv("DASHSCOPE_API_KEY")
if not api_key:
    print("[FAIL] DASHSCOPE_API_KEY not configured")
    sys.exit(1)

print(f"[OK] DASHSCOPE_API_KEY: {api_key[:10]}...")

# Test OpenAI client connection
print("\n[Test 1] Initialize OpenAI client")
print("-" * 60)

try:
    from openai import AsyncOpenAI

    base_url = os.getenv("DASHSCOPE_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
    client = AsyncOpenAI(
        api_key=api_key,
        base_url=base_url,
    )
    print(f"[OK] OpenAI client initialized")
    print(f"  Base URL: {base_url}")
except Exception as e:
    print(f"[FAIL] Failed to initialize client: {e}")
    sys.exit(1)

# Test API call
print("\n[Test 2] Test Qwen3-Omni HTTP API call")
print("-" * 60)

async def test_api():
    try:
        messages = [
            {"role": "system", "content": "你是专业的技术面试官，请简短问候候选人。"},
            {"role": "user", "content": "你好，我准备好了。"}
        ]

        print("Sending request to qwen3-omni-flash-2025-12-01...")
        print("Model: qwen3-omni-flash-2025-12-01")
        print("Modalities: text, audio")
        print("Voice: Cherry")
        print()

        completion = await client.chat.completions.create(
            model="qwen3-omni-flash-2025-12-01",
            messages=messages,
            modalities=["text", "audio"],
            audio={"voice": "Cherry", "format": "wav"},
            stream=True,
            stream_options={"include_usage": True},
        )

        text_chunks = []
        audio_chunks = []

        print("Receiving response...")
        print("-" * 60)

        async for chunk in completion:
            if not chunk.choices:
                if hasattr(chunk, 'usage') and chunk.usage:
                    print(f"\n[Usage] Prompt: {chunk.usage.prompt_tokens}, Completion: {chunk.usage.completion_tokens}")
                continue

            delta = chunk.choices[0].delta

            # Handle text
            if delta.content:
                text_chunks.append(delta.content)
                print(delta.content, end="", flush=True)

            # Handle audio
            if hasattr(delta, 'audio') and delta.audio and hasattr(delta.audio, 'data'):
                audio_data = delta.audio.data
                if audio_data:
                    audio_chunks.append(audio_data)
                    print(f"\r[Audio chunk: {len(audio_data)} bytes]", end="", flush=True)

        full_text = "".join(text_chunks)
        print(f"\n\n{'=' * 60}")
        print("Response Summary:")
        print(f"  Text length: {len(full_text)} chars")
        print(f"  Audio chunks: {len(audio_chunks)}")
        if audio_chunks:
            total_audio = sum(len(a) for a in audio_chunks)
            print(f"  Total audio: {total_audio} bytes ({total_audio / 1024:.1f} KB)")
        print(f"{'=' * 60}")
        print("\n[SUCCESS] Qwen3-Omni HTTP API test passed!")

        return True

    except Exception as e:
        print(f"\n[FAIL] API call failed: {e}")
        import traceback
        traceback.print_exc()
        return False

# Run test
success = asyncio.run(test_api())
sys.exit(0 if success else 1)
