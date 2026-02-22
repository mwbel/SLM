# SLM Trainer - 垂直小模型训练系统

轻量级垂直领域小语言模型训练工具，支持在普通家用电脑上快速训练。

## 快速开始

### 安装依赖
```bash
pip install -r requirements.txt
```

### 基本使用
1. 准备训练数据（JSONL 格式）
2. 配置 config.yaml
3. 运行训练脚本

## 硬件要求

**最低配置：**
- 8GB RAM
- NVIDIA GTX 1650 (4GB VRAM) 或 Apple M1

**推荐配置：**
- 16GB RAM
- RTX 3060 (12GB VRAM) 或 Apple M2

## 项目结构
```
slm-trainer/
├── data/           # 训练数据
├── models/         # 模型文件
├── outputs/        # 输出结果
├── src/            # 源代码
└── tests/          # 测试代码
```

## 技术栈
- Qwen2.5 (0.5B/1.5B)
- QLoRA (4-bit)
- Unsloth
- Gradio
