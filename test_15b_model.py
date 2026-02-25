#!/usr/bin/env python3
"""
测试 Qwen2.5-1.5B 模型的训练效果
对比训练前后的回答质量
"""

import sys
from pathlib import Path

# 添加src到路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

from inference import ModelInferencer


def test_model():
    """测试训练好的模型"""

    print("=" * 70)
    print("测试 Qwen2.5-1.5B 模型效果")
    print("=" * 70)

    # 模型路径
    model_path = "outputs/trained_model_15b"
    base_model = "models/Qwen/Qwen2.5-1.5B"

    # 测试问题集（来自原始训练数据）
    test_cases = [
        {
            "question": "对于课题协作费、制作费、材料费、印刷费、测试费、加工费等费用，以及设备采购，华东师范大学对协议和合同的签订金额有什么具体要求？",
            "expected_keywords": ["3000", "协议", "10000", "合同", "30000", "设备"],
            "description": "测试金额记忆准确性"
        },
        {
            "question": "同一家单位发票单张或累计金额达到多少元需要协议？多少元需要合同？",
            "expected_keywords": ["3000", "协议", "10000", "合同"],
            "description": "测试协议和合同金额门槛"
        },
        {
            "question": "如果只有一家以上(含)不同客户的单位共同申请报销费用，如何处理？",
            "expected_keywords": ["分别", "协议", "合同"],
            "description": "测试多客户报销规则"
        },
        {
            "question": "购买物品为设备时，协议和合同的金额要求是多少？",
            "expected_keywords": ["10000", "协议", "30000", "合同"],
            "description": "测试设备采购特殊规定"
        },
    ]

    try:
        print(f"\n正在加载模型...")
        print(f"  模型路径: {model_path}")
        print(f"  基座模型: {base_model}")

        # 初始化推理器
        inferencer = ModelInferencer(model_path, base_model)
        inferencer.load_model()

        print("\n" + "=" * 70)
        print("开始测试...")
        print("=" * 70)

        # 统计结果
        total_tests = len(test_cases)
        passed_tests = 0

        for i, test_case in enumerate(test_cases, 1):
            question = test_case["question"]
            expected_keywords = test_case["expected_keywords"]
            description = test_case["description"]

            print(f"\n{'=' * 70}")
            print(f"测试 {i}/{total_tests}: {description}")
            print(f"{'=' * 70}")
            print(f"\n问题: {question}")

            # 生成回答（使用较低温度以获得更确定的结果）
            response = inferencer.generate(
                question,
                max_new_tokens=300,
                temperature=0.1,  # 低温度，减少随机性
                top_p=0.95,
                repetition_penalty=1.1,
            )

            print(f"\n回答: {response}")

            # 检查是否包含关键词
            found_keywords = []
            missing_keywords = []

            for keyword in expected_keywords:
                if keyword in response:
                    found_keywords.append(keyword)
                else:
                    missing_keywords.append(keyword)

            # 判断是否通过
            passed = len(found_keywords) >= len(expected_keywords) * 0.6  # 60%关键词出现即可

            if passed:
                passed_tests += 1
                print(f"\n✅ 通过")
            else:
                print(f"\n❌ 未通过")

            print(f"  找到关键词: {', '.join(found_keywords) if found_keywords else '无'}")
            print(f"  缺失关键词: {', '.join(missing_keywords) if missing_keywords else '无'}")
            print(f"  关键词覆盖率: {len(found_keywords)}/{len(expected_keywords)} ({len(found_keywords)/len(expected_keywords)*100:.1f}%)")

        # 总结
        print("\n" + "=" * 70)
        print("测试总结")
        print("=" * 70)
        print(f"\n总测试数: {total_tests}")
        print(f"通过数: {passed_tests}")
        print(f"失败数: {total_tests - passed_tests}")
        print(f"通过率: {passed_tests/total_tests*100:.1f}%")

        # 与 0.5B 模型对比
        print("\n" + "-" * 70)
        print("与 0.5B 模型对比")
        print("-" * 70)
        print("0.5B 模型通过率: 0% (0/3)")
        print(f"1.5B 模型通过率: {passed_tests/total_tests*100:.1f}% ({passed_tests}/{total_tests})")

        if passed_tests >= total_tests * 0.5:
            print("\n🎉 1.5B 模型显著优于 0.5B 模型！")
            print("   升级基座模型有效解决了模型容量不足的问题。")
        elif passed_tests > 0:
            print("\n✅ 1.5B 模型有所改进，但仍需优化。")
            print("   建议：增加训练数据量（当前217条，建议500-1000条）")
        else:
            print("\n⚠️  1.5B 模型仍未达到预期效果。")
            print("   可能原因：")
            print("   1. 训练数据量不足（217条较少）")
            print("   2. 训练参数需要调整")
            print("   3. 需要更多训练轮次")

        return passed_tests >= total_tests * 0.5

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_model()

    print("\n下一步建议:")
    if success:
        print("  1. ✅ 1.5B 模型效果良好，可以用于生产环境")
        print("  2. 考虑增加更多训练数据以进一步提升效果")
        print("  3. 可以尝试在其他领域应用此方案")
    else:
        print("  1. 📊 增加训练数据量（当前217条 → 目标500-1000条）")
        print("  2. 🔧 调整训练参数（学习率、轮数、LoRA rank）")
        print("  3. 📝 检查训练数据质量")
        print("  4. 🔄 考虑使用更大的模型（如3B）")
