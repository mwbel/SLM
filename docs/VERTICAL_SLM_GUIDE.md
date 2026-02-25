# 垂直小模型构建指南

**项目目标**: 构建面向特定领域的轻量级垂直小模型（Vertical Small Language Model）

**文档版本**: v1.0
**更新日期**: 2026-02-25
**当前状态**: 原型验证阶段

---

## 目录

- [1. 项目概述](#1-项目概述)
- [2. 技术架构](#2-技术架构)
- [3. 核心模块详解](#3-核心模块详解)
- [4. 知识蒸馏流程](#4-知识蒸馏流程)
- [5. 模型训练流程](#5-模型训练流程)
- [6. 关键问题与解决方案](#6-关键问题与解决方案)
- [7. 当前状态分析](#7-当前状态分析)
- [8. 针对不同领域的优化方案](#8-针对不同领域的优化方案)
- [9. 下一步行动计划](#9-下一步行动计划)
- [10. 参考资源](#10-参考资源)

---

## 1. 项目概述

### 1.1 项目定位

构建一个**轻量级、可定制、领域专用**的小模型系统，用于：
- 降低大模型部署成本
- 提供准确的专业知识问答
- 支持离线部署和数据隐私保护
- 快速适配不同垂直领域

### 1.2 核心特性

- ✅ **轻量部署**: 支持0.5B-3B参数模型
- ✅ **领域定制**: 基于领域文档自动生成训练数据
- ✅ **完整流程**: 文档处理→数据蒸馏→模型训练→模型部署
- ✅ **友好界面**: Gradio Web UI，无代码操作
- ✅ **多源支持**: 支持PDF、Markdown、文本等多种格式

### 1.3 当前测试领域

- **财务报销制度**（华东师范大学财务细则）
- **文档大小**: 约50页PDF
- **训练样本**: 217个问答对
- **基座模型**: Qwen2.5-0.5B (462MB)

---

## 2. 技术架构

### 2.1 系统架构图

```
┌─────────────────────────────────────────────────────────────┐
│                     用户界面层 (Gradio Web UI)              │
├─────────────────────────────────────────────────────────────┤
│  数据蒸馏模块  │  模型训练模块  │  模型推理模块  │  模型导出  │
├─────────────────────────────────────────────────────────────┤
│  文件加载  │  数据处理  │  知识蒸馏  │  指令微调  │  LoRA  │
├─────────────────────────────────────────────────────────────┤
│  工具层: API密钥轮换  │  配置管理  │  日志记录              │
├─────────────────────────────────────────────────────────────┤
│  基础设施: HuggingFace Transformers  │  PEFT  │  ModelScope│
└─────────────────────────────────────────────────────────────┘
```

### 2.2 技术栈

| 类别 | 技术选型 | 版本 | 说明 |
|------|---------|------|------|
| **基座模型** | Qwen2.5-0.5B/1.5B/3B | - | 通义千问系列，开源商用友好 |
| **训练框架** | Transformers | 4.x | HuggingFace主流框架 |
| **参数高效训练** | PEFT (LoRA) | 0.18.1 | 只训练少量参数，降低成本 |
| **模型下载** | ModelScope | - | 阿里云镜像，国内快速 |
| **Web界面** | Gradio | 4.x | 快速构建ML应用界面 |
| **数据格式** | JSONL | - | 轻量级训练数据格式 |
| **大模型API** | Google Gemini 2.5 | - | 用于数据蒸馏 |

### 2.3 目录结构

```
垂直小模型/
├── src/                      # 源代码
│   ├── data_prep/           # 数据准备
│   │   ├── distiller.py     # 知识蒸馏器
│   │   ├── file_loader.py   # 文件加载器
│   │   └── data_processor.py # 数据处理器
│   ├── training/            # 模型训练
│   │   └── trainer.py       # 训练器
│   ├── inference/           # 模型推理
│   │   └── inferencer.py    # 推理器
│   ├── ui/                  # 用户界面
│   │   └── app.py           # Gradio应用
│   └── utils/               # 工具函数
├── data/                    # 数据目录
│   └── 报销细则_distilled_chunked.jsonl  # 训练数据
├── models/                  # 模型目录
│   └── Qwen/Qwen2.5-0.5B/   # 基座模型
├── outputs/                 # 输出目录
│   ├── trained_model/       # 训练好的模型
│   └── checkpoint-*/        # 训练检查点
├── config.yaml              # 配置文件
├── .env                     # 环境变量（API密钥）
└── main.py                  # 入口文件
```

---

## 3. 核心模块详解

### 3.1 数据准备模块 (`src/data_prep/`)

#### 3.1.1 文件加载器 (`file_loader.py`)

**功能**: 加载不同格式的文档

**支持的格式**:
- PDF (包括扫描PDF，需OCR)
- Markdown (.md)
- 纯文本 (.txt)
- Word文档 (.docx)

**关键代码**:
```python
class FileLoader:
    def load_file(self, file_path: str) -> str:
        """根据文件类型加载文件内容"""
        ext = Path(file_path).suffix.lower()

        if ext == '.pdf':
            return self._load_pdf(file_path)
        elif ext == '.md':
            return self._load_markdown(file_path)
        # ... 其他格式
```

#### 3.1.2 知识蒸馏器 (`distiller.py`)

**功能**: 使用大模型将领域文档转换为问答对

**工作流程**:
1. **文档分块**: 将长文档切分为小块（每块约2000字）
2. **问题生成**: 自动生成针对每个知识块的问题
3. **答案生成**: 基于文档生成准确答案
4. **质量检验**: 自动检验问答质量

**关键参数**:
```python
# API配置
DEFAULT_API_KEYS = [...]  # 支持多个API密钥轮换
BATCH_SIZE = 5            # 批处理大小

# 蒸馏参数
CHUNK_SIZE = 2000         # 文档块大小
CHUNK_OVERLAP = 200       # 块重叠
QUESTIONS_PER_CHUNK = 3   # 每块生成的问题数
```

**API密钥轮换机制**:
```python
class APIKeyRotator:
    """自动轮换多个API密钥，避免配额限制"""
    def __init__(self, api_keys):
        self.api_keys = api_keys
        self.current_index = 0
        self.failure_counts = [0] * len(api_keys)

    def get_next_key(self):
        """获取下一个可用的API密钥"""
        # 智能选择失败次数最少的密钥
```

### 3.2 模型训练模块 (`src/training/`)

#### 3.2.1 训练器 (`trainer.py`)

**核心功能**: QLoRA参数高效训练

**关键特性**:
1. **自动设备检测**: CUDA GPU > Apple MPS > CPU
2. **本地模型优先**: 优先使用本地下载的模型
3. **LoRA微调**: 只训练0.5%的参数
4. **梯度累积**: 模拟大批次训练

**训练配置** (`config.yaml`):
```yaml
model:
  base_model: "models/Qwen/Qwen2.5-0.5B"
  max_seq_length: 512

lora:
  rank: 8           # LoRA秩（控制参数量）
  alpha: 16         # LoRA缩放因子
  dropout: 0.05     # Dropout率

training:
  batch_size: 1
  learning_rate: 0.0002
  num_epochs: 3
  gradient_accumulation_steps: 4  # 有效批次大小 = 1×4 = 4
```

**关键修复**: Labels Masking（已修复）

```python
# ❌ 错误的做法（旧代码）
tokenized["labels"] = tokenized["input_ids"].copy()

# ✅ 正确的做法（当前代码）
# 只训练"回答"部分，将"问题"部分mask掉
labels = tokenized["input_ids"].copy()
prompt_length = len(self.tokenizer(f"问题：{instruction}\n回答：",
                                  add_special_tokens=False)["input_ids"])
labels[:prompt_length] = [-100] * prompt_length
tokenized["labels"] = labels
```

### 3.3 模型推理模块 (`src/inference/`)

#### 3.3.1 推理器 (`inferencer.py`)

**功能**: 加载训练好的模型进行推理

**特性**:
- LoRA权重合并
- 支持批处理推理
- 自动设备管理
- 生成参数优化

**生成参数**:
```python
def generate(
    self,
    prompt: str,
    max_new_tokens: int = 256,
    temperature: float = 0.7,    # 控制随机性
    top_p: float = 0.9,          # nucleus sampling
    top_k: int = 50,             # top-k sampling
    repetition_penalty: float = 1.2,  # 重复惩罚
):
```

### 3.4 用户界面模块 (`src/ui/`)

#### 3.4.1 Gradio应用 (`app.py`)

**功能**: 提供友好的Web操作界面

**主要功能页**:

1. **数据蒸馏页**
   - 上传文档
   - 选择参考文档
   - 配置蒸馏参数
   - 启动蒸馏任务
   - 下载训练数据

2. **模型训练页**
   - 选择训练数据
   - 配置训练参数
   - 启动训练
   - 监控训练进度

3. **模型对话页**
   - 加载训练好的模型
   - 实时对话测试
   - 查看模型状态

---

## 4. 知识蒸馏流程

### 4.1 完整流程图

```
┌──────────────┐
│ 1. 上传文档  │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ 2. 文档分块  │ ← 将长文档切分为小块
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ 3. 问题生成  │ ← LLM自动生成问题
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ 4. 答案生成  │ ← LLM基于文档生成答案
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ 5. 质量检验  │ ← 自动过滤低质量问答
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ 6. 保存数据  │ → JSONL格式
└──────────────┘
```

### 4.2 详细步骤

#### 步骤1: 文档预处理

```python
# 1. 加载文档
loader = FileLoader()
document = loader.load_file("财务细则.pdf")

# 2. 文档分块
chunks = split_document(
    document,
    chunk_size=2000,      # 每块2000字符
    overlap=200,          # 块之间重叠200字符
    separator="\n\n"      # 按段落分割
)
```

#### 步骤2: 问答生成

```python
# 3. 使用大模型生成问答对
distiller = DataDistiller()

for chunk in chunks:
    # 生成问题
    questions = distiller.generate_questions(chunk, count=3)

    # 生成答案
    for question in questions:
        answer = distiller.generate_answer(
            question=question,
            context=chunk,
            reference_doc="财务细则.pdf"
        )

        # 保存
        save_qa_pair(question, answer)
```

#### 步骤3: 数据格式

生成的JSONL格式:
```json
{
  "instruction": "对于课题协作费、制作费、材料费等费用，华东师范大学对协议和合同的签订金额有什么要求？",
  "input": "",
  "output": "1. 课题协作费等：同一家单位发票单张或累计金额3000元及以上需要协议，10000元及以上需要合同。\n2. 购买物品为设备：10000元以上需要协议，30000元以上需要合同。"
}
```

### 4.3 蒸馏质量控制

**自动检验指标**:
1. **答案长度**: 50-500字符
2. **关键词匹配**: 答案必须包含文档中的关键信息
3. **格式规范**: 符合预期格式（如包含数字、列表等）

**质量过滤示例**:
```python
def validate_qa_pair(question: str, answer: str) -> bool:
    # 检查答案是否太短
    if len(answer) < 50:
        return False

    # 检查是否包含具体信息
    if not any(char.isdigit() for char in answer):
        return False

    # 检查是否包含"不知道"等拒绝回答
    reject_phrases = ["不知道", "无法确定", "不清楚"]
    if any(phrase in answer for phrase in reject_phrases):
        return False

    return True
```

---

## 5. 模型训练流程

### 5.1 训练流程图

```
┌──────────────┐
│ 1. 加载配置  │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ 2. 加载数据  │ ← JSONL格式的问答对
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ 3. 初始化模型│ ← 基座模型 + LoRA配置
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ 4. Token化   │ ← 问题：xxx\n回答：xxx格式
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ 5. 设置Labels│ ← Mask问题部分，只训练回答部分
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ 6. 训练循环  │ ← QLoRA高效训练
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ 7. 保存模型  │ → LoRA权重文件
└──────────────┘
```

### 5.2 训练详细步骤

#### 步骤1: 环境准备

```bash
# 安装依赖
pip3 install torch torchvision torchaudio
pip3 install transformers peft datasets
pip3 install accelerate
pip3 install modelscope  # 国内快速下载模型

# 下载基座模型（使用ModelScope）
python3 download_model_modelscope.py
```

#### 步骤2: 数据准备

```python
import json

# 加载JSONL训练数据
train_data = []
with open("data/训练数据.jsonl", "r") as f:
    for line in f:
        train_data.append(json.loads(line))

print(f"加载了 {len(train_data)} 个训练样本")
```

#### 步骤3: 训练配置

```python
import yaml
from training import Trainer

# 加载配置
with open("config.yaml") as f:
    config = yaml.safe_load(f)

# 初始化训练器
trainer = Trainer(
    model_name="models/Qwen/Qwen2.5-0.5B",
    config=config
)
```

#### 步骤4: 开始训练

```python
# 执行训练
trainer.train(train_data)

# 训练过程：
# - Epoch 1/3: Loss从15.5降到2.3
# - Epoch 2/3: Loss从2.3降到0.8
# - Epoch 3/3: Loss从0.8降到0.26
```

#### 步骤5: 保存模型

```python
# 保存训练好的LoRA权重
trainer.save_model("outputs/trained_model")

# 生成的文件：
# - adapter_config.json    (LoRA配置)
# - adapter_model.safetensors (LoRA权重，约4MB)
# - tokenizer_config.json  (分词器配置)
# - tokenizer.json         (分词器文件)
```

### 5.3 训练技巧

#### 技巧1: 梯度累积

```python
# 模拟大批次训练，节省显存
gradient_accumulation_steps: 4
# 实际批次大小 = batch_size × gradient_accumulation_steps
#              = 1 × 4 = 4
```

#### 技巧2: 学习率调度

```python
# 带warmup的学习率调度
warmup_steps: 10    # 前10步线性增加学习率
learning_rate: 0.0002  # 峰值学习率
```

#### 技巧3: 早停机制

```python
# 监控验证loss，提前停止
save_strategy: "epoch"
save_total_limit: 2  # 只保留最近2个checkpoint
```

---

## 6. 关键问题与解决方案

### 6.1 问题1: 训练代码Labels错误 ✅ 已解决

**问题描述**:
原代码将整个序列（包括问题部分）都设为训练目标，导致模型学习预测问题而非答案。

**错误代码**:
```python
tokenized["labels"] = tokenized["input_ids"].copy()
```

**解决方案**:
```python
# 只训练"回答"部分
labels = tokenized["input_ids"].copy()
prompt_length = len(self.tokenizer(f"问题：{instruction}\n回答：",
                                  add_special_tokens=False)["input_ids"])
labels[:prompt_length] = [-100] * prompt_length  # Mask问题部分
tokenized["labels"] = labels
```

**影响**: Loss从15.5成功降到0.26，训练收敛正常。

---

### 6.2 问题2: 模型无法准确回答问题 ⚠️ 部分解决

**问题描述**:
即使Loss降到0.26，模型仍产生幻觉，回答不正确。

**测试结果**:
```
问题: 同一家单位发票单张多少需要合同？
预期: 3000元需要协议，10000元需要合同
实际: 原则上不超过项目总经费的10%  ❌
```

**根本原因分析**:
1. **模型容量不足**: 0.5B参数太少，无法有效记忆专业知识
2. **训练数据不足**: 仅217个样本，覆盖面不够
3. **过拟合**: Loss虽然降低，但模型记住了错误模式

**解决方案**:
1. ✅ 使用更大模型（1.5B或3B）
2. ✅ 增加训练数据（500-1000条）
3. ✅ 调整训练参数（降低学习率、增加epochs）

---

### 6.3 问题3: 网络请求错误 ✅ 已解决

**问题描述**:
```
RuntimeError: Cannot send a request, as the client has been closed.
```

**原因**:
- UI默认使用HuggingFace模型ID，触发网络请求
- 本地模型路径配置不正确

**解决方案**:
```python
# 1. 更新BASE_MODELS列表
BASE_MODELS = [
    "models/Qwen/Qwen2.5-0.5B",  # 本地路径优先
    "Qwen/Qwen2.5-0.5B",         # HuggingFace备用
]

# 2. 添加local_files_only=True
self.model = AutoModelForCausalLM.from_pretrained(
    model_path,
    local_files_only=True,  # 强制使用本地文件
    ...
)
```

---

### 6.4 问题4: API密钥安全 ✅ 已解决

**问题描述**:
用户之前将API密钥硬编码在配置文件中并推送到GitHub，导致密钥泄露。

**解决方案**:
1. **迁移到环境变量**
```python
# .env文件
GEMINI_API_KEY_1=xxx
GEMINI_API_KEY_2=yyy
ZHIPU_API_KEY=zzz

# 代码中读取
import os
api_key = os.getenv("GEMINI_API_KEY_1")
```

2. **更新.gitignore**
```
.env
.env.local
config/api_config.json
config/api_keys.json
```

3. **提供.env.example模板**
```bash
# .env.example
GEMINI_API_KEY_1=your_api_key_here
GEMINI_API_KEY_2=your_api_key_here
```

---

## 7. 当前状态分析

### 7.1 已完成功能 ✅

| 模块 | 功能 | 状态 | 完成度 |
|------|------|------|--------|
| **数据准备** | PDF/Markdown加载 | ✅ 完成 | 100% |
| | OCR文字识别 | ✅ 完成 | 100% |
| | 文档分块 | ✅ 完成 | 100% |
| **知识蒸馏** | API密钥轮换 | ✅ 完成 | 100% |
| | 问答生成 | ✅ 完成 | 100% |
| | 质量过滤 | ✅ 完成 | 80% |
| **模型训练** | QLoRA训练 | ✅ 完成 | 100% |
| | Labels Masking | ✅ 已修复 | 100% |
| | 多设备支持 | ✅ 完成 | 100% |
| **模型推理** | LoRA加载 | ✅ 完成 | 100% |
| | 批处理推理 | ✅ 完成 | 100% |
| **Web界面** | Gradio UI | ✅ 完成 | 90% |
| | 进度显示 | ✅ 完成 | 90% |
| **模型导出** | GGUF格式 | ✅ 完成 | 100% |
| | llama.cpp兼容 | ✅ 完成 | 100% |

### 7.2 当前限制 ❌

| 问题 | 影响 | 优先级 |
|------|------|--------|
| **0.5B模型能力不足** | 无法准确回答专业问题 | 🔴 高 |
| **训练数据量少** | 仅217条，过拟合风险 | 🔴 高 |
| **蒸馏质量不稳定** | 偶尔生成低质量问答 | 🟡 中 |
| **推理速度慢** | MPS加速不够快 | 🟢 低 |
| **无评估指标** | 缺少量化评估标准 | 🟡 中 |

### 7.3 性能指标

**训练性能** (Qwen2.5-0.5B, Apple MPS):
```
数据量: 217条
训练时间: ~10分钟
最终Loss: 0.26
模型大小: 462MB (基座) + 4MB (LoRA)
```

**推理性能**:
```
加载时间: ~30秒
生成速度: ~5字/秒 (MPS)
显存占用: ~2GB
```

**质量评估** (基于3个测试问题):
```
准确率: 0/3 (0%)
包含关键信息: 0/3 (0%)
格式正确: 3/3 (100%)
```

---

## 8. 针对不同领域的优化方案

### 8.1 通用优化框架

不同领域的垂直模型构建，需要考虑以下维度：

```
┌─────────────────────────────────────────────┐
│              领域特征分析                    │
├─────────────────────────────────────────────┤
│ 数据特征: 文档类型/大小/结构/更新频率         │
│ 任务特征: 问答/摘要/生成/分类/抽取            │
│ 精度要求: 严格事实/创造性/流畅性             │
│ 部署环境: 云端/边缘设备/移动端               │
└─────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────┐
│              技术方案选择                    │
├─────────────────────────────────────────────┤
│ 模型规模: 0.5B / 1.5B / 3B / 7B            │
│ 训练策略: LoRA / Full Fine-tuning / Prefix  │
│ 数据增强: 回译 / 同义词替换 / 生成式增强     │
│ 评估方法: 准确率 / ROUGE / 人工评估          │
└─────────────────────────────────────────────┘
```

### 8.2 不同领域的定制方案

#### 领域1: 财务/法律/医疗（高精度要求）

**特征**:
- 要求100%准确，不能有幻觉
- 文档结构化强
- 专业术语多

**推荐方案**:

```yaml
模型选择: Qwen2.5-3B 或 7B
训练数据: 1000+ 条高质量问答
训练策略:
  - LoRA rank: 16
  - Learning rate: 0.0001
  - Epochs: 5-10
  - Batch size: 4-8
质量保证:
  - 人工审核100%训练数据
  - 引入RAG检索验证
  - 设置置信度阈值
```

**数据增强**:
```python
# 对每个知识点生成多个变体问题
original = "发票金额3000元以上需要什么？"
variations = [
    "发票超过3000元需要什么材料？",
    "3000元以上的发票报销要求是什么？",
    "大额发票（>3000元）需要哪些手续？",
    "什么情况下发票需要附加协议？"
]
```

**评估指标**:
- 事实准确率: >95%
- 关键信息召回率: >90%
- 无幻觉率: 100%

---

#### 领域2: 教育/客服/咨询（中等精度）

**特征**:
- 可以有一定灵活性
- 需要多轮对话
- 用户体验重要

**推荐方案**:

```yaml
模型选择: Qwen2.5-1.5B 或 3B
训练数据: 500-1000 条
训练策略:
  - LoRA rank: 8-12
  - Learning rate: 0.0002
  - Epochs: 3-5
  - 温度: 0.7-0.9
质量保证:
  - 抽样审核20%数据
  - A/B测试对话质量
  - 用户反馈收集
```

**对话优化**:
```python
# 多轮对话训练
conversation = [
    {"role": "user", "content": "如何申请报销？"},
    {"role": "assistant", "content": "请提供以下材料..."},
    {"role": "user", "content": "发票丢了怎么办？"},
    {"role": "assistant", "content": "需要到财务处开具证明..."}
]
```

---

#### 领域3: 内容创作/营销（创意性）

**特征**:
- 需要创造性和多样性
- 准确性要求相对宽松
- 风格多样

**推荐方案**:

```yaml
模型选择: Qwen2.5-1.5B（够用）
训练数据: 300-500 条 + 大量未标注文本
训练策略:
  - 两阶段训练
    1. 领域预训练（未标注文本）
    2. 风格微调（标注样本）
  - 温度: 0.8-1.0
  - Top-p: 0.95
质量保证:
  - 多样性评估
  - 创造性评分
  - A/B测试用户偏好
```

---

#### 领域4: 技术/编程（精确性）

**特征**:
- 代码必须可运行
- API必须准确
- 版本敏感

**推荐方案**:

```yaml
模型选择: Qwen2.5-3B-Coder（专用代码模型）
训练数据: 包含可执行代码的样本
训练策略:
  - 语法验证
  - 单元测试验证
  - 添加代码注释
质量保证:
  - 代码执行测试
  - API文档对比
  - 版本兼容性检查
```

---

### 8.3 数据量指南

| 领域类型 | 最小样本 | 推荐样本 | 理想样本 |
|---------|---------|---------|---------|
| **高精度**（财务/法律/医疗） | 500 | 1000-2000 | 5000+ |
| **中等精度**（教育/客服） | 200 | 500-1000 | 2000+ |
| **创意性**（营销/创作） | 100 | 300-500 | 1000+ |
| **技术性**（编程/API） | 300 | 800-1500 | 3000+ |

### 8.4 模型规模选择指南

| 模型规模 | 参数量 | 大小 | 适用场景 | 推理速度 |
|---------|--------|------|---------|---------|
| **0.5B** | 462M | ~500MB | 简单问答、边缘设备 | 最快 |
| **1.5B** | 1.5B | ~1.2GB | 通用垂直领域、中等精度 | 快 |
| **3B** | 3B | ~2.4GB | 复杂推理、高精度要求 | 中等 |
| **7B** | 7B | ~5GB | 生产级应用、最佳质量 | 慢 |

---

## 9. 下一步行动计划

### 9.1 短期优化（1-2周）⚡

#### 优先级1: 升级基座模型 🔴

**目标**: 将0.5B升级到1.5B，提升模型能力

**步骤**:
```bash
# 1. 下载1.5B模型
python3 -c "
from modelscope import snapshot_download
snapshot_download('Qwen/Qwen2.5-1.5B', cache_dir='./models')
"

# 2. 更新配置
vim config.yaml  # 修改 base_model: models/Qwen/Qwen2.5-1.5B

# 3. 重新训练
python3 retrain_model.py

# 4. 测试评估
python3 test_trained_model.py
```

**预期效果**: 准确率从0%提升到50%+

---

#### 优先级2: 增加训练数据 🔴

**目标**: 将217条扩充到500-1000条

**方法**:
1. **数据增强**
```python
# 对现有问题改写
original_q = "发票金额3000元以上需要什么？"
rewritten_qs = augment_question(original_q, methods=[
    "paraphrase",      # 意译
    "change_focus",    # 改变焦点
    "add_context",     # 添加上下文
])
```

2. **人工补充**
   - 梳理知识点清单
   - 人工编写高频问题
   - 覆盖更多场景

3. **重新蒸馏**
   - 调整蒸馏参数
   - 增加每块的问题数
   - 提高答案质量要求

---

#### 优先级3: 优化训练参数 🟡

**目标**: 提升训练稳定性

**调整方案**:
```yaml
# config.yaml 优化版
training:
  learning_rate: 0.0001    # 降低学习率（从0.0002）
  num_epochs: 5            # 增加轮数（从3）
  batch_size: 2            # 增加批次大小（如果显存允许）
  gradient_accumulation_steps: 4
  warmup_ratio: 0.1        # 添加warmup比例
  weight_decay: 0.01       # 添加权重衰减
```

---

### 9.2 中期优化（1个月）🚀

#### 目标1: 实施两阶段训练

**阶段1: 领域预训练（Continual Pre-training）**

```python
# 在原始领域文本上预训练
domain_texts = load_all_pdf_texts(["财务细则.pdf", ...])

# 使用MLM（Masked Language Modeling）目标
trainer.pretrain(
    texts=domain_texts,
    epochs=2,
    learning_rate=0.0001
)
```

**阶段2: 指令微调（Instruction Fine-tuning）**

```python
# 在问答对上微调
trainer.finetune(
    qa_pairs=distilled_data,
    epochs=3,
    learning_rate=0.0002
)
```

**优势**:
- 让模型先学习领域知识结构
- 再学习如何回答问题
- 提升事实准确性

---

#### 目标2: 引入RAG验证

```python
class RAGEnhancedInferencer:
    """RAG增强的推理器"""

    def generate_with_verification(self, question):
        # 1. 生成答案
        answer = self.model.generate(question)

        # 2. 检索相关段落
        relevant_docs = self.retrieve(question, top_k=3)

        # 3. 事实一致性检查
        consistency = self.verify_consistency(answer, relevant_docs)

        if consistency < 0.8:
            # 重新生成或标记不确定
            return self.generate_with_context(question, relevant_docs)

        return answer
```

---

#### 目标3: 建立评估体系

**自动评估指标**:
```python
def evaluate_model(test_set):
    metrics = {
        "accuracy": calculate_accuracy(test_set),      # 准确率
        "recall": calculate_keyword_recall(test_set), # 关键词召回
        "hallucination": detect_hallucination(test_set), # 幻觉率
        "coherence": calculate_coherence(test_set),   # 连贯性
    }
    return metrics
```

**人工评估**:
- 随机抽取50个问题
- 专家打分（1-5分）
- 计算平均分和分布

---

### 9.3 长期规划（3个月）🎯

#### 目标1: 支持多领域

**实现思路**:
```yaml
领域管理:
  财务报销:
    model: models/finance/1.5B
    data: data/finance/
    status: production

  教学管理:
    model: models/education/1.5B
    data: data/education/
    status: training

  客户服务:
    model: models/service/1.5B
    data: data/service/
    status: development
```

**UI改进**:
- 添加领域切换功能
- 每个领域独立配置
- 统一的数据格式

---

#### 目标2: 模型压缩与优化

**目标**: 在保持精度的前提下加速推理

**方法**:
1. **量化**: FP16 → INT8 → INT4
2. **剪枝**: 移除不重要的权重
3. **知识蒸馏**: 大模型 → 小模型
4. **ONNX导出**: 跨平台部署

---

#### 目标3: 生产级部署

**部署架构**:
```
┌─────────────┐
│  Web前端    │ (Gradio/React)
└──────┬──────┘
       │ HTTP
       ▼
┌─────────────┐
│  API网关    │ (FastAPI)
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ 模型服务集群 │ (多实例负载均衡)
│ - Instance1 │
│ - Instance2 │
│ - Instance3 │
└─────────────┘
```

**监控指标**:
- QPS (每秒查询数)
- 延迟 (P50/P95/P99)
- 准确率监控
- 异常告警

---

## 10. 参考资源

### 10.1 推荐阅读

**论文**:
1. **QLoRA**: "QLoRA: Efficient Finetuning of Quantized LLMs" (2023)
2. **Instruction Tuning**: "Fine-tuned Language Models Are Zero-Shot Learners" (2022)
3. **LoRA**: "LoRA: Low-Rank Adaptation of Large Language Models" (2021)

**博客**:
1. HuggingFace PEFT官方文档
2. ModelScope官方文档
3. Qwen模型系列文档

### 10.2 工具推荐

**模型训练**:
- HuggingFace Transformers
- PEFT (LoRA/QLoRA)
- Accelerate (分布式训练)

**数据蒸馏**:
- LangChain (文档处理)
- LlamaIndex (RAG)
- unstructured.io (PDF解析)

**模型部署**:
- FastAPI (API服务)
- Docker (容器化)
- ONNX Runtime (推理加速)

### 10.3 社区资源

- **HuggingFace**: https://huggingface.co/
- **ModelScope**: https://modelscope.cn/
- **GitHub**: 搜索awesome-llm, llm-finetuning

---

## 附录

### A. 快速开始指南

```bash
# 1. 克隆项目
git clone <repository_url>
cd 垂直小模型

# 2. 安装依赖
pip3 install -r requirements.txt

# 3. 配置API密钥
cp .env.example .env
# 编辑.env，填入你的API密钥

# 4. 下载基座模型
python3 download_model_modelscope.py

# 5. 启动Web界面
python3 main.py

# 6. 打开浏览器
# 访问 http://localhost:7860
```

### B. 常见问题FAQ

**Q1: 训练需要什么硬件？**
- A: 最低要求8GB RAM（CPU模式），推荐16GB+，有GPU更佳

**Q2: 可以用其他模型吗？**
- A: 可以，支持所有HuggingFace兼容的模型

**Q3: 如何提升模型准确率？**
- A: 1)使用更大模型 2)增加训练数据 3)优化数据质量

**Q4: 支持多语言吗？**
- A: 基座模型决定，Qwen系列中英双语都支持

### C. 项目检查清单

**准备阶段**:
- [ ] 确定目标领域
- [ ] 收集领域文档
- [ ] 评估数据质量
- [ ] 选择合适模型规模

**开发阶段**:
- [ ] 配置开发环境
- [ ] 准备训练数据
- [ ] 执行模型训练
- [ ] 测试模型效果

**部署阶段**:
- [ ] 性能优化
- [ ] 建立监控体系
- [ ] 用户反馈收集
- [ ] 持续迭代优化

---

**文档结束**

**最后更新**: 2026-02-25
**维护者**: Claude Code Team
**联系方式**: [项目GitHub Issues]
