#!/usr/bin/env python3
"""
严格测试用例集 - 专注于数字类问题和关键信息准确性

设计原则:
1. 数字类问题必须100%准确
2. 金额阈值、日期、数量等关键信息不容许错误
3. 测试实际业务场景中的关键问题
"""

# 严格测试用例 - 优先级高（关键业务场景）
CRITICAL_TEST_CASES = [
    {
        "question": "图书资料报销在什么金额以上需要附合同？",
        "keywords": ["30000", "合同", "图书"],
        "category": "数字-金额阈值",
        "priority": "critical",
        "description": "图书合同金额测试",
        "notes": "容易混淆500元验收和30000元合同"
    },
    {
        "question": "课题协作费在什么金额以上需要签订协议或合同？",
        "keywords": ["3000", "10000", "协议", "合同"],
        "category": "数字-多重金额",
        "priority": "critical",
        "description": "课题协作费双重阈值",
        "notes": "3000元协议，10000元合同，容易混淆"
    },
    {
        "question": "制作费和材料费在什么金额范围内需要签订协议？",
        "keywords": ["3000", "10000", "协议"],
        "category": "数字-金额范围",
        "priority": "critical",
        "description": "制作费材料费协议阈值",
        "notes": "3000-10000元范围"
    },
    {
        "question": "办公用品报销金额在多少元以上需要提供明细清单？",
        "keywords": ["500", "明细清单", "办公用品"],
        "category": "数字-报销门槛",
        "priority": "critical",
        "description": "办公用品报销门槛",
        "notes": "500元以上需明细清单"
    },
]

# 标准测试用例 - 流程类问题
STANDARD_TEST_CASES = [
    {
        "question": "差旅费的报销需要提供哪些材料？",
        "keywords": ["审批单", "机票", "发票", "住宿"],
        "category": "流程-材料清单",
        "priority": "standard",
        "description": "差旅费材料测试",
    },
    {
        "question": "会议费报销需要提供哪些审批材料？",
        "keywords": ["会议通知", "签到", "审批"],
        "category": "流程-材料清单",
        "priority": "standard",
        "description": "会议费测试",
    },
    {
        "question": "国内差旅费的住宿费标准是什么？",
        "keywords": ["150", "200", "住宿费", "标准"],
        "category": "数字-费用标准",
        "priority": "standard",
        "description": "差旅住宿标准",
        "notes": "150-200元标准"
    },
]

# 数字密集型测试用例
NUMBER_DENSE_TEST_CASES = [
    {
        "question": "华东师范大学对不同金额的图书资料采购有哪些不同的报销要求？",
        "keywords": ["500", "30000", "图书馆", "验收", "清单", "合同"],
        "category": "数字-多条件组合",
        "priority": "high",
        "description": "图书采购多级门槛",
        "notes": "500元验收，30000元合同"
    },
    {
        "question": "对于不同金额的课题协作费、制作费、材料费，签订协议和合同的要求分别是什么？",
        "keywords": ["3000", "10000", "协议", "合同"],
        "category": "数字-多条件组合",
        "priority": "high",
        "description": "多种费用类型合同要求",
    },
    {
        "question": "出差期间的市内交通费每天补助标准是多少？",
        "keywords": ["80", "交通费", "补助"],
        "category": "数字-补助标准",
        "priority": "standard",
        "description": "市内交通费补助",
    },
]

# 材料清单类测试
MATERIAL_LIST_TEST_CASES = [
    {
        "question": "会议费报销需要提交哪些具体材料？",
        "keywords": ["会议通知", "预算审批单", "签到表", "明细单", "发票"],
        "category": "清单-会议材料",
        "priority": "standard",
        "description": "会议材料完整清单",
    },
    {
        "question": "图书资料报销时，单价500元以上的需要提供什么？",
        "keywords": ["500", "合同", "验收", "清单"],
        "category": "清单-图书材料",
        "priority": "standard",
        "description": "图书材料清单（分情况）",
    },
]

# 所有测试用例集合
ALL_STRICT_TEST_CASES = (
    CRITICAL_TEST_CASES +
    STANDARD_TEST_CASES +
    NUMBER_DENSE_TEST_CASES +
    MATERIAL_LIST_TEST_CASES
)

# 按类别分组
TEST_CASES_BY_CATEGORY = {
    "critical": CRITICAL_TEST_CASES,
    "standard": STANDARD_TEST_CASES,
    "number_dense": NUMBER_DENSE_TEST_CASES,
    "material_list": MATERIAL_LIST_TEST_CASES,
}

# 数字类测试用例（自动提取包含数字关键词的）
NUMBER_TEST_CASES = [
    case for case in ALL_STRICT_TEST_CASES
    if any(k.strip().isdigit() for k in case["keywords"])
]

# 统计信息
def print_statistics():
    """打印测试用例统计"""
    print("=" * 70)
    print("📊 严格测试用例集统计")
    print("=" * 70)

    print(f"\n总测试用例数: {len(ALL_STRICT_TEST_CASES)}")
    print(f"  - 关键优先级: {len(CRITICAL_TEST_CASES)}")
    print(f"  - 标准优先级: {len(STANDARD_TEST_CASES)}")
    print(f"  - 数字密集型: {len(NUMBER_DENSE_TEST_CASES)}")
    print(f"  - 材料清单型: {len(MATERIAL_LIST_TEST_CASES)}")

    print(f"\n数字类测试用例: {len(NUMBER_TEST_CASES)}")

    # 按类别统计
    print("\n按类别分布:")
    category_counts = {}
    for case in ALL_STRICT_TEST_CASES:
        cat = case["category"]
        category_counts[cat] = category_counts.get(cat, 0) + 1

    for cat, count in sorted(category_counts.items()):
        print(f"  - {cat}: {count}")

    print("\n" + "=" * 70)

if __name__ == "__main__":
    print_statistics()

    # 导出测试用例供evaluate_model.py使用
    print("\n💡 使用方法:")
    print("```python")
    print("from test_cases_strict import ALL_STRICT_TEST_CASES")
    print("")
    print("# 在evaluate_model.py中使用:")
    print("accuracy_result = evaluator.evaluate_accuracy(")
    print("    ALL_STRICT_TEST_CASES,")
    print("    strict_mode=True")
    print(")")
    print("```")
