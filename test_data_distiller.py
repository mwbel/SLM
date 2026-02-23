"""
测试 DataDistillerSkill 功能

验证数据蒸馏 Skill 是否正常工作
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from src.skills import DataDistillerSkill


async def test_distiller():
    """测试数据蒸馏功能"""

    print("\n" + "="*60)
    print("测试 DataDistillerSkill - 数据蒸馏")
    print("="*60)

    # 测试文本（财务报销制度示例）
    test_content = """
# 财务报销制度

## 一、差旅费报销

### 1.1 出差申请
员工出差前需填写《出差申请单》，注明出差目的、时间、地点和预算。申请单需经部门经理审批后方可出差。

### 1.2 报销标准
- **交通费**：实报实销，需提供正规发票。高铁、飞机需提供行程单。
- **住宿费**：
  - 一线城市（北上广深）：不超过 500 元/天
  - 二线城市：不超过 300 元/天
  - 三线及以下城市：不超过 200 元/天
- **餐费补贴**：100 元/天，无需发票

### 1.3 报销时限
出差结束后 15 个工作日内完成报销，逾期不予受理。

### 1.4 所需材料
1. 出差申请单（需审批）
2. 发票原件
3. 行程单（交通费）
4. 住宿发票

## 二、办公用品报销

### 2.1 采购流程
办公用品由行政部统一采购，个人不得私自采购后报销。

### 2.2 报销标准
每人每月办公用品额度不超过 200 元。

### 2.3 审批流程
部门经理审批 → 财务审核 → 总经理批准

## 三、业务招待费

### 3.1 申请要求
业务招待需提前申请，填写《业务招待申请单》，注明招待对象、人数、预算。

### 3.2 报销标准
- 每人每餐不超过 150 元
- 需提供正规餐饮发票
- 需附招待对象名单

### 3.3 审批权限
- 500 元以下：部门经理审批
- 500-2000 元：副总经理审批
- 2000 元以上：总经理审批
    """

    try:
        # 创建蒸馏器（使用 Gemini，如果没有 API key 会提示）
        print("\n初始化 DataDistillerSkill...")
        print("提示：需要设置环境变量 GEMINI_API_KEY 或 DEEPSEEK_API_KEY")

        distiller = DataDistillerSkill(
            api_provider='gemini',  # 或 'deepseek'
            output_file='data/output/test_dataset.jsonl',
            chunk_size=1000,
            qa_per_chunk=3
        )

        print("✅ 初始化成功")

        # 执行蒸馏
        print("\n开始数据蒸馏...")
        result = await distiller.run(
            test_content,
            source_file='test_policy.md',
            resume=True
        )

        if result['success']:
            data = result['data']
            print(f"\n✅ 蒸馏成功！")
            print(f"   生成 QA 对: {data['total_qa_pairs']} 个")
            print(f"   输出文件: {data['output_file']}")
            print(f"   处理块数: {data['chunks_processed']}")
            print(f"   API 调用: {data['api_calls']} 次")
            print(f"   失败块数: {data['failed_chunks']}")

            # 读取并显示生成的 QA 对
            output_file = Path(data['output_file'])
            if output_file.exists():
                print(f"\n生成的 QA 对示例：")
                with open(output_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    for i, line in enumerate(lines[:3], 1):  # 显示前 3 个
                        import json
                        qa = json.loads(line)
                        print(f"\n  QA {i}:")
                        print(f"  Q: {qa['question']}")
                        print(f"  A: {qa['answer'][:100]}...")
        else:
            print(f"\n❌ 蒸馏失败: {result['error']}")

    except ValueError as e:
        print(f"\n⚠️  配置错误: {e}")
        print("\n请设置 API 密钥：")
        print("  export GEMINI_API_KEY='your-api-key'")
        print("  或")
        print("  export DEEPSEEK_API_KEY='your-api-key'")
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_distiller())
