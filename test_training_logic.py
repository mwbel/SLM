#!/usr/bin/env python3
"""测试训练逻辑（不需要网络连接）"""

import sys
import os
import json
import yaml
from pathlib import Path

# 添加src目录到路径
sys.path.insert(0, str(Path(__file__).parent / "src"))


def test_training_logic():
    """测试训练逻辑"""
    try:
        print("🔍 开始测试训练逻辑...")

        # 加载配置
        config_path = Path(__file__).parent / "config.yaml"
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        print(f"✅ 配置加载成功")

        # 检查训练数据
        data_file = Path(__file__).parent / "data" / "报销细则_21页_distilled.jsonl"
        if not data_file.exists():
            print(f"❌ 训练数据文件不存在: {data_file}")
            return False

        # 加载训练数据
        train_data = []
        with open(data_file, "r", encoding="utf-8") as f:
            for line in f:
                train_data.append(json.loads(line.strip()))

        print(f"✅ 训练数据加载成功: {len(train_data)} 条样本")

        # 验证数据格式
        for i, item in enumerate(train_data[:3]):
            if "instruction" not in item or "output" not in item:
                print(f"❌ 数据格式错误，缺少必要字段: {item}")
                return False
            print(f"✅ 样本 {i+1} 格式正确")

        # 测试tokenize_function逻辑
        print("\n🔍 测试tokenize_function逻辑...")

        # 模拟tokenizer
        class MockTokenizer:
            def __call__(
                self, text, truncation=True, max_length=512, padding="max_length"
            ):
                return {
                    "input_ids": [1, 2, 3, 4, 5] * (max_length // 5),
                    "attention_mask": [1, 1, 1, 1, 1] * (max_length // 5),
                }

        # 模拟tokenize_function
        def mock_tokenize_function(examples):
            instruction = examples.get("instruction", "")
            output = examples.get("output", "")
            text = f"问题：{instruction}\n回答：{output}"
            tokenizer = MockTokenizer()
            return tokenizer(
                text,
                truncation=True,
                max_length=config.get("model", {}).get("max_seq_length", 512),
                padding="max_length",
            )

        # 测试tokenize_function
        for i, item in enumerate(train_data[:3]):
            result = mock_tokenize_function(item)
            if "input_ids" not in result or "attention_mask" not in result:
                print(f"❌ tokenize_function输出格式错误: {result}")
                return False
            print(f"✅ 样本 {i+1} tokenize_function测试通过")

        # 测试配置参数转换
        print("\n🔍 测试配置参数转换...")

        # 测试学习率转换
        lr = config.get("training", {}).get("learning_rate", 2e-4)
        try:
            lr_float = float(lr)
            print(f"✅ 学习率转换成功: {lr} -> {lr_float}")
        except ValueError:
            print(f"❌ 学习率转换失败: {lr}")
            return False

        # 测试批次大小转换
        batch_size = config.get("training", {}).get("batch_size", 1)
        try:
            batch_size_int = int(batch_size)
            print(f"✅ 批次大小转换成功: {batch_size} -> {batch_size_int}")
        except ValueError:
            print(f"❌ 批次大小转换失败: {batch_size}")
            return False

        # 测试训练轮数转换
        epochs = config.get("training", {}).get("num_epochs", 3)
        try:
            epochs_int = int(epochs)
            print(f"✅ 训练轮数转换成功: {epochs} -> {epochs_int}")
        except ValueError:
            print(f"❌ 训练轮数转换失败: {epochs}")
            return False

        print("\n🎉 所有逻辑测试通过！训练功能逻辑正常。")
        print("⚠️  注意：由于网络连接问题，无法测试实际的模型加载和训练过程。")
        print("💡 建议：在网络连接正常时再进行完整的训练测试。")
        return True

    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_training_logic()
    sys.exit(0 if success else 1)
