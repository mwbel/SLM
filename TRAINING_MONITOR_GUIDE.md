# 训练进度监控工具使用指南

## 概述

`monitor_training_progress.py` 是一个用于监控和分析模型训练进度的工具，可以可视化训练损失、学习率变化、梯度范数等关键指标，帮助您更好地了解模型训练状态。

## 功能特性

- 📊 **训练进度可视化**: 生成包含损失曲线、学习率变化、梯度范数和损失分布的综合图表
- 📈 **训练状态摘要**: 显示当前训练进度、损失信息、训练参数等关键信息
- 🔄 **多检查点比较**: 比较不同训练阶段的损失曲线
- 💾 **图表保存**: 将可视化结果保存为高质量图片
- 📋 **自动检测**: 自动查找最新的训练检查点

## 安装依赖

```bash
pip install matplotlib pandas numpy
```

## 使用方法

### 基本用法

1. **查看最新检查点的训练摘要**:
   ```bash
   python3 monitor_training_progress.py --latest --summary
   ```

2. **生成训练进度图表**:
   ```bash
   python3 monitor_training_progress.py --latest --plot
   ```

3. **保存训练进度图表**:
   ```bash
   python3 monitor_training_progress.py --latest --plot --save-plot training_progress.png
   ```

### 高级用法

1. **指定特定检查点**:
   ```bash
   python3 monitor_training_progress.py --checkpoint outputs/checkpoint-582 --summary --plot
   ```

2. **比较多个检查点**:
   ```bash
   python3 monitor_training_progress.py --compare outputs/checkpoint-291 outputs/checkpoint-582 --save-plot comparison.png
   ```

3. **只显示摘要不显示图表**:
   ```bash
   python3 monitor_training_progress.py --latest --summary
   ```

### 命令行参数

| 参数 | 简写 | 描述 | 示例 |
|------|------|------|------|
| `--checkpoint` | `-c` | 指定检查点目录路径 | `outputs/checkpoint-582` |
| `--outputs` | `-o` | 指定输出目录路径（默认: ./outputs） | `./outputs` |
| `--plot` | `-p` | 显示训练进度图表 | |
| `--save-plot` | `-s` | 保存图表到指定路径 | `training_progress.png` |
| `--summary` | `-u` | 显示训练摘要 | |
| `--compare` | | 比较多个检查点 | `cp1 cp2 cp3` |
| `--latest` | `-l` | 使用最新检查点 | |

## 输出说明

### 训练摘要

训练摘要包含以下信息：

1. **训练进度**:
   - 当前轮次和总轮次
   - 轮次进度百分比
   - 当前步骤和总步骤
   - 步骤进度百分比

2. **损失信息**:
   - 当前损失值
   - 最小/最大/平均损失
   - 损失趋势（上升/下降）

3. **训练参数**:
   - 当前学习率
   - 当前梯度范数
   - 总训练步数
   - 训练轮次数

4. **时间信息**:
   - 检查点生成时间

### 可视化图表

生成的图表包含四个子图：

1. **训练损失曲线**: 显示损失随训练步骤的变化，包含移动平均线
2. **学习率变化**: 显示学习率调度器的变化情况
3. **梯度范数**: 显示梯度范数的对数变化，用于判断训练稳定性
4. **损失值分布**: 显示损失值的直方图分布

## 示例输出

### 训练摘要示例

```
============================================================
📊 训练进度摘要
============================================================

🔸 训练进度:
  当前轮次: 2.00 / 3
  轮次进度: 66.67%
  当前步骤: 582 / 873
  步骤进度: 66.67%

🔸 损失信息:
  当前损失: 0.078305
  最小损失: 0.019137
  最大损失: 7.939564
  平均损失: 0.396181
  损失趋势: 下降

🔸 训练参数:
  当前学习率: 1.73e-05
  当前梯度范数: 0.2105
  总训练步数: 873
  训练轮次: 3

🔸 时间信息:
  检查点时间: 2026-02-28 16:46:59
============================================================
```

## 常见问题

### 1. 中文字体警告

如果在运行时看到中文字体警告，这是正常的，不影响功能。图表仍会正常生成和保存。

### 2. 找不到检查点

如果提示"未找到检查点"，请确保：
- 训练已经运行并生成了检查点
- 检查点目录路径正确
- 检查点目录包含 `trainer_state.json` 文件

### 3. 图表不显示

如果在远程环境中运行，图表可能无法显示。建议使用 `--save-plot` 参数保存图表到文件。

## 集成到训练流程

可以在训练脚本中添加监控功能：

```python
import subprocess
import os

def monitor_training():
    """训练完成后自动生成监控报告"""
    try:
        # 生成训练摘要
        subprocess.run([
            "python3", "monitor_training_progress.py", 
            "--latest", "--summary"
        ], check=True)
        
        # 保存训练进度图表
        subprocess.run([
            "python3", "monitor_training_progress.py", 
            "--latest", "--plot", 
            "--save-plot", "final_training_progress.png"
        ], check=True)
        
        print("✅ 训练监控报告已生成")
    except subprocess.CalledProcessError as e:
        print(f"❌ 生成监控报告失败: {e}")

# 在训练完成后调用
if __name__ == "__main__":
    # ... 训练代码 ...
    monitor_training()
```

## 扩展功能

可以根据需要扩展监控工具，例如：

1. **添加更多指标**: 可以添加验证损失、准确率等指标
2. **实时监控**: 可以集成到训练过程中实现实时监控
3. **自动报告**: 可以定期生成训练报告并发送通知
4. **性能分析**: 可以添加训练速度、资源使用等性能指标

## 技术实现

工具的核心功能：

1. **数据加载**: 从 `trainer_state.json` 加载训练历史数据
2. **指标提取**: 从日志历史中提取损失、学习率、梯度范数等
3. **可视化**: 使用 matplotlib 生成综合图表
4. **摘要生成**: 计算并格式化关键训练指标

这种设计使得工具可以轻松适配不同的训练框架和配置。