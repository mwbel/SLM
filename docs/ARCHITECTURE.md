# SLM Trainer 架构文档

## 项目结构

```
slm-trainer/
├── data/              # 训练数据目录
├── models/            # 模型存储目录
├── outputs/           # 训练输出目录
├── src/               # 源代码
│   ├── data_prep/     # 数据处理模块
│   ├── training/      # 训练模块
│   ├── inference/     # 推理模块
│   ├── export/        # 模型导出模块
│   ├── management/    # 模型管理模块
│   ├── ui/            # 用户界面模块
│   └── utils/         # 工具模块
├── tests/             # 测试代码
├── docs/              # 文档
├── config.yaml        # 配置文件
├── requirements.txt   # 依赖列表
└── main.py            # 主入口
```

## 模块说明

### 1. 数据处理模块 (data_prep)
- **file_loader.py**: 文件上传和加载
- **data_processor.py**: 数据转换和格式化

### 2. 训练模块 (training)
- **trainer.py**: QLoRA训练器实现

### 3. 推理模块 (inference)
- **inference.py**: 模型推理引擎

### 4. 导出模块 (export)
- **model_exporter.py**: 模型导出到不同格式（GGUF, EXL2, Ollama）

### 5. 管理模块 (management)
- **model_manager.py**: 模型版本管理和元数据管理

### 6. 界面模块 (ui)
- **app.py**: Gradio Web界面

### 7. 工具模块 (utils)
- **config_loader.py**: 配置文件加载
- **logger.py**: 日志记录

## 技术栈

- **基座模型**: Qwen2.5 (0.5B/1.5B)
- **训练框架**: Unsloth + QLoRA
- **量化**: 4-bit (bitsandbytes)
- **UI框架**: Gradio
- **配置管理**: PyYAML

## 工作流程

1. **数据准备**: 上传文档 → 解析 → 蒸馏 → JSONL格式
2. **模型训练**: 加载基座模型 → QLoRA微调 → 保存权重
3. **模型导出**: 合并权重 → 导出格式 → 验证
4. **模型推理**: 加载模型 → 对话交互 → 生成回复
