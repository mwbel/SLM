#!/usr/bin/env python3
"""测试训练好的模型"""

import sys
from pathlib import Path

# 添加src到路径
sys.path.insert(0, str(Path(__file__).parent / "src"))


def test_model():
    """测试训练好的模型"""
    print("=" * 70)
    print("测试 Qwen2.5-3B 训练模型")
    print("=" * 70)

    try:
        from inference import ModelInferencer

        # 模型配置 - 使用刚训练好的3B模型
        model_path = "outputs/qwen2_5-3b-trained"
        base_model = "models/Qwen/Qwen2.5-3B"

        print(f"\n模型路径: {model_path}")
        print(f"基座模型: {base_model}")

        print("\n1. 加载模型...")
        inferencer = ModelInferencer(model_path, base_model)
        inferencer.load_model()
        print("   ✓ 模型加载成功")

        # 测试问题 - 基于华东师范大学财务报销细则
        test_questions = [
            {
                "question": "对于课题协作费、制作费、材料费等费用，以及设备采购，华东师范大学对协议和合同的签订金额有什么具体要求？",
                "keywords": ["3000", "10000", "协议", "合同"],
                "description": "测试金额阈值记忆"
            },
            {
                "question": "华东师范大学对办公用品和图书资料的报销有哪些特殊规定？",
                "keywords": ["500", "明细清单", "30000", "图书"],
                "description": "测试办公用品和图书规定"
            },
            {
                "question": "差旅费的报销需要提供哪些材料？",
                "keywords": ["审批单", "机票", "发票", "住宿"],
                "description": "测试差旅费报销流程"
            },
            {
                "question": "会议费报销需要什么审批流程？",
                "keywords": ["会议", "审批", "通知", "签到"],
                "description": "测试会议费规定"
            },
        ]

        print("\n2. 测试问答能力...")
        print("   使用温度0.1（更确定性的回答）...")
        print("   " + "=" * 66)

        correct_count = 0
        for i, test_case in enumerate(test_questions, 1):
            question = test_case["question"]
            keywords = test_case["keywords"]
            description = test_case["description"]

            print(f"\n问题 {i}: {description}")
            print(f"问题: {question}")
            print(f"预期关键词: {', '.join(keywords)}")

            response = inferencer.generate(
                question,
                max_new_tokens=300,
                temperature=0.1,  # 降低温度使回答更确定性
                top_p=0.95,
                top_k=50,
                repetition_penalty=1.0,
            )
            print(f"\n模型回答: {response}")

            # 评估关键词覆盖
            found_keywords = []
            missing_keywords = []
            for kw in keywords:
                if kw in response:
                    found_keywords.append(kw)
                else:
                    missing_keywords.append(kw)

            print(f"\n关键词检查:")
            print(f"  ✓ 找到: {', '.join(found_keywords) if found_keywords else '无'}")
            if missing_keywords:
                print(f"  ✗ 缺少: {', '.join(missing_keywords)}")

            # 判断是否合格（至少包含一半关键词）
            if len(found_keywords) >= len(keywords) / 2:
                print(f"  ✅ 合格")
                correct_count += 1
            else:
                print(f"  ❌ 不合格")

            print("-" * 70)

        # 总结
        print("\n" + "=" * 70)
        print("📊 测试总结")
        print("=" * 70)
        print(f"总问题数: {len(test_questions)}")
        print(f"合格数: {correct_count}")
        print(f"合格率: {correct_count/len(test_questions)*100:.1f}%")
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
