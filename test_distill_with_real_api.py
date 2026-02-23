#!/usr/bin/env python3
"""
使用真实 API keys 测试知识蒸馏功能
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from src.skills import DataDistillerSkill


async def test_distill():
    """测试数据蒸馏功能"""
    print("\n" + "="*60)
    print("测试 DataDistillerSkill - 使用真实 API keys")
    print("="*60)

    # 测试文本（财务报销制度）
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

    print("\n【配置信息】")
    print("-" * 60)
    print(f"API 配置文件: config/api_config.json")
    print(f"API 提供商: gemini")
    print(f"输出文件: data/output/test_real_dataset.jsonl")
    print(f"切片大小: 1000 字符")
    print(f"每片生成: 3 个 QA 对")

    try:
        # 创建蒸馏器（使用真实的 9 个 API keys）
        print("\n【初始化蒸馏器】")
        print("-" * 60)
        distiller = DataDistillerSkill(
            api_provider='gemini',
            api_config_file='config/api_config.json',  # 使用真实的 9 个 keys
            output_file='data/output/test_real_dataset.jsonl',
            chunk_size=1000,
            qa_per_chunk=3,
            max_retries=3
        )
        print("✅ 蒸馏器初始化成功")

        # 执行蒸馏
        print("\n【开始蒸馏】")
        print("-" * 60)
        result = await distiller.run(
            test_content,
            source_file='test_policy.md',
            resume=True
        )

        # 显示结果
        if result['success']:
            data = result['data']
            print("\n" + "="*60)
            print("✅ 蒸馏成功！")
            print("="*60)
            print(f"生成 QA 对: {data['total_qa_pairs']} 个")
            print(f"输出文件: {data['output_file']}")
            print(f"处理块数: {data['chunks_processed']}")
            print(f"API 调用: {data['api_calls']} 次")
            print(f"失败块数: {data['failed_chunks']}")

            # 读取并显示生成的 QA 对
            output_file = Path(data['output_file'])
            if output_file.exists():
                print(f"\n【生成的 QA 对示例】")
                print("-" * 60)
                import json
                with open(output_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    for i, line in enumerate(lines[:3], 1):  # 显示前 3 个
                        qa = json.loads(line)
                        print(f"\nQA 对 #{i}:")
                        print(f"Q: {qa['question']}")
                        print(f"A: {qa['answer'][:100]}..." if len(qa['answer']) > 100 else f"A: {qa['answer']}")
        else:
            print(f"\n❌ 蒸馏失败: {result['error']}")

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("\n提示：此测试将使用真实的 Gemini API keys 进行调用")
    print("确保 config/api_config.json 中配置了有效的 API keys\n")

    asyncio.run(test_distill())
