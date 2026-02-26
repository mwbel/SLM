"""
改进的评估逻辑 - 修复数字类问题评估漏洞

核心改进:
1. 识别数字类关键词
2. 数字必须100%匹配
3. 降低数字类问题的合格阈值
"""

def evaluate_accuracy_improved(self, test_cases, temperature=0.1):
    """改进的精确度评估"""
    correct_count = 0
    total_count = len(test_cases)
    detailed_results = []

    for i, case in enumerate(test_cases, 1):
        question = case["question"]
        keywords = case["keywords"]
        description = case.get("description", "")

        # 生成回答
        response = self.inferencer.generate(
            question,
            max_new_tokens=300,
            temperature=temperature,
            top_p=0.95,
            repetition_penalty=1.0,
        )

        # 分离数字和非数字关键词
        number_keywords = [kw for kw in keywords if kw.isdigit()]
        text_keywords = [kw for kw in keywords if not kw.isdigit()]

        # 匹配关键词
        found_numbers = [kw for kw in number_keywords if kw in response]
        found_text = [kw for kw in text_keywords if kw in response]
        found_keywords = found_numbers + found_text

        missing_numbers = [kw for kw in number_keywords if kw not in response]
        missing_text = [kw for kw in text_keywords if kw not in response]
        missing_keywords = missing_numbers + missing_text

        # 改进的判断逻辑
        if number_keywords:
            # 数字类问题：数字必须100%正确
            numbers_correct = (len(found_numbers) == len(number_keywords))
            text_coverage = len(found_text) / len(text_keywords) if text_keywords else 1.0

            # 数字全对 + 文本至少50%
            is_correct = numbers_correct and text_coverage >= 0.5

            if not is_correct:
                if not numbers_correct:
                    reason = f"数字错误: 缺少 {missing_numbers}"
                else:
                    reason = f"文本不足: 覆盖率 {text_coverage*100:.1f}%"
            else:
                reason = "数字正确 + 文本充足"
        else:
            # 非数字类问题：使用原来的50%阈值
            keyword_coverage = len(found_keywords) / len(keywords) if keywords else 0
            is_correct = keyword_coverage >= 0.5
            reason = f"覆盖率 {keyword_coverage*100:.1f}%"

        if is_correct:
            correct_count += 1

        # 保存结果
        detailed_results.append({
            "question": question,
            "description": description,
            "expected_keywords": keywords,
            "number_keywords": number_keywords,
            "found_keywords": found_keywords,
            "missing_keywords": missing_keywords,
            "response": response,
            "is_correct": is_correct,
            "reason": reason
        })

        # 打印
        print(f"\n[{i}/{total_count}] {description}")
        print(f"问题: {question}")
        print(f"预期关键词: {', '.join(keywords)}")
        print(f"模型回答: {response}")
        print(f"数字关键词: {number_keywords} → 找到: {found_numbers}")
        print(f"文本关键词: {text_keywords} → 找到: {found_text}")
        print(f"结果: {'✅ 合格' if is_correct else '❌ 不合格'} - {reason}")

    accuracy = correct_count / total_count if total_count > 0 else 0
    avg_coverage = sum(
        len(r["found_keywords"]) / len(r["expected_keywords"])
        for r in detailed_results
    ) / total_count

    return {
        "type": "accuracy_improved",
        "total": total_count,
        "correct": correct_count,
        "accuracy": accuracy,
        "avg_coverage": avg_coverage,
        "detailed_results": detailed_results
    }


# 使用示例
if __name__ == "__main__":
    from src.inference.inferencer import ModelInferencer

    # 创建推理器（需要先加载模型）
    # inferencer = ModelInferencer("outputs/qwen2_5-3b-trained", "models/Qwen/Qwen2.5-3B")
    # inferencer.load_model()

    # 测试用例需要标记哪些是数字类问题
    test_cases = [
        {
            "question": "图书资料报销在什么金额以上需要附合同？",
            "keywords": ["30000", "合同", "图书"],
            # 30000会被自动识别为数字关键词
            "description": "图书采购测试"
        },
        # ... 更多测试用例
    ]

    print("注意：此文件展示改进的评估逻辑，请集成到 evaluate_model.py 中使用")
    print("核心改进：数字类问题要求100%准确，不能遗漏任何数字关键词")
