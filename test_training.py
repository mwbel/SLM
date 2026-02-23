#!/usr/bin/env python3
"""测试训练功能"""

import sys
import os
import json
import yaml
from pathlib import Path

# 添加src目录到路径
sys.path.insert(0, str(Path(__file__).parent / "src"))


def test_training():
    """测试训练功能"""
    try:
        print("🔍 开始测试训练功能...")

        # 加载配置
        config_path = Path(__file__).parent / "config.yaml"
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        print(f"✅ 配置加载成功: {config_path}")

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

        # 只使用前3条数据进行快速测试
        test_data = train_data[:3]

        # 初始化训练器
        from training import Trainer

        model_name = config["model"]["base_model"]

        print(f"🚀 初始化训练器，模型: {model_name}")
        trainer = Trainer(model_name=model_name, config=config)
        print("✅ 训练器初始化成功")

        # 执行训练（只训练1个epoch进行测试）
        print("🏃 开始测试训练...")
        original_epochs = config["training"]["num_epochs"]
        config["training"]["num_epochs"] = 1  # 只训练1个epoch

        trainer.train(test_data)
        print("✅ 训练执行成功")

        # 恢复原始配置
        config["training"]["num_epochs"] = original_epochs

        # 测试模型保存
        output_path = Path(__file__).parent / "outputs" / "test_model"
        print(f"💾 测试模型保存到: {output_path}")
        trainer.save_model(str(output_path))
        print("✅ 模型保存成功")

        print("\n🎉 所有测试通过！训练功能正常工作。")
        return True

    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_training()
    sys.exit(0 if success else 1)
