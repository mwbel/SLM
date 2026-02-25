#!/usr/bin/env python3
"""测试训练好的模型"""

import sys
from pathlib import Path

# 添加src到路径
sys.path.insert(0, str(Path(__file__).parent / "src"))


def test_model():
    """测试训练好的模型"""
    print("=" * 70)
    print("测试训练好的模型")
    print("=" * 70)

    try:
        from inference import ModelInferencer

        # 模型配置 - 使用loss最低的checkpoint 56
        model_path = "outputs/trained_model_checkpoint56"
        base_model = "models/Qwen/Qwen2.5-0.5B"

        print(f"\n模型路径: {model_path}")
        print(f"基座模型: {base_model}")

        print("\n1. 加载模型...")
        inferencer = ModelInferencer(model_path, base_model)
        inferencer.load_model()
        print("   ✓ 模型加载成功")

        # 测试问题 - 使用训练数据中的原始问题
        test_questions = [
            ("对于课题协作费、制作费、材料费、印刷费、测试费、加工费等费用，以及设备采购，华东师范大学对协议和合同的签订金额有什么具体要求？",
             "课题协作费等：3000元以上需协议，10000元以上需合同"),
            ("华东师范大学对办公用品和图书资料的报销有哪些特殊规定？",
             "办公用品500元以上需明细清单，图书30000元以上需附合同"),
            ("同一家单位发票单张多少需要合同？",
             "3000元需要协议，10000元需要合同"),
        ]

        print("\n2. 测试问答...")
        print("   使用温度0.1（更确定性）...")
        for i, (question, expected) in enumerate(test_questions, 1):
            print(f"\n问题 {i}: {question}")
            print(f"预期答案关键点: {expected}")
            response = inferencer.generate(
                question,
                max_new_tokens=300,
                temperature=0.1,  # 降低温度使回答更确定性
                top_p=0.95,
                top_k=50,
                repetition_penalty=1.0,
            )
            print(f"实际回答: {response}")

            # 简单评估
            if "3000" in response and "10000" in response:
                print("✓ 包含关键数字")
            else:
                print("✗ 缺少关键数字")

        print("\n" + "=" * 70)
        print("✅ 测试完成！")
        print("=" * 70)

        return True

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_model()
    sys.exit(0 if success else 1)
