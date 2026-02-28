#!/usr/bin/env python3
"""
Quick Training Monitor Example
A simple example to demonstrate how to use the training progress monitor
"""

import subprocess
import sys
from pathlib import Path


def run_command(cmd, description):
    """Run a command and display results"""
    print(f"\n{'='*60}")
    print(f"🔍 {description}")
    print(f"{'='*60}")
    print(f"Command: {' '.join(cmd)}\n")

    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print("Errors/Warnings:")
            print(result.stderr)
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running command: {e}")
        return False
    return True


def main():
    """Main example function"""
    print("🚀 Training Progress Monitor - Quick Example")
    print("This script demonstrates various ways to use the training monitor tool")

    # Check if monitor script exists
    monitor_script = "monitor_training_progress_en.py"
    if not Path(monitor_script).exists():
        print(f"❌ Monitor script not found: {monitor_script}")
        sys.exit(1)

    # Example 1: Show training summary for latest checkpoint
    success = run_command(
        ["python3", monitor_script, "--latest", "--summary"],
        "Show training summary for latest checkpoint",
    )

    if not success:
        return

    # Example 2: Generate and save training progress chart
    success = run_command(
        [
            "python3",
            monitor_script,
            "--latest",
            "--plot",
            "--save-plot",
            "example_training_progress.png",
        ],
        "Generate and save training progress chart",
    )

    if not success:
        return

    # Example 3: Compare multiple checkpoints (if they exist)
    checkpoints = ["outputs/checkpoint-291", "outputs/checkpoint-582"]
    existing_checkpoints = []

    for cp in checkpoints:
        if Path(cp).exists():
            existing_checkpoints.append(cp)

    if len(existing_checkpoints) >= 2:
        success = run_command(
            ["python3", monitor_script, "--compare"]
            + existing_checkpoints
            + ["--save-plot", "example_checkpoint_comparison.png"],
            "Compare multiple checkpoints",
        )

    print(f"\n{'='*60}")
    print("✅ All examples completed!")
    print("Generated files:")
    print("  - example_training_progress.png")
    if len(existing_checkpoints) >= 2:
        print("  - example_checkpoint_comparison.png")
    print(f"{'='*60}")

    print("\n💡 Tips:")
    print("  - Use --help to see all available options")
    print("  - Use --checkpoint to specify a specific checkpoint")
    print("  - Use --latest to automatically use the newest checkpoint")
    print("  - Use --compare to compare multiple checkpoints")


if __name__ == "__main__":
    main()
