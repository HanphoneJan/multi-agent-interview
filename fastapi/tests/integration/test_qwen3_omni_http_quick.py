"""Quick test for Qwen3-Omni HTTP Service structure"""
import sys
import os

# Add app to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_service_structure():
    """Test that the service module can be imported and has the right structure"""
    try:
        # Import the service module (without initializing it)
        from app.services.qwen3_omni_http_service import ChatChunk, Qwen3OmniHTTPService

        # Check ChatChunk dataclass
        chunk = ChatChunk(type="text", content="Hello", audio_data=None, usage=None)
        assert chunk.type == "text"
        assert chunk.content == "Hello"
        print("✓ ChatChunk dataclass works correctly")

        # Check Qwen3OmniHTTPService has the required methods
        assert hasattr(Qwen3OmniHTTPService, 'chat')
        assert hasattr(Qwen3OmniHTTPService, 'chat_with_history')
        assert hasattr(Qwen3OmniHTTPService, 'build_interview_system_prompt')
        assert hasattr(Qwen3OmniHTTPService, 'VOICES')
        print("✓ Qwen3OmniHTTPService has all required methods")

        # Check VOICES list
        assert "Cherry" in Qwen3OmniHTTPService.VOICES
        assert "Serena" in Qwen3OmniHTTPService.VOICES
        print("✓ VOICES list is correct")

        print("\n✅ All structure tests passed!")
        return True

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_qwen_vl_service_structure():
    """Test that the QwenVLService module has the right structure"""
    try:
        from app.services.qwen_vl_service import VideoEvaluationResult, QwenVLService

        # Check VideoEvaluationResult dataclass
        result = VideoEvaluationResult(
            language_expression="Good",
            logical_thinking="Good",
            professional_knowledge="Good",
            communication_skills="Good",
            overall_impression="Good",
            overall_score=85.0,
            strengths=["Good communication"],
            weaknesses=["Could be better"],
            suggestions="Practice more",
            raw_response="raw"
        )
        assert result.overall_score == 85.0
        print("✓ VideoEvaluationResult dataclass works correctly")

        # Check QwenVLService has the required methods
        assert hasattr(QwenVLService, 'analyze_interview_video')
        assert hasattr(QwenVLService, 'batch_analyze_videos')
        print("✓ QwenVLService has all required methods")

        print("\n✅ All QwenVLService structure tests passed!")
        return True

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Testing Qwen3-Omni HTTP Service Structure")
    print("=" * 60)
    test_service_structure()

    print("\n" + "=" * 60)
    print("Testing Qwen-VL Service Structure")
    print("=" * 60)
    test_qwen_vl_service_structure()
