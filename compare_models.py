#!/usr/bin/env python3
"""
对比测试脚本
对比基座模型和训练后模型的表现差异
"""

import sys
from pathlib import Path

# 添加src到路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

from inference import ModelInferencer


class ModelComparator:
    """模型对比器"""

    def __init__(self, base_model_path: str, trained_model_path: str):
        self.base_model_path = base_model_path
        self.trained_model_path = trained_model_path
        self.base_inferencer = None
        self.trained_inferencer = None

    def load_models(self):
        """加载两个模型"""
        print("=" * 70)
        print("🔄 加载模型")
        print("=" * 70)

        print("\n1️⃣ 加载基座模型（未训练）...")
        self.base_inferencer = ModelInferencer(
            self.base_model_path,
            self.base_model_path
        )
        self.base_inferencer.load_model()
        print("✅ 基座模型加载完成\n")

        print("2️⃣ 加载训练后模型...")
        self.trained_inferencer = ModelInferencer(
            self.trained_model_path,
            self.base_model_path  # 使用相同的基座
        )
        self.trained_inferencer.load_model()
        print("✅ 训练后模型加载完成\n")

    def compare_single_question(
        self,
        question: str,
        expected_keywords: list = None,
        temperature: float = 0.1
    ):
        """
        对比单个问题的回答

        Args:
            question: 测试问题
            expected_keywords: 期望的关键词
            temperature: 生成温度
        """
        print("=" * 70)
        print(f"❓ 问题: {question}")
        print("=" * 70)

        if expected_keywords:
            print(f"📌 期望关键词: {', '.join(expected_keywords)}")

        # 基座模型回答
        print("\n🔵 基座模型回答:")
        base_response = self.base_inferencer.generate(
            question,
            max_new_tokens=300,
            temperature=temperature,
            repetition_penalty=1.0,
        )
        print(f"  {base_response}")

        if expected_keywords:
            base_found = [kw for kw in expected_keywords if kw in base_response]
            print(f"  ✓ 关键词匹配: {', '.join(base_found) if base_found else '无'}")

        # 训练后模型回答
        print("\n🟢 训练后模型回答:")
        trained_response = self.trained_inferencer.generate(
            question,
            max_new_tokens=300,
            temperature=temperature,
            repetition_penalty=1.0,
        )
        print(f"  {trained_response}")

        if expected_keywords:
            trained_found = [kw for kw in expected_keywords if kw in trained_response]
            print(f"  ✓ 关键词匹配: {', '.join(trained_found) if trained_found else '无'}")

        # 对比分析
        print("\n📊 对比分析:")

        # 1. 关键词对比
        if expected_keywords:
            base_coverage = len(base_found) / len(expected_keywords)
            trained_coverage = len(trained_found) / len(expected_keywords)

            print(f"  基座模型关键词覆盖率: {base_coverage*100:.1f}%")
            print(f"  训练后模型关键词覆盖率: {trained_coverage*100:.1f}%")

            if trained_coverage > base_coverage:
                improvement = (trained_coverage - base_coverage) * 100
                print(f"  ✅ 提升: +{improvement:.1f}%")
            elif trained_coverage < base_coverage:
                decline = (base_coverage - trained_coverage) * 100
                print(f"  ⚠️  下降: -{decline:.1f}%")
            else:
                print(f"  ➡️  持平")

        # 2. 回答长度对比
        base_len = len(base_response)
        trained_len = len(trained_response)
        print(f"\n  基座模型回答长度: {base_len} 字符")
        print(f"  训练后模型回答长度: {trained_len} 字符")

        # 3. 内容质量评估（主观）
        print(f"\n💡 主观评估:")
        if trained_coverage > base_coverage:
            print(f"  ✅ 训练后模型在关键词匹配上表现更好")
        elif "华东师大" in trained_response or "华东师范大学" in trained_response:
            print(f"  ✅ 训练后模型更好地适应了领域（华东师范大学）")
        elif base_response == trained_response:
            print(f"  ⚠️  两个模型回答相同，训练效果不明显")
        else:
            print(f"  📝 两个模型回答不同，需人工判断优劣")

        print()

    def compare_batch(
        self,
        test_cases: list,
        temperature: float = 0.1
    ):
        """
        批量对比测试

        Args:
            test_cases: 测试用例列表
            temperature: 生成温度
        """
        print("=" * 70)
        print("📋 批量对比测试")
        print("=" * 70)
        print(f"测试用例数: {len(test_cases)}\n")

        base_better = 0
        trained_better = 0
        tie = 0

        for i, case in enumerate(test_cases, 1):
            question = case["question"]
            keywords = case.get("keywords", [])
            description = case.get("description", f"测试{i}")

            print(f"[{i}/{len(test_cases)}] {description}")
            self.compare_single_question(question, keywords, temperature)

            # 统计（基于关键词覆盖）
            if keywords:
                base_response = self.base_inferencer.generate(
                    question, max_new_tokens=300, temperature=temperature
                )
                trained_response = self.trained_inferencer.generate(
                    question, max_new_tokens=300, temperature=temperature
                )

                base_found = len([kw for kw in keywords if kw in base_response])
                trained_found = len([kw for kw in keywords if kw in trained_response])

                if trained_found > base_found:
                    trained_better += 1
                elif base_found > trained_found:
                    base_better += 1
                else:
                    tie += 1

        # 总结
        total = len(test_cases)
        print("=" * 70)
        print("📊 批量对比总结")
        print("=" * 70)
        print(f"总测试数: {total}")
        print(f"训练后模型更好: {trained_better} ({trained_better/total*100:.1f}%)")
        print(f"基座模型更好: {base_better} ({base_better/total*100:.1f}%)")
        print(f"持平: {tie} ({tie/total*100:.1f}%)")

        if trained_better > base_better:
            print(f"\n✅ 结论: 训练后模型整体表现优于基座模型")
        elif base_better > trained_better:
            print(f"\n⚠️  结论: 基座模型表现更好，需要检查训练配置")
        else:
            print(f"\n➡️  结论: 两个模型表现相当")

        print("=" * 70 + "\n")


