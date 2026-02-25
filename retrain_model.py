#!/usr/bin/env python3
"""重新训练模型（修复了labels问题）"""

import sys
from pathlib import Path

# 添加src到路径
sys.path.insert(0, str(Path(__file__).parent / "src"))


def retrain():
    """重新训练模型"""
    print("=" * 70)
    print("重新训练模型 - 修复版")
    print("=" * 70)

    try:
        import yaml
        import json
        from training import Trainer

        # 加载配置
        print("\n1. 加载配置...")
        config_path = Path("config.yaml")
        with open(config_path) as f:
            config = yaml.safe_load(f)

        # 模型名称
        model_name = config['model']['base_model']
        print(f"   基座模型: {model_name}")

        # 加载训练数据
        print("\n2. 加载训练数据...")
        data_file = Path("data/报销细则_distilled_chunked.jsonl")
        train_data = []
        with open(data_file, "r", encoding="utf-8") as f:
            for line in f:
                train_data.append(json.loads(line.strip()))
        print(f"   训练样本数: {len(train_data)}")

        # 初始化训练器
        print("\n3. 初始化训练器...")
        trainer = Trainer(model_name, config)
        print("   ✓ 训练器初始化成功")

        # 开始训练
        print("\n4. 开始训练...")
        print(f"   轮数: {config['training']['num_epochs']}")
        print(f"   批次大小: {config['training']['batch_size']}")
        print(f"   学习率: {config['training']['learning_rate']}")
        print(f"   梯度累积步数: {config['training']['gradient_accumulation_steps']}")

        trainer.train(train_data)

        # 保存模型
        print("\n5. 保存模型...")
        output_path = str(Path("outputs/trained_model"))
        trainer.save_model(output_path)
        print(f"   ✓ 模型已保存到: {output_path}")

        print("\n" + "=" * 70)
        print("✅ 训练完成！")
        print("=" * 70)
        print("\n请运行 test_trained_model.py 来测试模型")

        return True

    except Exception as e:
        print(f"\n❌ 训练失败: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = retrain()
    sys.exit(0 if success else 1)
