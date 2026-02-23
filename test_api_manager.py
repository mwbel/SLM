"""
测试 APIManagerSkill 功能

验证 API 配置与轮询管理是否正常工作
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from src.skills import APIManagerSkill


async def test_api_manager():
    """测试 API 管理器"""
    print("\n" + "="*60)
    print("测试 APIManagerSkill - API 配置与轮询管理")
    print("="*60)

    # 测试 1: 从环境变量加载
    print("\n【测试 1】从环境变量加载 API 配置")
    print("-" * 60)

    manager = APIManagerSkill(
        auto_rotate=True,
        failure_threshold=3,
        cooldown_minutes=5
    )

    print("✅ API 管理器初始化成功")

    # 测试 2: 获取可用 API
    print("\n【测试 2】获取可用的 API")
    print("-" * 60)

    for provider in ['gemini', 'deepseek', 'openai']:
        print(f"\n尝试获取 {provider} API:")
        api = manager.get_available_api(provider)
        if api:
            print(f"  ✅ 获取成功")
            print(f"     API ID: {api['api_id']}")
            print(f"     模型: {api['model']}")
            print(f"     名称: {api.get('name', 'N/A')}")

            # 模拟成功调用
            manager.report_success(api['api_id'])
            print(f"  ✅ 报告调用成功")
        else:
            print(f"  ⚠️  未配置 {provider} API")

    # 测试 3: 轮询机制
    print("\n【测试 3】测试 API 轮询机制")
    print("-" * 60)

    if manager.apis['gemini']:
        print("\n连续获取 Gemini API 3 次（测试轮询）:")
        for i in range(3):
            api = manager.get_available_api('gemini')
            if api:
                print(f"  第 {i+1} 次: {api['api_id']}")
                manager.report_success(api['api_id'])

    # 测试 4: 失败处理和冷却机制
    print("\n【测试 4】测试失败处理和冷却机制")
    print("-" * 60)

    if manager.apis['gemini']:
        api = manager.get_available_api('gemini')
        if api:
            api_id = api['api_id']
            print(f"\n模拟 API 连续失败: {api_id}")

            # 模拟连续失败
            for i in range(4):
                manager.report_failure(api_id, f"测试错误 {i+1}")
                print(f"  第 {i+1} 次失败报告")

            # 尝试再次获取（应该跳过冷却中的 API）
            print("\n尝试获取 API（应跳过冷却中的）:")
            api = manager.get_available_api('gemini')
            if api:
                print(f"  ✅ 获取到其他可用 API: {api['api_id']}")
            else:
                print(f"  ⚠️  所有 API 都不可用")

    # 测试 5: 获取统计信息
    print("\n【测试 5】获取统计信息")
    print("-" * 60)

    result = await manager.run('get_stats')
    if result['success']:
        stats = result['data']
        print(f"\n总体统计:")
        print(f"  总 API 数: {stats['total_apis']}")
        print(f"  总调用数: {stats['total_calls']}")
        print(f"  成功调用: {stats['total_success']}")
        print(f"  失败调用: {stats['total_failed']}")
        print(f"  成功率: {stats['overall_success_rate']}%")

        print(f"\nAPI 详情:")
        for api_detail in stats['api_details']:
            status = "🚫 冷却中" if api_detail['in_cooldown'] else "✅ 活跃"
            print(f"  {status} {api_detail['name']}:")
            print(f"     提供商: {api_detail['provider']}")
            print(f"     调用次数: {api_detail['total_calls']}")
            print(f"     成功率: {api_detail['success_rate']}%")
            print(f"     连续失败: {api_detail['consecutive_failures']}")

    # 测试 6: 保存配置
    print("\n【测试 6】保存配置到文件")
    print("-" * 60)

    config_file = 'config/api_config_test.json'
    manager.save_config(config_file)
    print(f"✅ 配置已保存到: {config_file}")

    # 测试 7: 从配置文件加载
    print("\n【测试 7】从配置文件加载")
    print("-" * 60)

    manager2 = APIManagerSkill(config_file=config_file)
    print("✅ 从配置文件加载成功")

    print("\n" + "="*60)
    print("测试完成")
    print("="*60)


async def test_with_config_file():
    """测试使用配置文件"""
    print("\n" + "="*60)
    print("测试使用配置文件初始化")
    print("="*60)

    # 创建示例配置文件
    config_content = """{
    "gemini": [
        {
            "api_key": "test-gemini-key-1",
            "model": "gemini-1.5-flash",
            "name": "Gemini-Test-1",
            "priority": 1
        },
        {
            "api_key": "test-gemini-key-2",
            "model": "gemini-1.5-flash",
            "name": "Gemini-Test-2",
            "priority": 2
        }
    ],
    "deepseek": [
        {
            "api_key": "test-deepseek-key-1",
            "model": "deepseek-chat",
            "name": "DeepSeek-Test-1",
            "priority": 1
        }
    ]
}"""

    config_file = Path('config/test_api_config.json')
    config_file.parent.mkdir(parents=True, exist_ok=True)
    config_file.write_text(config_content, encoding='utf-8')

    print(f"✅ 创建测试配置文件: {config_file}")

    # 使用配置文件初始化
    manager = APIManagerSkill(config_file=str(config_file))

    # 测试轮询
    print("\n测试 Gemini API 轮询:")
    for i in range(3):
        api = manager.get_available_api('gemini')
        if api:
            print(f"  第 {i+1} 次: {api['name']}")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("APIManagerSkill 功能测试套件")
    print("="*60)

    print("\n提示：")
    print("  - 可以设置环境变量来测试实际 API:")
    print("    export GEMINI_API_KEY='your-key'")
    print("    export GEMINI_API_KEY_1='key1'")
    print("    export GEMINI_API_KEY_2='key2'")
    print("  - 或者使用配置文件测试")

    # 运行测试
    asyncio.run(test_api_manager())

    print("\n")
    asyncio.run(test_with_config_file())
