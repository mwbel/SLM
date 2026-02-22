"""日志工具"""

import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional


def setup_logger(
    name: str = "slm_trainer",
    log_file: Optional[str] = None,
    level: int = logging.INFO,
    console: bool = True
) -> logging.Logger:
    """
    设置日志记录器

    Args:
        name: 日志记录器名称
        log_file: 日志文件路径
        level: 日志级别
        console: 是否输出到控制台

    Returns:
        配置好的日志记录器
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.handlers.clear()

    # 日志格式
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # 控制台处理器
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    # 文件处理器
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


class TrainingLogger:
    """训练过程日志记录器"""

    def __init__(self, log_dir: str = "./outputs/logs"):
        """
        初始化训练日志记录器

        Args:
            log_dir: 日志目录
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = self.log_dir / f"training_{timestamp}.log"

        self.logger = setup_logger(
            name="training",
            log_file=str(log_file),
            level=logging.INFO
        )
        self.metrics = []

    def log_epoch(self, epoch: int, loss: float, metrics: dict = None):
        """
        记录训练轮次信息

        Args:
            epoch: 轮次编号
            loss: 损失值
            metrics: 其他指标
        """
        msg = f"Epoch {epoch} - Loss: {loss:.4f}"
        if metrics:
            metric_str = ", ".join([f"{k}: {v:.4f}" for k, v in metrics.items()])
            msg += f" - {metric_str}"

        self.logger.info(msg)
        self.metrics.append({
            'epoch': epoch,
            'loss': loss,
            **(metrics or {})
        })

    def log_step(self, step: int, loss: float):
        """
        记录训练步骤信息

        Args:
            step: 步骤编号
            loss: 损失值
        """
        self.logger.info(f"Step {step} - Loss: {loss:.4f}")

    def save_metrics(self, output_path: str = None):
        """
        保存训练指标到文件

        Args:
            output_path: 输出文件路径
        """
        import json

        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = self.log_dir / f"metrics_{timestamp}.json"

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.metrics, f, ensure_ascii=False, indent=2)
