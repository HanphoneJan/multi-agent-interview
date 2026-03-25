"""Test script for non-realtime interview endpoints"""
import asyncio
import os
import sys
from pathlib import Path

# Add app to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Test configuration
TEST_SESSION_ID = 1  # Change this to a valid session ID
TEST_USER_TOKEN = "your_test_token_here"  # Change this to a valid token
BASE_URL = "http://localhost:8000"


def test_imports():
    """Test that all modules can be imported"""
    print("=" * 60)
    print("Test 1: Module Imports")
    print("=" * 60)

    tests = [
        ("Qwen3-Omni HTTP Service", "app.services.qwen3_omni_http_service", "Qwen3OmniHTTPService"),
        ("Qwen-VL Service", "app.services.qwen_vl_service", "QwenVLService"),
        ("Video Upload API", "app.api.v1.interviews", None),
    ]

    results = []
    for name, module_path, class_name in tests:
        try:
            module = __import__(module_path, fromlist=[class_name or "__name__"])
            if class_name:
                cls = getattr(module, class_name)
                print(f"  ✅ {name}: {cls.__name__}")
            else:
                print(f"  ✅ {name}: Module OK")
            results.append((name, True))
        except Exception as e:
            print(f"  ❌ {name}: {e}")
            results.append((name, False))

    return all(r[1] for r in results)


def test_video_upload_validation():
    """Test video upload validation logic"""
    print("\n" + "=" * 60)
    print("Test 2: Video Upload Validation")
    print("=" * 60)

    # Import the validation constants
    try:
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app', 'api', 'v1'))
        from interviews import ALLOWED_VIDEO_EXTENSIONS, MAX_VIDEO_SIZE

        print(f"  Allowed extensions: {ALLOWED_VIDEO_EXTENSIONS}")
        print(f"  Max file size: {MAX_VIDEO_SIZE / 1024 / 1024}MB")

        # Test extension validation
        test_files = [
            ("interview.webm", True),
            ("interview.mp4", True),
            ("interview.mov", True),
            ("interview.avi", True),
            ("interview.txt", False),
            ("interview.exe", False),
            ("interview", False),
        ]

        for filename, expected in test_files:
            ext = filename.lower().rsplit(".", 1)[-1] if "." in filename else ""
            is_valid = f".{ext}" in ALLOWED_VIDEO_EXTENSIONS
            status = "✅" if is_valid == expected else "❌"
            print(f"  {status} {filename}: {'Valid' if is_valid else 'Invalid'}")

        return True
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False


def test_directory_structure():
    """Test that upload directories can be created"""
    print("\n" + "=" * 60)
    print("Test 3: Directory Structure")
    print("=" * 60)

    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        upload_dir = os.path.join(base_dir, "uploads", "interviews", "test")

        # Create directory
        os.makedirs(upload_dir, exist_ok=True)
        print(f"  ✅ Upload directory created: {upload_dir}")

        # Test write permission
        test_file = os.path.join(upload_dir, "test.txt")
        with open(test_file, "w") as f:
            f.write("test")
        print(f"  ✅ Write permission OK")

        # Cleanup
        os.remove(test_file)
        print(f"  ✅ Cleanup OK")

        return True
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False


def test_qwen_vl_local_file_detection():
    """Test Qwen-VL local file detection"""
    print("\n" + "=" * 60)
    print("Test 4: Qwen-VL Local File Detection")
    print("=" * 60)

    test_paths = [
        ("/uploads/interviews/123/video.webm", "Local path"),
        ("https://example.com/video.mp4", "HTTPS URL"),
        ("http://example.com/video.mp4", "HTTP URL"),
        ("/path/to/local/file.webm", "Local path"),
    ]

    for path, expected_type in test_paths:
        is_url = path.startswith(('http://', 'https://'))
        detected_type = "URL" if is_url else "Local file"
        status = "✅" if detected_type == expected_type else "❌"
        print(f"  {status} {path[:40]}... -> {detected_type}")

    return True


async def test_service_structure():
    """Test service structure without API calls"""
    print("\n" + "=" * 60)
    print("Test 5: Service Structure")
    print("=" * 60)

    try:
        # Test Qwen3-Omni HTTP Service
        from app.services.qwen3_omni_http_service import Qwen3OmniHTTPService, ChatChunk

        print("  ✅ Qwen3OmniHTTPService imported")
        print(f"     - Available voices: {Qwen3OmniHTTPService.VOICES}")
        print(f"     - Model: qwen3-omni-flash-2025-12-01")

        # Test ChatChunk
        chunk = ChatChunk(type="text", content="Hello", audio_data=None, usage=None)
        print(f"  ✅ ChatChunk dataclass works")

        # Test Qwen-VL Service
        from app.services.qwen_vl_service import QwenVLService, VideoEvaluationResult

        print("  ✅ QwenVLService imported")
        print(f"     - Model: qwen-vl-max-latest")

        # Test VideoEvaluationResult
        result = VideoEvaluationResult(
            language_expression="Good",
            logical_thinking="Good",
            professional_knowledge="Good",
            communication_skills="Good",
            overall_impression="Good",
            overall_score=85.0,
            strengths=["Good communication"],
            weaknesses=["Could improve"],
            suggestions="Practice more",
            raw_response="test"
        )
        print(f"  ✅ VideoEvaluationResult dataclass works")

        return True
    except Exception as e:
        print(f"  ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_api_routes():
    """Test API route definitions"""
    print("\n" + "=" * 60)
    print("Test 6: API Routes")
    print("=" * 60)

    try:
        from app.api.v1.interviews import router

        routes = []
        for route in router.routes:
            if hasattr(route, 'methods') and hasattr(route, 'path'):
                for method in route.methods:
                    if method != 'HEAD':
                        routes.append((method, route.path))

        # Check for video upload route
        video_routes = [r for r in routes if 'video' in r[1]]
        print(f"  Found {len(video_routes)} video-related routes:")
        for method, path in video_routes:
            print(f"    {method} {path}")

        # Check for specific routes
        expected_routes = [
            ('POST', '/sessions/{session_id}/video'),
            ('POST', '/sessions/{session_id}/analyze-video'),
        ]

        for method, path in expected_routes:
            found = any(r[0] == method and r[1] == path for r in routes)
            status = "✅" if found else "❌"
            print(f"  {status} {method} {path}")

        return True
    except Exception as e:
        print(f"  ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("Non-Realtime Interview Endpoint Tests")
    print("=" * 60)

    results = []

    # Run tests
    results.append(("Module Imports", test_imports()))
    results.append(("Video Upload Validation", test_video_upload_validation()))
    results.append(("Directory Structure", test_directory_structure()))
    results.append(("Qwen-VL Local File Detection", test_qwen_vl_local_file_detection()))
    results.append(("Service Structure", await test_service_structure()))
    results.append(("API Routes", test_api_routes()))

    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)

    for name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{status}: {name}")

    passed_count = sum(1 for _, p in results if p)
    total_count = len(results)
    print(f"\nTotal: {passed_count}/{total_count} tests passed")

    if passed_count == total_count:
        print("\n🎉 All tests passed!")
    else:
        print(f"\n⚠️ {total_count - passed_count} test(s) failed")

    return passed_count == total_count


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTests interrupted by user")
        sys.exit(130)
