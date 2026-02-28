#!/usr/bin/env python3
"""
Training Progress Monitor Tool
For monitoring and analyzing model training progress, including loss visualization, training status summary, etc.
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


def load_checkpoint_data(checkpoint_dir: str) -> Dict:
    """
    Load checkpoint data

    Args:
        checkpoint_dir: Checkpoint directory path

    Returns:
        Dictionary containing training state data
    """
    checkpoint_path = Path(checkpoint_dir)
    if not checkpoint_path.exists():
        raise FileNotFoundError(
            f"Checkpoint directory does not exist: {checkpoint_dir}"
        )

    # Load trainer_state.json
    trainer_state_path = checkpoint_path / "trainer_state.json"
    if not trainer_state_path.exists():
        raise FileNotFoundError(
            f"trainer_state.json file does not exist: {trainer_state_path}"
        )

    with open(trainer_state_path, "r", encoding="utf-8") as f:
        trainer_state = json.load(f)

    return trainer_state


def extract_training_metrics(trainer_state: Dict) -> Tuple[List, List, List, List]:
    """
    Extract metrics from training state

    Args:
        trainer_state: Training state dictionary

    Returns:
        (steps, losses, learning_rates, grad_norms): Training steps, loss values, learning rates and gradient norms
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
    Plot training progress charts

    Args:
        steps: Training steps list
        losses: Loss values list
        learning_rates: Learning rates list
        grad_norms: Gradient norms list
        save_path: Chart save path
        show_plot: Whether to display chart
    """
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))

    # Training Loss
    ax1.plot(steps, losses, "b-", linewidth=2)
    ax1.set_title("Training Loss", fontsize=14, fontweight="bold")
    ax1.set_xlabel("Training Steps")
    ax1.set_ylabel("Loss Value")
    ax1.grid(True, alpha=0.3)

    # Loss Moving Average
    if len(losses) > 10:
        window_size = min(10, len(losses) // 10)
        moving_avg = pd.Series(losses).rolling(window=window_size).mean()
        ax1.plot(
            steps,
            moving_avg,
            "r-",
            linewidth=2,
            label=f"Moving Avg (window={window_size})",
        )
        ax1.legend()

    # Learning Rate
    ax2.plot(steps, learning_rates, "g-", linewidth=2)
    ax2.set_title("Learning Rate", fontsize=14, fontweight="bold")
    ax2.set_xlabel("Training Steps")
    ax2.set_ylabel("Learning Rate")
    ax2.grid(True, alpha=0.3)

    # Gradient Norm
    ax3.plot(steps, grad_norms, "orange", linewidth=2)
    ax3.set_title("Gradient Norm", fontsize=14, fontweight="bold")
    ax3.set_xlabel("Training Steps")
    ax3.set_ylabel("Gradient Norm")
    ax3.grid(True, alpha=0.3)
    ax3.set_yscale("log")  # Use log scale because gradient norm can vary greatly

    # Loss Distribution
    ax4.hist(losses, bins=30, alpha=0.7, color="skyblue", edgecolor="black")
    ax4.set_title("Loss Distribution", fontsize=14, fontweight="bold")
    ax4.set_xlabel("Loss Value")
    ax4.set_ylabel("Frequency")
    ax4.grid(True, alpha=0.3)

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches="tight")
        print(f"Chart saved to: {save_path}")

    if show_plot:
        plt.show()


def generate_training_summary(trainer_state: Dict) -> Dict:
    """
    Generate training summary

    Args:
        trainer_state: Training state dictionary

    Returns:
        Dictionary containing training summary
    """
    log_history = trainer_state.get("log_history", [])

    # Extract basic information
    current_epoch = trainer_state.get("epoch", 0)
    global_step = trainer_state.get("global_step", 0)
    max_steps = trainer_state.get("max_steps", 0)
    num_train_epochs = trainer_state.get("num_train_epochs", 0)

    # Calculate progress
    epoch_progress = (
        (current_epoch / num_train_epochs) * 100 if num_train_epochs > 0 else 0
    )
    step_progress = (global_step / max_steps) * 100 if max_steps > 0 else 0

    # Extract loss information
    losses = [entry.get("loss", 0) for entry in log_history if "loss" in entry]
    if losses:
        current_loss = losses[-1]
        min_loss = min(losses)
        max_loss = max(losses)
        avg_loss = sum(losses) / len(losses)

        # Calculate loss trend
        if len(losses) >= 10:
            recent_losses = losses[-10:]
            earlier_losses = (
                losses[-20:-10] if len(losses) >= 20 else losses[: len(losses) - 10]
            )
            recent_avg = sum(recent_losses) / len(recent_losses)
            earlier_avg = sum(earlier_losses) / len(earlier_losses)
            loss_trend = "decreasing" if recent_avg < earlier_avg else "increasing"
        else:
            loss_trend = "insufficient data"
    else:
        current_loss = min_loss = max_loss = avg_loss = 0
        loss_trend = "no data"

    # Extract learning rate information
    learning_rates = [
        entry.get("learning_rate", 0)
        for entry in log_history
        if "learning_rate" in entry
    ]
    current_lr = learning_rates[-1] if learning_rates else 0

    # Extract gradient norm information
    grad_norms = [
        entry.get("grad_norm", 0) for entry in log_history if "grad_norm" in entry
    ]
    current_grad_norm = grad_norms[-1] if grad_norms else 0

    summary = {
        "Training Progress": {
            "Current Epoch": f"{current_epoch:.2f} / {num_train_epochs}",
            "Epoch Progress": f"{epoch_progress:.2f}%",
            "Current Step": f"{global_step} / {max_steps}",
            "Step Progress": f"{step_progress:.2f}%",
        },
        "Loss Information": {
            "Current Loss": f"{current_loss:.6f}",
            "Min Loss": f"{min_loss:.6f}",
            "Max Loss": f"{max_loss:.6f}",
            "Avg Loss": f"{avg_loss:.6f}",
            "Loss Trend": loss_trend,
        },
        "Training Parameters": {
            "Current Learning Rate": f"{current_lr:.2e}",
            "Current Gradient Norm": f"{current_grad_norm:.4f}",
            "Total Training Steps": max_steps,
            "Training Epochs": num_train_epochs,
        },
        "Time Information": {
            "Checkpoint Time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        },
    }

    return summary


def print_training_summary(summary: Dict):
    """
    Print training summary

    Args:
        summary: Training summary dictionary
    """
    print("\n" + "=" * 60)
    print("📊 Training Progress Summary")
    print("=" * 60)

    for category, items in summary.items():
        print(f"\n🔸 {category}:")
        for key, value in items.items():
            print(f"  {key}: {value}")

    print("\n" + "=" * 60)


def find_latest_checkpoint(outputs_dir: str = "./outputs") -> Optional[str]:
    """
    Find the latest checkpoint directory

    Args:
        outputs_dir: Output directory path

    Returns:
        Latest checkpoint directory path, or None if not found
    """
    outputs_path = Path(outputs_dir)
    if not outputs_path.exists():
        return None

    # Find all checkpoint directories
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

    # Return the checkpoint with the largest step number
    latest_checkpoint = max(checkpoint_dirs, key=lambda x: x[0])[1]
    return latest_checkpoint


def compare_checkpoints(checkpoint_dirs: List[str], save_path: Optional[str] = None):
    """
    Compare multiple checkpoints' training progress

    Args:
        checkpoint_dirs: List of checkpoint directory paths
        save_path: Chart save path
    """
    plt.figure(figsize=(15, 8))

    for checkpoint_dir in checkpoint_dirs:
        try:
            trainer_state = load_checkpoint_data(checkpoint_dir)
            steps, losses, _, _ = extract_training_metrics(trainer_state)

            # Use checkpoint name as label
            label = Path(checkpoint_dir).name
            plt.plot(steps, losses, label=label, linewidth=2, marker="o", markersize=3)
        except Exception as e:
            print(f"Failed to load checkpoint {checkpoint_dir}: {e}")

    plt.title("Multi-Checkpoint Loss Comparison", fontsize=16, fontweight="bold")
    plt.xlabel("Training Steps")
    plt.ylabel("Loss Value")
    plt.legend()
    plt.grid(True, alpha=0.3)

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches="tight")
        print(f"Comparison chart saved to: {save_path}")

    plt.show()


def main():
    parser = argparse.ArgumentParser(description="Training Progress Monitor Tool")
    parser.add_argument(
        "--checkpoint", "-c", type=str, help="Checkpoint directory path"
    )
    parser.add_argument(
        "--outputs", "-o", type=str, default="./outputs", help="Output directory path"
    )
    parser.add_argument(
        "--plot", "-p", action="store_true", help="Show training progress chart"
    )
    parser.add_argument(
        "--save-plot", "-s", type=str, help="Save chart to specified path"
    )
    parser.add_argument(
        "--summary", "-u", action="store_true", help="Show training summary"
    )
    parser.add_argument(
        "--compare", type=str, nargs="+", help="Compare multiple checkpoints"
    )
    parser.add_argument(
        "--latest", "-l", action="store_true", help="Use latest checkpoint"
    )

    args = parser.parse_args()

    # If --latest is specified or no checkpoint is specified, find the latest checkpoint
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

    # Compare multiple checkpoints
    if args.compare:
        compare_checkpoints(args.compare, args.save_plot)
        return

    # Load checkpoint data
    try:
        trainer_state = load_checkpoint_data(args.checkpoint)
    except Exception as e:
        print(f"Failed to load checkpoint: {e}")
        return

    # Extract training metrics
    steps, losses, learning_rates, grad_norms = extract_training_metrics(trainer_state)

    # Show training summary
    if args.summary or (not args.plot and not args.save_plot):
        summary = generate_training_summary(trainer_state)
        print_training_summary(summary)

    # Plot training progress chart
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
