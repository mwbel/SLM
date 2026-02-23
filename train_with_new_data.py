"""使用新生成的367样本数据训练模型"""

import sys
from pathlib import Path
import json

# 添加src目录到路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

from training.trainer import Trainer
import yaml

if __name__ == "__main__":
    print("="*60)
    print("使用新数据训练模型 (367样本)")
    print("="*60)

    # 加载配置
    with open("config.yaml", "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    # 修改配置以使用新数据和更多训练轮次
    config["paths"]["train_data"] = "data/报销细则_distilled_chunked.jsonl"
    config["training"]["num_epochs"] = 10  # 使用10个epoch
    config["paths"]["output_dir"] = "./outputs/trained_model_367samples"

    print(f"\n📊 训练配置:")
    print(f"   - 训练数据: {config['paths']['train_data']}")
    print(f"   - 样本数量: 367组")
    print(f"   - 训练轮次: {config['training']['num_epochs']} epochs")
    print(f"   - 批次大小: {config['training']['batch_size']}")
    print(f"   - 学习率: {config['training']['learning_rate']}")
    print(f"   - 输出目录: {config['paths']['output_dir']}")
    print(f"\n预期训练时间: 约30-60分钟 (取决于设备性能)\n")

    # 加载训练数据
    print("📂 加载训练数据...")
    train_data = []
    with open(config["paths"]["train_data"], 'r', encoding='utf-8') as f:
        for line in f:
            train_data.append(json.loads(line.strip()))
    print(f"✅ 成功加载 {len(train_data)} 条训练样本")

    # 初始化训练器
    print("\n🔧 初始化训练器...")
    trainer = Trainer(
        model_name=config["model"]["base_model"],
        config=config
    )

    # 开始训练
    print("\n🚀 开始训练...\n")
    trainer.train(train_data)

    # 保存模型
    print(f"\n💾 保存模型到: {config['paths']['output_dir']}")
    trainer.save_model(config["paths"]["output_dir"])

    print("\n" + "="*60)
    print("✅ 训练完成！")
    print(f"📁 模型已保存到: {config['paths']['output_dir']}")
    print("="*60)
    print("\n💡 下一步:")
    print("   1. 运行推理测试: python test_inference.py")
    print("   2. 启动Web界面: python app.py")
