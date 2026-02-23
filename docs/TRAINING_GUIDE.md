# 训练指南

## 快速开始

### 1. 准备训练数据

已生成的训练数据：
- 文件：`data/报销细则_21页_distilled.jsonl`
- 样本数：12条
- 格式：标准JSONL

### 2. 检查配置

编辑 `config.yaml` 确认训练参数：

```yaml
# Model settings
model:
  base_model: "Qwen/Qwen2.5-0.5B"  # 基座模型
  max_seq_length: 2048

# LoRA settings
lora:
  rank: 8
  alpha: 16
  dropout: 0.05

# Training settings
training:
  batch_size: 4
  learning_rate: 2e-4
  num_epochs: 3
  warmup_steps: 10
```

### 3. 运行训练

```bash
python3 train.py
```

### 4. 训练输出

训练完成后，模型将保存到：
- 路径：`outputs/reimbursement_model/`
- 包含：LoRA权重 + tokenizer

### 5. 查看日志

```bash
cat outputs/logs/training.log
```

## 注意事项

### 硬件要求

**最低配置：**
- 8GB RAM
- NVIDIA GTX 1650 (4GB VRAM) 或 Apple M1
- 使用4-bit量化

**推荐配置：**
- 16GB RAM
- RTX 3060 (12GB VRAM) 或 Apple M2

### 训练时间估算

- 12个样本，3个epoch
- 预计时间：5-15分钟（取决于硬件）

### 常见问题

**Q: CUDA内存不足？**
A: 减小batch_size到2或1

**Q: 没有GPU？**
A: 可以使用CPU训练，但会很慢。建议使用更小的模型或减少样本数。

**Q: 训练数据太少？**
A: 12个样本适合快速测试。实际应用建议至少100+样本。

## 下一步

训练完成后：
1. 测试模型效果
2. 生成更多训练数据
3. 继续微调优化
