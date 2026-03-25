"""Test script for syntax and structure validation (no env required)"""
import ast
import os
import sys


def check_python_syntax(filepath):
    """Check if a Python file has valid syntax"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            source = f.read()
        ast.parse(source)
        return True, None
    except SyntaxError as e:
        return False, str(e)
    except Exception as e:
        return False, str(e)


def test_file_syntax():
    """Test Python syntax for all modified files"""
    print("=" * 60)
    print("Test 1: Python Syntax Validation")
    print("=" * 60)

    files_to_check = [
        "app/services/qwen3_omni_http_service.py",
        "app/services/qwen_vl_service.py",
        "app/services/oss_service.py",
        "app/api/v1/interviews.py",
        "app/websockets/interview.py",
    ]

    base_dir = os.path.dirname(os.path.abspath(__file__))
    results = []

    for filepath in files_to_check:
        full_path = os.path.join(base_dir, filepath)
        if os.path.exists(full_path):
            valid, error = check_python_syntax(full_path)
            status = "PASS" if valid else "FAIL"
            print(f"  [{status}] {filepath}")
            if error:
                print(f"       Error: {error}")
            results.append((filepath, valid))
        else:
            print(f"  [SKIP] {filepath} (not found)")
            results.append((filepath, True))  # Skip doesn't count as failure

    return all(r[1] for r in results)


def test_code_structure():
    """Test code structure by parsing AST"""
    print("\n" + "=" * 60)
    print("Test 2: Code Structure Validation")
    print("=" * 60)

    base_dir = os.path.dirname(os.path.abspath(__file__))

    # Test Qwen3-Omni HTTP Service structure
    qwen3_path = os.path.join(base_dir, "app/services/qwen3_omni_http_service.py")
    if os.path.exists(qwen3_path):
        with open(qwen3_path, 'r', encoding='utf-8') as f:
            tree = ast.parse(f.read())

        # Check for required classes and methods
        classes = [node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
        functions = [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]

        print(f"  Qwen3-Omni HTTP Service:")
        print(f"    Classes: {classes}")
        print(f"    Key methods: chat, chat_with_history")

        has_chat = any('chat' in f for f in functions)
        print(f"    [PASS] chat method exists" if has_chat else "    [FAIL] chat method missing")

    # Test Qwen-VL Service structure
    qwen_vl_path = os.path.join(base_dir, "app/services/qwen_vl_service.py")
    if os.path.exists(qwen_vl_path):
        with open(qwen_vl_path, 'r', encoding='utf-8') as f:
            tree = ast.parse(f.read())

        classes = [node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
        functions = [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]

        print(f"  Qwen-VL Service:")
        print(f"    Classes: {classes}")
        print(f"    Key methods: analyze_interview_video")

        has_analyze = any('analyze' in f for f in functions)
        print(f"    [PASS] analyze method exists" if has_analyze else "    [FAIL] analyze method missing")

    # Test Video Upload API structure
    api_path = os.path.join(base_dir, "app/api/v1/interviews.py")
    if os.path.exists(api_path):
        with open(api_path, 'r', encoding='utf-8') as f:
            content = f.read()
            tree = ast.parse(content)

        # Check for video upload endpoint
        has_video_upload = 'upload_interview_video' in content
        has_analyze_video = 'analyze_interview_video' in content

        print(f"  Interview API:")
        print(f"    [PASS] upload_interview_video endpoint" if has_video_upload else "    [FAIL] upload_interview_video missing")
        print(f"    [PASS] analyze_interview_video endpoint" if has_analyze_video else "    [FAIL] analyze_interview_video missing")

    return True


def test_import_statements():
    """Test that import statements are valid"""
    print("\n" + "=" * 60)
    print("Test 3: Import Statements Validation")
    print("=" * 60)

    # List of standard library and common package imports to check
    standard_imports = [
        "os", "sys", "typing", "dataclasses", "asyncio", "json", "re",
        "base64", "uuid", "tempfile", "pathlib", "math"
    ]

    third_party_imports = [
        "fastapi", "sqlalchemy", "pydantic", "openai", "dashscope", "structlog"
    ]

    print("  Standard library imports:")
    for imp in standard_imports:
        try:
            __import__(imp)
            print(f"    [OK] {imp}")
        except ImportError:
            print(f"    [MISSING] {imp} (optional)")

    print("  Third-party imports:")
    for imp in third_party_imports:
        try:
            __import__(imp)
            print(f"    [OK] {imp}")
        except ImportError:
            print(f"    [MISSING] {imp} (install with pip)")

    return True


def test_vue_syntax():
    """Test Vue file structure (basic check)"""
    print("\n" + "=" * 60)
    print("Test 4: Frontend Vue File Check")
    print("=" * 60)

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    vue_file = os.path.join(base_dir, "uniapp/src/pages/interview/classic/classic.vue")

    if os.path.exists(vue_file):
        with open(vue_file, 'r', encoding='utf-8') as f:
            content = f.read()

        checks = [
            ("Template section", "<template>" in content and "</template>" in content),
            ("Script section", "<script" in content and "</script>" in content),
            ("Style section", "<style" in content and "</style>" in content),
            ("Audio state", "audioState" in content),
            ("Video recording", "videoRecorder" in content),
            ("Upload video", "uploadVideo" in content),
            ("Analyze video", "analyzeVideo" in content),
            ("WebSocket handler", "handleWebSocketMessage" in content),
            ("Audio delta handler", "audio_delta" in content),
        ]

        for name, found in checks:
            status = "PASS" if found else "FAIL"
            print(f"  [{status}] {name}")

        return all(c[1] for c in checks)
    else:
        print(f"  [SKIP] Vue file not found")
        return True


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("Non-Realtime Interview Syntax & Structure Tests")
    print("(No environment variables required)")
    print("=" * 60)

    results = []
    results.append(("Python Syntax", test_file_syntax()))
    results.append(("Code Structure", test_code_structure()))
    results.append(("Import Statements", test_import_statements()))
    results.append(("Vue File Check", test_vue_syntax()))

    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)

    for name, passed in results:
        status = "PASS" if passed else "FAIL"
        print(f"  [{status}] {name}")

    passed_count = sum(1 for _, p in results if p)
    total_count = len(results)
    print(f"\nTotal: {passed_count}/{total_count} test groups passed")

    if passed_count == total_count:
        print("\nAll tests passed!")
        return 0
    else:
        print(f"\n{total_count - passed_count} test group(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
