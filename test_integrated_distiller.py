"""
测试集成 APIManagerSkill 的 DataDistillerSkill

验证 API 管理器集成是否正常工作
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from src.skills import DataDistillerSkill, APIManagerSkill


async def test_integrated_distiller():
    """测试集成了 API 管理器的数据蒸馏器"""
    print("\n" + "="*60)
    print("测试集成 APIManagerSkill 的 DataDistillerSkill")
    print("="*60)

    # 测试文本
    test_content = """
# 财务报销制度

## 差旅费报销

### 出差申请
员工出差前需填写《出差申请单》，经部门经理审批后方可出差。

### 报销标准
- 交通费：实报实销，需提供发票
- 住宿费：一线城市不超过500元/天，二线城市不超过300元/天
- 餐费：100元/天

### 报销时限
出差结束后15个工作日内完成报销

### 所需材料
1. 出差申请单
2. 发票原件
3. 行程单
    """

    print("\n【方式 1】自动创建 API 管理器")
    print("-" * 60)

    try:
        # DataDistillerSkill 会自动创建 API 管理器
        distiller1 = DataDistillerSkill(
            api_provider='gemini',
            output_file='data/output/test_dataset_1.jsonl',
            chunk_size=1000,
            qa_per_chunk=3
        )

        print("✅ DataDistillerSkill 初始化成功（自动创建 API 管理器）")

        # 执行蒸馏
        result = await distiller1.run(
            test_content,
            source_file='test_policy.md',
            resume=True
        )

        if result['success']:
            data = result['data']
            print(f"\n✅ 蒸馏成功！")
            print(f"   生成 QA 对: {data['total_qa_pairs']} 个")
            print(f"   API 调用: {data['api_calls']} 次")

    except Exception as e:
        print(f"\n⚠️  测试失败: {e}")
        print("   提示：需要设置环境变量 GEMINI_API_KEY 或 DEEPSEEK_API_KEY")

    print("\n【方式 2】使用共享的 API 管理器")
    print("-" * 60)

    try:
        # 创建共享的 API 管理器
        api_manager = APIManagerSkill(
            auto_rotate=True,
            failure_threshold=2,
            cooldown_minutes=3
        )

        print("✅ 创建共享 API 管理器")

        # 创建多个 DataDistillerSkill 实例，共享同一个 API 管理器
        distiller2 = DataDistillerSkill(
            api_manager=api_manager,
            api_provider='gemini',
            output_file='data/output/test_dataset_2.jsonl',
            chunk_size=1000,
            qa_per_chunk=2
        )

        print("✅ DataDistillerSkill 初始化成功（使用共享 API 管理器）")

        # 执行蒸馏
        result = await distiller2.run(
            test_content,
            source_file='test_policy_2.md',
            resume=True
        )

        if result['success']:
            data = result['data']
            print(f"\n✅ 蒸馏成功！")
            print(f"   生成 QA 对: {data['total_qa_pairs']} 个")
            print(f"   API 调用: {data['api_calls']} 次")

        # 查看 API 管理器统计
        print("\n【API 管理器统计】")
        print("-" * 60)
        stats_result = await api_manager.run('get_stats')
        if stats_result['success']:
            stats = stats_result['data']
            print(f"总调用数: {stats['total_calls']}")
            print(f"成功率: {stats['overall_success_rate']}%")
            print(f"\nAPI 详情:")
            for api_detail in stats['api_details']:
                print(f"  - {api_detail['name']}: {api_detail['total_calls']} 次调用")

    except Exception as e:
        print(f"\n⚠️  测试失败: {e}")
        print("   提示：需要设置环境变量 GEMINI_API_KEY 或 DEEPSEEK_API_KEY")

    print("\n【方式 3】使用配置文件")
    print("-" * 60)

    # 创建测试配置文件
    config_content = """{
    "gemini": [
        {
            "api_key": "test-key-1",
            "model": "gemini-1.5-flash",
            "name": "Gemini-Test-1",
            "priority": 1
        }
    ]
}"""

    config_file = Path('config/test_distiller_api.json')
    config_file.parent.mkdir(parents=True, exist_ok=True)
    config_file.write_text(config_content, encoding='utf-8')

    print(f"✅ 创建测试配置文件: {config_file}")

    try:
        distiller3 = DataDistillerSkill(
            api_provider='gemini',
            api_config_file=str(config_file),
            output_file='data/output/test_dataset_3.jsonl',
            chunk_size=1000,
            qa_per_chunk=2
        )

        print("✅ DataDistillerSkill 初始化成功（使用配置文件）")
        print("   注意：使用测试配置，实际调用会失败（测试密钥无效）")

    except Exception as e:
        print(f"⚠️  初始化失败: {e}")

    print("\n" + "="*60)
    print("测试完成")
    print("="*60)


async def test_api_rotation():
    """测试 API 轮询功能"""
    print("\n" + "="*60)
    print("测试 API 轮询和故障转移")
    print("="*60)

    # 创建配置文件（多个 API）
    config_content = """{
    "gemini": [
        {
            "api_key": "key-1",
            "model": "gemini-1.5-flash",
            "name": "Gemini-Account-1",
            "priority": 1
        },
        {
            "api_key": "key-2",
            "model": "gemini-1.5-flash",
            "name": "Gemini-Account-2",
            "priority": 1
        }
    ]
}"""

    config_file = Path('config/test_rotation_api.json')
    config_file.parent.mkdir(parents=True, exist_ok=True)
    config_file.write_text(config_content, encoding='utf-8')

    print(f"✅ 创建多 API 配置文件: {config_file}")

    # 创建 API 管理器
    api_manager = APIManagerSkill(
        config_file=str(config_file),
        auto_rotate=True
    )

    print("\n测试 API 轮询:")
    for i in range(4):
        api = api_manager.get_available_api('gemini')
        if api:
            print(f"  第 {i+1} 次: {api['name']}")

    print("\n✅ API 轮询测试完成")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("DataDistillerSkill + APIManagerSkill 集成测试")
    print("="*60)

    print("\n提示：")
    print("  - 设置环境变量来测试实际功能:")
    print("    export GEMINI_API_KEY='your-key'")
    print("    export GEMINI_API_KEY_1='key1'")
    print("    export GEMINI_API_KEY_2='key2'")
    print("  - 或者使用配置文件")

    # 运行测试
    asyncio.run(test_integrated_distiller())

    print("\n")
    asyncio.run(test_api_rotation())
