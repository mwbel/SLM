#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
模型测试脚本 - 用于测试训练好的垂直领域小模型
"""

import sys
import os
from pathlib import Path

# 添加src到路径，确保可以导入项目模块
current_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(current_dir / "src"))

try:
    from inference.inferencer import ModelInferencer
except ImportError:
    print(
        "错误: 无法导入 inference.inferencer 模块。请确保你在 slm-trainer 目录下运行此脚本。"
    )
    sys.exit(1)


def main():
    # 模型路径配置
    # 自动查找可能的模型路径
    script_dir = Path(__file__).resolve().parent
    possible_paths = [
        script_dir / "outputs" / "trained_model",
        script_dir / "outputs" / "reimbursement_model",
    ]

    model_path = None
    for path in possible_paths:
        if path.exists():
            model_path = path
            break

    if model_path is None:
        model_path = script_dir / "outputs" / "trained_model"  # 默认路径用于报错显示

    print(f"=== 垂直小模型测试脚本 ===")
    print(f"检查模型路径: {model_path}")

    if not os.path.exists(model_path):
        print(f"\n警告: 找不到模型路径 '{model_path}'")
        print("如果模型正在训练中，请等待训练完成后再运行此脚本。")
        print("或者修改脚本中的 model_path 变量指向正确的路径。")
        return

    # 初始化推理器
    try:
        inferencer = ModelInferencer(model_path=model_path)
        inferencer.load_model()
    except Exception as e:
        print(f"\n加载模型失败: {e}")
        return

    # 预设测试问题（基于报销细则）
    test_questions = [
        "华东师范大学制定财务报销细则的依据和目的是什么？",
        "学校的哪些经费类型需要遵守本财务报销细则？",
        "购买办公用品达到什么金额需要附明细清单？",
        "购买图书资料有哪些报销规定？",
        "办理财务报销前，需要准备哪些基本材料？",
    ]

    print("\n=== 开始自动测试预设问题 ===")
    for i, question in enumerate(test_questions, 1):
        print(f"\n[{i}/{len(test_questions)}] 问题: {question}")
        try:
            # 生成回答
            response = inferencer.generate(question)
            print(f"回答: {response}")
            print("-" * 50)
        except Exception as e:
            print(f"生成回答时出错: {e}")

    # 交互式测试模式
    print("\n=== 进入交互式测试模式 ===")
    print("输入 'q' 或 'quit' 退出")

    while True:
        try:
            user_input = input("\n请输入问题: ").strip()
            if user_input.lower() in ["q", "quit", "exit"]:
                break

            if not user_input:
                continue

            print("正在生成回答...")
            response = inferencer.generate(user_input)
            print(f"回答: {user_input}\n{response}")

        except KeyboardInterrupt:
            print("\n退出测试")
            break
        except Exception as e:
            print(f"发生错误: {e}")

    print("\n测试结束")


if __name__ == "__main__":
    main()
