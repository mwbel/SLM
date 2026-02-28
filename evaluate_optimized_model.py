#!/usr/bin/env python3
"""
评估优化后的模型性能 - 使用严格模式
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from test_cases_strict import ALL_STRICT_TEST_CASES, CRITICAL_TEST_CASES
from evaluate_model import ModelEvaluator
import json

def main():
    print("=" * 70)
    print("📊 评估优化后的模型 - 严格模式")
    print("=" * 70)

    # 使用最新的checkpoint
    model_path = "outputs/checkpoint-873"
    base_model = "models/Qwen/Qwen2.5-3B"

    print(f"\n🔵 模型路径: {model_path}")
    print(f"📦 基座模型: {base_model}")

    # 初始化评估器
    print("\n🔵 加载模型...")
    evaluator = ModelEvaluator(
        model_path=model_path,
        base_model=base_model
    )

    try:
        evaluator.load_model()
        print("✅ 模型加载成功")
    except Exception as e:
        print(f"❌ 模型加载失败: {e}")
        return

    # 1. 使用严格模式评估所有测试用例
    print("\n" + "=" * 70)
    print("🔵 严格模式评估 - 所有测试用例")
    print("=" * 70)

    result_all = evaluator.evaluate_accuracy(ALL_STRICT_TEST_CASES, strict_mode=True)

    # 2. 仅评估关键测试用例
    print("\n" + "=" * 70)
    print("🔵 严格模式评估 - 关键测试用例")
    print("=" * 70)

    result_critical = evaluator.evaluate_accuracy(CRITICAL_TEST_CASES, strict_mode=True)

    # 3. 保存结果
    print("\n" + "=" * 70)
    print("💾 保存评估结果")
    print("=" * 70)

    results = {
        "all_tests": result_all,
        "critical_tests": result_critical,
        "model_info": {
            "model_path": model_path,
            "base_model": base_model,
            "training_data": "报销细则_combined.jsonl (863+298条)",
            "optimization": "强调数字类问题"
        }
    }

    output_file = f"evaluation_optimized_{Path(model_path).name}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"✅ 结果已保存到: {output_file}")

    # 4. 打印总结
    print("\n" + "=" * 70)
    print("📊 评估总结")
    print("=" * 70)

    print(f"\n所有测试用例 ({len(ALL_STRICT_TEST_CASES)}个):")
    print(f"  精确度: {result_all['accuracy']*100:.1f}%")
    print(f"  正确数: {result_all['correct_count']}/{len(ALL_STRICT_TEST_CASES)}")
    print(f"  综合评分: {result_all.get('overall_score', 0):.0f}/100")

    print(f"\n关键测试用例 ({len(CRITICAL_TEST_CASES)}个):")
    print(f"  精确度: {result_critical['accuracy']*100:.1f}%")
    print(f"  正确数: {result_critical['correct_count']}/{len(CRITICAL_TEST_CASES)}")
    print(f"  综合评分: {result_critical.get('overall_score', 0):.0f}/100")

    # 计算数字类问题准确率
    all_number_tests = [t for t in ALL_STRICT_TEST_CASES if any(k.strip().isdigit() for k in t['keywords'])]
    if all_number_tests:
        correct_number = sum(1 for r in result_all['detailed_results']
                            if r['is_correct'] and any(k.strip().isdigit() for k in r['expected_keywords']))
        print(f"\n数字类问题 ({len(all_number_tests)}个):")
        print(f"  准确率: {correct_number/len(all_number_tests)*100:.1f}%")
        print(f"  正确数: {correct_number}/{len(all_number_tests)}")

    print("\n" + "=" * 70)
    print("✅ 评估完成！")
    print("=" * 70)

    return results

if __name__ == "__main__":
    main()
