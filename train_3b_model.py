#!/usr/bin/env python3
"""
训练 Qwen2.5-3B 模型
使用QLoRA技术在普通设备上高效训练3B参数模型
"""

import sys
import json
from pathlib import Path
import yaml

# 添加src到路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

from training import Trainer


def load_jsonl(file_path: str) -> list:
    """加载JSONL格式的训练数据"""
    data = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():  # 跳过空行
                data.append(json.loads(line.strip()))
    return data


def print_training_info(config, train_data):
    """打印训练信息"""
    print("\n" + "=" * 70)
    print("🚀 Qwen2.5-3B 模型训练")
    print("=" * 70)

    # 模型配置
    print("\n📦 模型配置:")
    print(f"  基座模型: {config['model']['base_model']}")
    print(f"  最大序列长度: {config['model']['max_seq_length']}")

    # LoRA配置
    print("\n🔧 LoRA配置:")
    print(f"  Rank: {config['lora']['rank']}")
    print(f"  Alpha: {config['lora']['alpha']}")
    print(f"  Dropout: {config['lora']['dropout']}")

    # 训练配置
    print("\n⚙️  训练配置:")
    print(f"  训练样本数: {len(train_data)}")
    print(f"  训练轮数: {config['training']['num_epochs']}")
    print(f"  批次大小: {config['training']['batch_size']}")
    print(f"  梯度累积步数: {config['training']['gradient_accumulation_steps']}")
    print(f"  有效批次大小: {config['training']['batch_size'] * config['training']['gradient_accumulation_steps']}")
    print(f"  学习率: {config['training']['learning_rate']}")
    print(f"  Warmup步数: {config['training']['warmup_steps']}")

    # 数据样本示例
    print("\n📄 数据样本示例:")
    if len(train_data) > 0:
        sample = train_data[0]
        print(f"  问题: {sample.get('instruction', '')[:80]}...")
        print(f"  回答: {sample.get('output', '')[:80]}...")

    print("\n" + "=" * 70)


def main():
    """主训练流程"""

    print("\n🔵 开始加载训练配置和数据...")

    # 加载配置
    config_path = Path(__file__).parent / "config.yaml"
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    # 加载训练数据
    data_path = Path(__file__).parent / "data" / "报销细则_distilled_chunked.jsonl"

    if not data_path.exists():
        print(f"\n❌ 错误: 找不到训练数据文件")
        print(f"   路径: {data_path}")
        print(f"   请先运行数据蒸馏生成训练数据")
        return False

    train_data = load_jsonl(str(data_path))

    if len(train_data) == 0:
        print(f"\n❌ 错误: 训练数据为空")
        print(f"   请检查数据文件格式")
        return False

    # 打印训练信息
    print_training_info(config, train_data)

    # 初始化训练器
    print("\n🔵 初始化训练器...")
    model_name = config['model']['base_model']

    try:
        trainer = Trainer(model_name=model_name, config=config)
        print("✅ 训练器初始化成功")

        # 开始训练
        print("\n🔵 开始训练...")
        print("💡 提示: 训练过程中会显示进度条和损失值")
        print("   按 Ctrl+C 可以安全中断训练\n")

        trainer.train(train_data)

        print("\n✅ 训练完成！")

        # 保存模型
        output_path = Path(__file__).parent / "outputs" / "qwen2_5-3b-trained"
        print(f"\n💾 保存模型到: {output_path}")

        trainer.save_model(str(output_path))

        print("✅ 模型已保存")

        # 打印总结
        print("\n" + "=" * 70)
        print("🎉 训练总结")
        print("=" * 70)
        print(f"✅ 模型: Qwen2.5-3B")
        print(f"✅ 训练样本: {len(train_data)}")
        print(f"✅ 保存位置: {output_path}")
        print("\n下一步:")
        print("  1. 运行测试脚本验证模型效果")
        print("  2. 如果满意，可以导出为GGUF格式用于ollama")
        print("  3. 或者直接在应用中加载使用")
        print("=" * 70 + "\n")

        return True

    except Exception as e:
        print(f"\n❌ 训练失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
