#!/usr/bin/env python3
"""
测试 Qwen-Omni-Realtime API 连接
"""
import asyncio
import os
import sys

import websockets

# 配置
API_KEY = os.getenv("DASHSCOPE_API_KEY")
REGION = os.getenv("DASHSCOPE_REGION", "beijing")

API_ENDPOINTS = {
    "beijing": "wss://dashscope.aliyuncs.com/api-ws/v1/realtime?model=qwen3-omni-flash-realtime",
    "singapore": "wss://dashscope-intl.aliyuncs.com/api-ws/v1/realtime?model=qwen3-omni-flash-realtime",
    "virginia": "wss://dashscope-intl.aliyuncs.com/api-ws/v1/realtime?model=qwen3-omni-flash-realtime",
}


async def test_connection(region, api_url):
    """测试连接到指定区域"""
    print(f"\n🔍 测试连接: {region.upper()}")
    print(f"   端点: {api_url}")

    if not API_KEY:
        print("   ❌ 错误: 未设置 DASHSCOPE_API_KEY")
        return False

    headers = {"Authorization": f"Bearer {API_KEY}"}

    try:
        # 尝试连接
        ws = await asyncio.wait_for(
            websockets.connect(
                api_url, extra_headers=headers, ping_interval=20, ping_timeout=10
            ),
            timeout=10,  # 10秒超时
        )

        print("   ✅ 连接成功！")

        # 关闭连接
        await ws.close()
        return True

    except asyncio.TimeoutError:
        print("   ❌ 连接超时 (>10秒)")
        return False
    except websockets.exceptions.InvalidStatusCode as e:
        print(f"   ❌ HTTP 错误: {e.status_code}")
        if e.status_code == 401:
            print("      可能原因: API Key 无效或不匹配该区域")
        elif e.status_code == 403:
            print("      可能原因: 没有权限访问该区域")
        return False
    except Exception as e:
        print(f"   ❌ 错误: {type(e).__name__}: {e}")
        return False


async def main():
    print("=" * 60)
    print("🚀 Qwen-Omni-Realtime 连接测试工具")
    print("=" * 60)
    print(f"\nAPI Key: {'已设置 ✅' if API_KEY else '未设置 ❌'}")
    print(f"当前区域: {REGION.upper()}")

    if not API_KEY:
        print("\n❌ 请先设置 DASHSCOPE_API_KEY 环境变量")
        print("   export DASHSCOPE_API_KEY='your-api-key-here'")
        sys.exit(1)

    # 测试当前配置的区域
    print("\n" + "=" * 60)
    print("1️⃣ 测试当前配置的区域")
    print("=" * 60)

    current_url = API_ENDPOINTS.get(REGION)
    success = await test_connection(REGION, current_url)

    # 询问是否测试其他区域
    print("\n" + "=" * 60)
    print("2️⃣ 测试所有区域 (可选)")
    print("=" * 60)
    print("\n是否测试所有区域以找到最佳连接？")
    response = input("输入 'y' 继续, 其他键跳过: ").strip().lower()

    if response == "y":
        results = {}
        for region, url in API_ENDPOINTS.items():
            if region != REGION:  # 跳过已测试的
                result = await test_connection(region, url)
                results[region] = result

        print("\n" + "=" * 60)
        print("📊 测试结果汇总")
        print("=" * 60)
        print(f"✅ 当前区域 ({REGION}): {'成功' if success else '失败'}")
        for region, result in results.items():
            status = "✅ 成功" if result else "❌ 失败"
            print(f"{status} {region}: {status}")

    # 建议
    print("\n" + "=" * 60)
    print("💡 建议")
    print("=" * 60)

    if success:
        print(f"✅ 当前配置 ({REGION}) 工作正常，可以直接使用！")
    else:
        print(f"❌ 当前配置 ({REGION}) 无法连接")
        print("\n建议检查：")
        print("1. API Key 是否正确")
        print("2. API Key 是否对应该区域")
        print("3. 网络连接是否正常")
        print("4. 是否需要代理设置")
        print("\n尝试更换区域：")
        print("  export DASHSCOPE_REGION=singapore")
        print("  或")
        print("  export DASHSCOPE_REGION=beijing")

    print("")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 测试已取消")
        sys.exit(0)
