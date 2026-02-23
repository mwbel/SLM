"""训练脚本 - 使用生成的JSONL数据训练模型"""

import sys
import json
from pathlib import Path
import yaml

# 添加src到路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

from training import Trainer
from utils import setup_logger

def load_jsonl(file_path: str) -> list:
    """加载JSONL文件"""
    data = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            data.append(json.loads(line.strip()))
    return data

def main():
    """主训练流程"""

    # 设置日志
    logger = setup_logger("training", log_file="outputs/logs/training.log")

    logger.info("=== 开始训练流程 ===")

    # 加载配置
    with open('config.yaml', 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    # 加载训练数据
    train_file = "data/报销细则_21页_distilled.jsonl"
    logger.info(f"加载训练数据: {train_file}")
    train_data = load_jsonl(train_file)
    logger.info(f"训练样本数量: {len(train_data)}")

    # 显示第一个样本
    logger.info(f"样本示例:\n{json.dumps(train_data[0], ensure_ascii=False, indent=2)}")

    # 初始化训练器
    model_name = config['model']['base_model']
    logger.info(f"初始化训练器，基座模型: {model_name}")

    try:
        trainer = Trainer(model_name=model_name, config=config)
        logger.info("训练器初始化成功")

        # 开始训练
        logger.info("开始训练...")
        trainer.train(train_data)
        logger.info("训练完成")

        # 保存模型
        output_path = "outputs/reimbursement_model"
        logger.info(f"保存模型到: {output_path}")
        trainer.save_model(output_path)
        logger.info("模型保存成功")

        logger.info("=== 训练流程完成 ===")

    except Exception as e:
        logger.error(f"训练失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise

if __name__ == "__main__":
    main()