def main():
    """主对比流程"""
    print("=" * 70)
    print("⚖️  模型对比测试系统")
    print("=" * 70)
    print()

    # 模型路径
    base_model = "models/Qwen/Qwen2.5-3B"
    trained_model = "outputs/qwen2_5-3b-trained"

    # 初始化对比器
    comparator = ModelComparator(base_model, trained_model)
    comparator.load_models()

    # 测试用例
    test_cases = [
        {
            "question": "对于课题协作费、制作费、材料费等费用，华东师范大学对协议和合同的签订金额有什么具体要求？",
            "keywords": ["3000", "10000", "协议", "合同"],
            "description": "金额阈值记忆测试"
        },
        {
            "question": "差旅费的报销需要提供哪些材料？",
            "keywords": ["审批单", "机票", "发票", "住宿"],
            "description": "差旅费流程测试"
        },
        {
            "question": "办公用品500元以上报销需要提供什么？",
            "keywords": ["明细", "清单", "发票"],
            "description": "办公用品规定测试"
        },
        {
            "question": "华东师范大学财务报销细则的制定目的是什么？",
            "keywords": ["规范", "管理", "资金", "效益"],
            "description": "制度目标测试"
        },
    ]

    # 批量对比
    comparator.compare_batch(test_cases, temperature=0.1)

    # 单个问题深入对比
    print("\n" + "=" * 70)
    print("🔍 深度对比分析")
    print("=" * 70)
    comparator.compare_single_question(
        "请详细说明差旅费报销的完整流程和所需材料",
        expected_keywords=["审批", "机票", "发票", "住宿", "报销"],
        temperature=0.3
    )

    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
