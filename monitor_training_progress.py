#!/usr/bin/env python3
"""
训练进度监控工具
用于监控和分析模型训练进度，包括损失可视化、训练状态摘要等功能
"""

import os
import json
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime
import pandas as pd

# 设置matplotlib支持中文显示
plt.rcParams["font.sans-serif"] = ["SimHei", "Arial Unicode MS", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False  # 解决负号显示问题


def load_checkpoint_data(checkpoint_dir: str) -> Dict:
    """
    加载检查点数据

    Args:
        checkpoint_dir: 检查点目录路径

    Returns:
        包含训练状态数据的字典
    """
    checkpoint_path = Path(checkpoint_dir)
    if not checkpoint_path.exists():
        raise FileNotFoundError(f"检查点目录不存在: {checkpoint_dir}")

    # 加载trainer_state.json
    trainer_state_path = checkpoint_path / "trainer_state.json"
    if not trainer_state_path.exists():
        raise FileNotFoundError(f"trainer_state.json文件不存在: {trainer_state_path}")

    with open(trainer_state_path, "r", encoding="utf-8") as f:
        trainer_state = json.load(f)

    return trainer_state


def extract_training_metrics(trainer_state: Dict) -> Tuple[List, List, List, List]:
    """
    从训练状态中提取指标

    Args:
        trainer_state: 训练状态字典

    Returns:
        (steps, losses, learning_rates, grad_norms): 训练步骤、损失值、学习率和梯度范数
    """
    log_history = trainer_state.get("log_history", [])

    steps = []
    losses = []
    learning_rates = []
    grad_norms = []

    for entry in log_history:
        if "loss" in entry:
            steps.append(entry.get("step", 0))
            losses.append(entry["loss"])
            learning_rates.append(entry.get("learning_rate", 0))
            grad_norms.append(entry.get("grad_norm", 0))

    return steps, losses, learning_rates, grad_norms


def plot_training_progress(
    steps: List,
    losses: List,
    learning_rates: List,
    grad_norms: List,
    save_path: Optional[str] = None,
    show_plot: bool = True,
):
    """
    绘制训练进度图表

    Args:
        steps: 训练步骤列表
        losses: 损失值列表
        learning_rates: 学习率列表
        grad_norms: 梯度范数列表
        save_path: 图表保存路径
        show_plot: 是否显示图表
    """
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))

    # 损失曲线
    ax1.plot(steps, losses, "b-", linewidth=2)
    ax1.set_title("训练损失", fontsize=14, fontweight="bold")
    ax1.set_xlabel("训练步骤")
    ax1.set_ylabel("损失值")
    ax1.grid(True, alpha=0.3)

    # 损失移动平均
    if len(losses) > 10:
        window_size = min(10, len(losses) // 10)
        moving_avg = pd.Series(losses).rolling(window=window_size).mean()
        ax1.plot(
            steps, moving_avg, "r-", linewidth=2, label=f"移动平均(窗口={window_size})"
        )
        ax1.legend()

    # 学习率曲线
    ax2.plot(steps, learning_rates, "g-", linewidth=2)
    ax2.set_title("学习率变化", fontsize=14, fontweight="bold")
    ax2.set_xlabel("训练步骤")
    ax2.set_ylabel("学习率")
    ax2.grid(True, alpha=0.3)

    # 梯度范数曲线
    ax3.plot(steps, grad_norms, "orange", linewidth=2)
    ax3.set_title("梯度范数", fontsize=14, fontweight="bold")
    ax3.set_xlabel("训练步骤")
    ax3.set_ylabel("梯度范数")
    ax3.grid(True, alpha=0.3)
    ax3.set_yscale("log")  # 使用对数刻度，因为梯度范数变化可能很大

    # 损失分布直方图
    ax4.hist(losses, bins=30, alpha=0.7, color="skyblue", edgecolor="black")
    ax4.set_title("损失值分布", fontsize=14, fontweight="bold")
    ax4.set_xlabel("损失值")
    ax4.set_ylabel("频次")
    ax4.grid(True, alpha=0.3)

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches="tight")
        print(f"Chart saved to: {save_path}")

    if show_plot:
        plt.show()


def generate_training_summary(trainer_state: Dict) -> Dict:
    """
    生成训练摘要

    Args:
        trainer_state: 训练状态字典

    Returns:
        包含训练摘要的字典
    """
    log_history = trainer_state.get("log_history", [])

    # 提取基本信息
    current_epoch = trainer_state.get("epoch", 0)
    global_step = trainer_state.get("global_step", 0)
    max_steps = trainer_state.get("max_steps", 0)
    num_train_epochs = trainer_state.get("num_train_epochs", 0)

    # 计算进度
    epoch_progress = (
        (current_epoch / num_train_epochs) * 100 if num_train_epochs > 0 else 0
    )
    step_progress = (global_step / max_steps) * 100 if max_steps > 0 else 0

    # 提取损失信息
    losses = [entry.get("loss", 0) for entry in log_history if "loss" in entry]
    if losses:
        current_loss = losses[-1]
        min_loss = min(losses)
        max_loss = max(losses)
        avg_loss = sum(losses) / len(losses)

        # 计算损失变化趋势
        if len(losses) >= 10:
            recent_losses = losses[-10:]
            earlier_losses = (
                losses[-20:-10] if len(losses) >= 20 else losses[: len(losses) - 10]
            )
            recent_avg = sum(recent_losses) / len(recent_losses)
            earlier_avg = sum(earlier_losses) / len(earlier_losses)
            loss_trend = "下降" if recent_avg < earlier_avg else "上升"
        else:
            loss_trend = "数据不足"
    else:
        current_loss = min_loss = max_loss = avg_loss = 0
        loss_trend = "无数据"

    # 提取学习率信息
    learning_rates = [
        entry.get("learning_rate", 0)
        for entry in log_history
        if "learning_rate" in entry
    ]
    current_lr = learning_rates[-1] if learning_rates else 0

    # 提取梯度范数信息
    grad_norms = [
        entry.get("grad_norm", 0) for entry in log_history if "grad_norm" in entry
    ]
    current_grad_norm = grad_norms[-1] if grad_norms else 0

    summary = {
        "训练进度": {
            "当前轮次": f"{current_epoch:.2f} / {num_train_epochs}",
            "轮次进度": f"{epoch_progress:.2f}%",
            "当前步骤": f"{global_step} / {max_steps}",
            "步骤进度": f"{step_progress:.2f}%",
        },
        "损失信息": {
            "当前损失": f"{current_loss:.6f}",
            "最小损失": f"{min_loss:.6f}",
            "最大损失": f"{max_loss:.6f}",
            "平均损失": f"{avg_loss:.6f}",
            "损失趋势": loss_trend,
        },
        "训练参数": {
            "当前学习率": f"{current_lr:.2e}",
            "当前梯度范数": f"{current_grad_norm:.4f}",
            "总训练步数": max_steps,
            "训练轮次": num_train_epochs,
        },
        "时间信息": {"检查点时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S")},
    }

    return summary


