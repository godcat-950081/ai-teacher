"""
测试模块化代码结构
验证所有导入和基本功能
"""


def test_imports():
    """测试所有模块是否可以正常导入"""
    print("🧪 Testing module imports...")

    try:
        from services.qwen_client import QwenRealtimeClient

        print("  ✅ services.qwen_client")
    except Exception as e:
        print(f"  ❌ services.qwen_client: {e}")
        return False

    try:
        from services.lesson_service import (
            create_lesson_plan,
            extract_lesson_info,
            parse_structured_lesson,
        )

        print("  ✅ services.lesson_service")
    except Exception as e:
        print(f"  ❌ services.lesson_service: {e}")
        return False

    try:
        from handlers.stage_handler import get_system_prompt, handle_stage_switch

        print("  ✅ handlers.stage_handler")
    except Exception as e:
        print(f"  ❌ handlers.stage_handler: {e}")
        return False

    try:
        from routes.lesson_routes import lesson_routes

        print("  ✅ routes.lesson_routes")
    except Exception as e:
        print(f"  ❌ routes.lesson_routes: {e}")
        return False

    try:
        from routes.websocket_routes import register_websocket_routes

        print("  ✅ routes.websocket_routes")
    except Exception as e:
        print(f"  ❌ routes.websocket_routes: {e}")
        return False

    return True


def test_app_creation():
    """测试应用创建"""
    print("\n🧪 Testing app creation...")

    try:
        from app import app

        print(f"  ✅ App created successfully")

        # 检查路由
        routes = [rule.rule for rule in app.url_map.iter_rules()]
        expected_routes = [
            "/",
            "/api/lessons",
            "/api/lessons/<lesson_id>",
            "/api/lessons/<lesson_id>/prepare",
            "/tutor/<lesson_id>",
            "/api/lessons/<lesson_id>/plan",
            "/ws/tutor/<lesson_id>",
        ]

        for route in expected_routes:
            if route in routes:
                print(f"  ✅ Route registered: {route}")
            else:
                print(f"  ❌ Route missing: {route}")
                return False

        return True
    except Exception as e:
        print(f"  ❌ App creation failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_lesson_parsing():
    """测试课程内容解析"""
    print("\n🧪 Testing lesson parsing...")

    from services.lesson_service import parse_structured_lesson

    test_input = """
    单词：indigenous, fluent, Sweden

    文章：Gordon lives in Sweden and his wife Chris is learning Swedish.

    练习：
    1. Where does Gordon live?
    2. What language is Chris learning?
    """

    try:
        result = parse_structured_lesson(test_input)

        if len(result["vocabulary"]) >= 3:
            print(f"  ✅ Vocabulary parsed: {result['vocabulary']}")
        else:
            print(f"  ❌ Vocabulary parsing failed: {result['vocabulary']}")
            return False

        if len(result["articles"]) > 0:
            print(f"  ✅ Article parsed: {result['articles'][0][:50]}...")
        else:
            print(f"  ❌ Article parsing failed")
            return False

        if len(result["questions"]) >= 2:
            print(f"  ✅ Questions parsed: {len(result['questions'])} questions")
        else:
            print(f"  ❌ Questions parsing failed: {result['questions']}")
            return False

        return True
    except Exception as e:
        print(f"  ❌ Parsing failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_system_prompt():
    """测试系统提示词"""
    print("\n🧪 Testing system prompt...")

    from handlers.stage_handler import get_system_prompt

    try:
        prompt = get_system_prompt()
        if "English teacher" in prompt and "SHORT" in prompt:
            print(f"  ✅ System prompt generated (length: {len(prompt)})")
            return True
        else:
            print(f"  ❌ System prompt invalid")
            return False
    except Exception as e:
        print(f"  ❌ System prompt failed: {e}")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("🚀 Running modular code structure tests")
    print("=" * 60)

    results = []

    # 运行所有测试
    results.append(("Module Imports", test_imports()))
    results.append(("App Creation", test_app_creation()))
    results.append(("Lesson Parsing", test_lesson_parsing()))
    results.append(("System Prompt", test_system_prompt()))

    # 汇总结果
    print("\n" + "=" * 60)
    print("📊 Test Results Summary")
    print("=" * 60)

    passed = 0
    for name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{name:.<40} {status}")
        if result:
            passed += 1

    print("=" * 60)
    print(f"Total: {passed}/{len(results)} tests passed")

    if passed == len(results):
        print("🎉 All tests passed! Code structure is working correctly.")
        exit(0)
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
        exit(1)
