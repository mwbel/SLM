#!/usr/bin/env python3
"""
自动化模型评估脚本
提供多维度、多指标的模型效果评估
"""

import sys
import json
from pathlib import Path
from datetime import datetime
import random

# 添加src到路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

from inference import ModelInferencer


class ModelEvaluator:
    """模型评估器"""

    def __init__(self, model_path: str, base_model: str):
        self.model_path = model_path
        self.base_model = base_model
        self.inferencer = None
        self.results = []

    def load_model(self):
        """加载模型"""
        print(f"正在加载模型: {self.model_path}")
        self.inferencer = ModelInferencer(self.model_path, self.base_model)
        self.inferencer.load_model()
        print("✅ 模型加载完成\n")

    def evaluate_accuracy(
        self,
        test_cases: list,
        temperature: float = 0.1
    ) -> dict:
        """
        精确度评估 - 基于关键词匹配

        Args:
            test_cases: 测试用例列表 [{"question": "", "keywords": [], "description": ""}]
            temperature: 生成温度

        Returns:
            评估结果字典
        """
        print("=" * 70)
        print("📊 精确度评估")
        print("=" * 70)

        correct_count = 0
        total_count = len(test_cases)
        detailed_results = []

        for i, case in enumerate(test_cases, 1):
            question = case["question"]
            keywords = case["keywords"]
            description = case.get("description", "")

            print(f"\n[{i}/{total_count}] {description}")
            print(f"问题: {question}")
            print(f"预期关键词: {', '.join(keywords)}")

            # 生成回答
            response = self.inferencer.generate(
                question,
                max_new_tokens=300,
                temperature=temperature,
                top_p=0.95,
                repetition_penalty=1.0,
            )

            print(f"模型回答: {response}")

            # 关键词匹配
            found_keywords = [kw for kw in keywords if kw in response]
            missing_keywords = [kw for kw in keywords if kw not in response]

            # 计算得分
            keyword_coverage = len(found_keywords) / len(keywords) if keywords else 0

            print(f"\n关键词匹配:")
            print(f"  ✓ 找到 ({len(found_keywords)}/{len(keywords)}): {', '.join(found_keywords)}")
            if missing_keywords:
                print(f"  ✗ 缺少 ({len(missing_keywords)}): {', '.join(missing_keywords)}")

            # 判断是否合格（至少包含50%关键词）
            is_correct = keyword_coverage >= 0.5
            if is_correct:
                correct_count += 1
                print(f"  ✅ 合格 (覆盖率: {keyword_coverage*100:.1f}%)")
            else:
                print(f"  ❌ 不合格 (覆盖率: {keyword_coverage*100:.1f}%)")

            # 保存详细结果
            detailed_results.append({
                "question": question,
                "description": description,
                "expected_keywords": keywords,
                "found_keywords": found_keywords,
                "missing_keywords": missing_keywords,
                "keyword_coverage": keyword_coverage,
                "response": response,
                "is_correct": is_correct
            })

            print("-" * 70)

        # 总结
        accuracy = correct_count / total_count if total_count > 0 else 0
        avg_coverage = sum(r["keyword_coverage"] for r in detailed_results) / total_count

        print("\n" + "=" * 70)
        print("📈 精确度评估总结")
        print("=" * 70)
        print(f"总测试数: {total_count}")
        print(f"合格数: {correct_count}")
        print(f"合格率: {accuracy*100:.1f}%")
        print(f"平均关键词覆盖率: {avg_coverage*100:.1f}%")
        print("=" * 70 + "\n")

        return {
            "type": "accuracy",
            "total": total_count,
            "correct": correct_count,
            "accuracy": accuracy,
            "avg_coverage": avg_coverage,
            "detailed_results": detailed_results
        }

    def evaluate_diversity(
        self,
        test_questions: list,
        num_samples: int = 3
    ) -> dict:
        """
        多样性评估 - 测试模型对同一问题的回答多样性

        Args:
            test_questions: 测试问题列表
            num_samples: 每个问题生成次数

        Returns:
            多样性评估结果
        """
        print("=" * 70)
        print("🎨 多样性评估")
        print("=" * 70)
        print(f"每个问题生成 {num_samples} 次回答（温度=0.7）\n")

        diversity_scores = []

        for i, question in enumerate(test_questions, 1):
            print(f"[{i}/{len(test_questions)}] 问题: {question}")

            # 生成多个回答
            responses = []
            for j in range(num_samples):
                response = self.inferencer.generate(
                    question,
                    max_new_tokens=200,
                    temperature=0.7,  # 提高温度以增加多样性
                    top_p=0.95,
                    repetition_penalty=1.0,
                )
                responses.append(response)
                print(f"  回答{j+1}: {response[:100]}...")

            # 计算多样性（简单方法：比较回答长度差异）
            lengths = [len(r) for r in responses]
            avg_length = sum(lengths) / len(lengths)
            length_variance = sum((l - avg_length) ** 2 for l in lengths) / len(lengths)

            diversity_score = min(length_variance / 1000, 1.0)  # 归一化到[0,1]
            diversity_scores.append(diversity_score)

            print(f"  多样性得分: {diversity_score:.3f}")
            print("-" * 70)

        avg_diversity = sum(diversity_scores) / len(diversity_scores)

        print("\n" + "=" * 70)
        print("🎨 多样性评估总结")
        print("=" * 70)
        print(f"平均多样性得分: {avg_diversity:.3f}")
        print(f"得分说明: 0=回答完全相同, 1=回答差异很大")
        print("=" * 70 + "\n")

        return {
            "type": "diversity",
            "avg_diversity": avg_diversity,
            "scores": diversity_scores
        }

    def evaluate_consistency(
        self,
        test_questions: list,
        num_samples: int = 3
    ) -> dict:
        """
        一致性评估 - 测试模型对同一问题回答的稳定性

        Args:
            test_questions: 测试问题列表
            num_samples: 每个问题生成次数

        Returns:
            一致性评估结果
        """
        print("=" * 70)
        print("🎯 一致性评估")
        print("=" * 70)
        print(f"每个问题生成 {num_samples} 次回答（温度=0.1）\n")

        consistency_scores = []

        for i, question in enumerate(test_questions, 1):
            print(f"[{i}/{len(test_questions)}] 问题: {question}")

            # 生成多个回答（使用低温度）
            responses = []
            for j in range(num_samples):
                response = self.inferencer.generate(
                    question,
                    max_new_tokens=200,
                    temperature=0.1,  # 低温度以保持一致性
                    top_p=0.95,
                    repetition_penalty=1.0,
                )
                responses.append(response)
                print(f"  回答{j+1}: {response[:100]}...")

            # 计算一致性（简单方法：比较回答的相似度）
            # 这里使用关键词相似度
            all_words = set()
            for r in responses:
                all_words.update(r.split())

            similarities = []
            for word in all_words:
                count = sum(1 for r in responses if word in r)
                if count == num_samples:  # 所有回答都包含这个词
                    similarities.append(1)
                elif count > 0:
                    similarities.append(count / num_samples)

            consistency = sum(similarities) / len(similarities) if similarities else 0
            consistency_scores.append(consistency)

            print(f"  一致性得分: {consistency:.3f}")
            print("-" * 70)

        avg_consistency = sum(consistency_scores) / len(consistency_scores)

        print("\n" + "=" * 70)
        print("🎯 一致性评估总结")
        print("=" * 70)
        print(f"平均一致性得分: {avg_consistency:.3f}")
        print(f"得分说明: 0=完全不一致, 1=完全一致")
        print("=" * 70 + "\n")

        return {
            "type": "consistency",
            "avg_consistency": avg_consistency,
            "scores": consistency_scores
        }

    def evaluate_on_test_set(
        self,
        test_data_file: str,
        sample_size: int = 20
    ) -> dict:
        """
        在测试集上评估

        Args:
            test_data_file: 测试数据文件路径（JSONL格式）
            sample_size: 采样数量

        Returns:
            测试集评估结果
        """
        print("=" * 70)
        print("📚 测试集评估")
        print("=" * 70)

        # 加载测试数据
        test_data_path = Path(test_data_file)
        if not test_data_path.exists():
            print(f"⚠️  测试数据文件不存在: {test_data_path}")
            return {}

        with open(test_data_path, 'r', encoding='utf-8') as f:
            all_data = [json.loads(line.strip()) for line in f if line.strip()]

        # 随机采样
        if len(all_data) > sample_size:
            sampled_data = random.sample(all_data, sample_size)
        else:
            sampled_data = all_data

        print(f"从 {len(all_data)} 条数据中采样 {len(sampled_data)} 条\n")

        correct_count = 0
        for i, item in enumerate(sampled_data, 1):
            question = item.get("instruction", "")
            expected_answer = item.get("output", "")

            print(f"[{i}/{len(sampled_data)}] {question[:60]}...")

            # 生成回答
            response = self.inferencer.generate(
                question,
                max_new_tokens=300,
                temperature=0.1,
            )

            # 简单相似度评估（基于词重叠）
            response_words = set(response.split())
            expected_words = set(expected_answer.split())

            overlap = len(response_words & expected_words)
            union = len(response_words | expected_words)
            similarity = overlap / union if union > 0 else 0

            print(f"  预期: {expected_answer[:80]}...")
            print(f"  实际: {response[:80]}...")
            print(f"  相似度: {similarity:.3f}")

            if similarity >= 0.3:  # 阈值可调整
                correct_count += 1
                print(f"  ✅ 合格")
            else:
                print(f"  ❌ 不合格")

            print("-" * 70)

        accuracy = correct_count / len(sampled_data)

        print("\n" + "=" * 70)
        print("📚 测试集评估总结")
        print("=" * 70)
        print(f"测试样本数: {len(sampled_data)}")
        print(f"合格数: {correct_count}")
        print(f"合格率: {accuracy*100:.1f}%")
        print("=" * 70 + "\n")

        return {
            "type": "test_set",
            "sample_size": len(sampled_data),
            "correct": correct_count,
            "accuracy": accuracy
        }

    def save_report(self, results: list, output_file: str = None):
        """保存评估报告"""
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"evaluation_report_{timestamp}.json"

        report = {
            "timestamp": datetime.now().isoformat(),
            "model_path": self.model_path,
            "base_model": self.base_model,
            "evaluations": results
        }

        output_path = Path(output_file)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        print(f"📄 评估报告已保存: {output_path}")


