#!/usr/bin/env python3
"""
测试 lesson_manager 的阶段提示词功能
"""

from lesson_manager import lesson_manager


def test_stage_prompts():
    """测试各个阶段的提示词"""

    stages = ["vocabulary", "article", "question", "review"]

    print("=" * 80)
    print("测试阶段提示词功能")
    print("=" * 80)

    for stage in stages:
        print(f"\n{'='*80}")
        print(f"阶段: {stage.upper()}")
        print(f"{'='*80}")
        try:
            prompt = lesson_manager.get_stage_prompt(stage)
            print(prompt)
            print(f"\n✅ {stage} 阶段提示词获取成功")
        except Exception as e:
            print(f"\n❌ {stage} 阶段提示词获取失败: {e}")

    # 测试无效阶段
    print(f"\n{'='*80}")
    print("测试: 无效阶段")
    print(f"{'='*80}")
    try:
        prompt = lesson_manager.get_stage_prompt("invalid_stage")
        print("❌ 应该抛出 ValueError")
    except ValueError as e:
        print(f"✅ 正确抛出 ValueError: {e}")

    # 测试完整系统提示
    print(f"\n{'='*80}")
    print("完整系统提示（包含所有阶段）")
    print(f"{'='*80}")
    full_prompt = lesson_manager._get_tutor_system_prompt()
    print(f"提示词长度: {len(full_prompt)} 字符")
    print(f"提示词行数: {len(full_prompt.splitlines())} 行")
    print("\n✅ 完整系统提示获取成功")


if __name__ == "__main__":
    test_stage_prompts()