def print_training_summary(summary: Dict):
    """
    打印训练摘要

    Args:
        summary: 训练摘要字典
    """
    print("\n" + "=" * 60)
    print("📊 训练进度摘要")
    print("=" * 60)

    for category, items in summary.items():
        print(f"\n🔸 {category}:")
        for key, value in items.items():
            print(f"  {key}: {value}")

    print("\n" + "=" * 60)


def find_latest_checkpoint(outputs_dir: str = "./outputs") -> Optional[str]:
    """
    查找最新的检查点目录

    Args:
        outputs_dir: 输出目录路径

    Returns:
        最新检查点目录路径，如果没有找到则返回None
    """
    outputs_path = Path(outputs_dir)
    if not outputs_path.exists():
        return None

    # 查找所有checkpoint目录
    checkpoint_dirs = []
    for item in outputs_path.iterdir():
        if item.is_dir() and item.name.startswith("checkpoint-"):
            try:
                step_num = int(item.name.split("-")[1])
                checkpoint_dirs.append((step_num, str(item)))
            except (IndexError, ValueError):
                continue

    if not checkpoint_dirs:
        return None

    # 返回步骤数最大的检查点
    latest_checkpoint = max(checkpoint_dirs, key=lambda x: x[0])[1]
    return latest_checkpoint


def compare_checkpoints(checkpoint_dirs: List[str], save_path: Optional[str] = None):
    """
    比较多个检查点的训练进度

    Args:
        checkpoint_dirs: 检查点目录列表
        save_path: 图表保存路径
    """
    plt.figure(figsize=(15, 8))

    for checkpoint_dir in checkpoint_dirs:
        try:
            trainer_state = load_checkpoint_data(checkpoint_dir)
            steps, losses, _, _ = extract_training_metrics(trainer_state)

            # 使用检查点名称作为标签
            label = Path(checkpoint_dir).name
            plt.plot(steps, losses, label=label, linewidth=2, marker="o", markersize=3)
        except Exception as e:
            print(f"加载检查点 {checkpoint_dir} 失败: {e}")

    plt.title("多检查点损失比较", fontsize=16, fontweight="bold")
    plt.xlabel("训练步骤")
    plt.ylabel("损失值")
    plt.legend()
    plt.grid(True, alpha=0.3)

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches="tight")
        print(f"Comparison chart saved to: {save_path}")

    plt.show()


def main():
    parser = argparse.ArgumentParser(description="训练进度监控工具")
    parser.add_argument("--checkpoint", "-c", type=str, help="检查点目录路径")
    parser.add_argument(
        "--outputs", "-o", type=str, default="./outputs", help="输出目录路径"
    )
    parser.add_argument("--plot", "-p", action="store_true", help="显示训练进度图表")
    parser.add_argument("--save-plot", "-s", type=str, help="保存图表到指定路径")
    parser.add_argument("--summary", "-u", action="store_true", help="显示训练摘要")
    parser.add_argument("--compare", type=str, nargs="+", help="比较多个检查点")
    parser.add_argument("--latest", "-l", action="store_true", help="使用最新检查点")

    args = parser.parse_args()

    # 如果指定了--latest或没有指定检查点，则查找最新检查点
    if args.latest or not args.checkpoint:
        latest_checkpoint = find_latest_checkpoint(args.outputs)
        if latest_checkpoint:
            args.checkpoint = latest_checkpoint
            print(f"Using latest checkpoint: {latest_checkpoint}")
        else:
            print(
                "No checkpoint found, please specify checkpoint path or ensure checkpoints exist in outputs directory"
            )
            return

    # 比较多个检查点
    if args.compare:
        compare_checkpoints(args.compare, args.save_plot)
        return

    # 加载检查点数据
    try:
        trainer_state = load_checkpoint_data(args.checkpoint)
    except Exception as e:
        print(f"Failed to load checkpoint: {e}")
        return

    # 提取训练指标
    steps, losses, learning_rates, grad_norms = extract_training_metrics(trainer_state)

    # 显示训练摘要
    if args.summary or (not args.plot and not args.save_plot):
        summary = generate_training_summary(trainer_state)
        print_training_summary(summary)

    # 绘制训练进度图表
    if args.plot or args.save_plot:
        plot_training_progress(
            steps,
            losses,
            learning_rates,
            grad_norms,
            save_path=args.save_plot,
            show_plot=args.plot,
        )


if __name__ == "__main__":
    main()