def main():
    """主评估流程"""
    print("=" * 70)
    print("🔬 模型效果评估系统")
    print("=" * 70)
    print()

    # 模型配置
    model_path = "outputs/qwen2_5-3b-trained"
    base_model = "models/Qwen/Qwen2.5-3B"

    # 初始化评估器
    evaluator = ModelEvaluator(model_path, base_model)
    evaluator.load_model()

    all_results = []

    # 1. 精确度评估
    accuracy_test_cases = [
        {
            "question": "对于课题协作费、制作费、材料费等费用，华东师范大学对协议和合同的签订金额有什么具体要求？",
            "keywords": ["3000", "10000", "协议", "合同"],
            "description": "金额阈值测试"
        },
        {
            "question": "华东师范大学对办公用品的报销有哪些特殊规定？",
            "keywords": ["500", "明细清单", "发票"],
            "description": "办公用品规定测试"
        },
        {
            "question": "差旅费的报销需要提供哪些材料？",
            "keywords": ["审批单", "机票", "发票", "住宿"],
            "description": "差旅费流程测试"
        },
        {
            "question": "图书资料报销在什么金额以上需要附合同？",
            "keywords": ["30000", "合同", "图书"],
            "description": "图书采购测试"
        },
        {
            "question": "会议费报销需要提供哪些审批材料？",
            "keywords": ["会议通知", "签到", "审批"],
            "description": "会议费测试"
        },
    ]

    accuracy_result = evaluator.evaluate_accuracy(accuracy_test_cases)
    all_results.append(accuracy_result)

    # 2. 多样性评估
    diversity_questions = [
        "请说明差旅费的报销流程",
        "华东师范大学对办公用品报销有什么规定？"
    ]

    diversity_result = evaluator.evaluate_diversity(diversity_questions, num_samples=3)
    all_results.append(diversity_result)

    # 3. 一致性评估
    consistency_questions = [
        "课题协作费在什么金额以上需要签订合同？",
        "办公用品报销需要提供什么材料？"
    ]

    consistency_result = evaluator.evaluate_consistency(consistency_questions, num_samples=3)
    all_results.append(consistency_result)

    # 4. 测试集评估
    test_data_file = "data/报销细则_distilled_chunked.jsonl"
    test_set_result = evaluator.evaluate_on_test_set(test_data_file, sample_size=20)
    if test_set_result:
        all_results.append(test_set_result)

    # 保存报告
    evaluator.save_report(all_results)

    # 总体评分
    print("\n" + "=" * 70)
    print("🎯 总体评估报告")
    print("=" * 70)

    if len(all_results) > 0:
        accuracy = all_results[0]["accuracy"]
        diversity = all_results[1]["avg_diversity"]
        consistency = all_results[2]["avg_consistency"]

        print(f"\n📊 核心指标:")
        print(f"  精确度: {accuracy*100:.1f}%")
        print(f"  多样性: {diversity:.3f}")
        print(f"  一致性: {consistency:.3f}")

        # 综合评分
        overall_score = (accuracy * 0.6 + consistency * 0.3 + diversity * 0.1)
        print(f"\n🏆 综合评分: {overall_score*100:.1f}/100")

        if overall_score >= 0.8:
            print(f"  评级: ⭐⭐⭐⭐⭐ 优秀")
        elif overall_score >= 0.7:
            print(f"  评级: ⭐⭐⭐⭐ 良好")
        elif overall_score >= 0.6:
            print(f"  评级: ⭐⭐⭐ 合格")
        else:
            print(f"  评级: ⭐⭐ 需改进")

    print("=" * 70 + "\n")

    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
