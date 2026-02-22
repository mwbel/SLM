# 数据蒸馏模块使用指南

## 功能说明

数据蒸馏模块使用 Gemini 1.5 Flash API 从文档中提取知识并生成训练数据。

## 安装依赖

```bash
pip install google-generativeai PyMuPDF pdfminer.six
```

## 快速开始

### 1. 获取 Gemini API Key

访问 [Google AI Studio](https://makersuite.google.com/app/apikey) 获取 API 密钥。

### 2. 基本使用

```python
from src.data_prep import DataDistiller

# 初始化蒸馏器
api_key = "YOUR_GEMINI_API_KEY"
distiller = DataDistiller(api_key)

# 处理单个文件
output_file = distiller.process_file(
    file_path="data/example.pdf",
    output_dir="data",
    num_pairs=15  # 生成15组对话对
)

print(f"蒸馏完成: {output_file}")
```

### 3. 批量处理

```python
# 批量处理目录中的所有文件
output_files = distiller.process_directory(
    input_dir="data/raw",
    output_dir="data/processed",
    num_pairs=10
)

print(f"处理完成，共生成 {len(output_files)} 个文件")
```

### 4. 单独使用函数

```python
from src.data_prep import extract_text, distill_with_gemini, save_as_jsonl

# 提取文本
text = extract_text("data/document.pdf")

# 蒸馏数据
data = distill_with_gemini(text, api_key="YOUR_API_KEY", num_pairs=10)

# 保存为JSONL
save_as_jsonl(data, "data/output.jsonl")
```

## 输出格式

生成的 JSONL 文件格式：

```jsonl
{"instruction": "什么是机器学习？", "input": "", "output": "机器学习是人工智能的一个分支..."}
{"instruction": "如何开始学习深度学习？", "input": "", "output": "开始学习深度学习需要..."}
```

## 支持的文件格式

- PDF (.pdf) - 使用 PyMuPDF 或 pdfminer.six
- TXT (.txt) - 纯文本文件

## 注意事项

1. API 密钥安全：不要将 API 密钥硬编码在代码中，建议使用环境变量
2. 文本长度：Gemini 1.5 Flash 支持长文本，但建议单次处理不超过 100 页
3. 成本控制：注意 API 调用次数和 token 消耗
4. 输出质量：生成的对话对数量和质量取决于输入文本的内容

## 环境变量配置

```bash
# 设置环境变量
export GEMINI_API_KEY="your_api_key_here"
```

```python
import os
from src.data_prep import DataDistiller

# 从环境变量读取
api_key = os.getenv("GEMINI_API_KEY")
distiller = DataDistiller(api_key)
```

## 错误处理

```python
try:
    output_file = distiller.process_file("data/example.pdf")
except FileNotFoundError:
    print("文件不存在")
except ValueError as e:
    print(f"文件格式错误: {e}")
except Exception as e:
    print(f"处理失败: {e}")
```
