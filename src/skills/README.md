# Skill 系统使用文档

## 概述

Skill 系统是一个模块化的文档处理框架，将复杂的数据处理流程解耦为独立的组件。每个 Skill 负责特定的功能，可以灵活组合使用。

## 系统架构

```
┌─────────────────────────────────────────────────────────┐
│                    WorkflowManager                       │
│              (流程控制器 + 断点续传)                      │
└─────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        ▼                   ▼                   ▼
┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│FileRouter    │   │NativeParser  │   │OCRParser     │
│(文件路由)    │──▶│(原生解析)    │   │(OCR解析)     │
└──────────────┘   └──────────────┘   └──────────────┘
                            │                   │
                            └─────────┬─────────┘
                                      ▼
                            ┌──────────────┐
                            │SmartChunker  │
                            │(智能切分)    │
                            └──────────────┘
                                      │
                                      ▼
                            ┌──────────────┐
                            │   Chunks     │
                            │(切分结果)    │
                            └──────────────┘
```

## 核心组件

### 1. BaseSkill (基础类)

所有 Skill 的抽象基类，提供：
- 统一的执行接口 (`execute()`)
- 自动日志记录
- 错误捕获与处理
- 性能统计

```python
from src.skills import BaseSkill

class MyCustomSkill(BaseSkill):
    async def execute(self, input_data, **kwargs):
        # 实现你的逻辑
        return result
```

### 2. FileRouterSkill (文件路由)

**功能：**
- 识别文件类型（.txt, .md, .docx, .pdf, .png, .jpg）
- 检测 PDF 是否为扫描版（读取前 N 页判断字符数）
- 推荐合适的解析器

**使用示例：**
```python
from src.skills import FileRouterSkill

router = FileRouterSkill(
    scanned_pdf_threshold=100,  # 字符数阈值
    check_pages=2               # 检测页数
)

result = await router.run("data/document.pdf")
# result['data']['recommended_parser']  # 'native' 或 'ocr'
```

### 3. NativeParserSkill (原生解析)

**功能：**
- 解析纯文本 (.txt)
- 解析 Markdown (.md) - 提取标题结构
- 解析 Word (.docx) - 保留标题层级
- 解析原生 PDF (.pdf) - 保持段落逻辑

**使用示例：**
```python
from src.skills import NativeParserSkill

parser = NativeParserSkill(preserve_formatting=True)

result = await parser.run("data/document.docx")
# result['data']['content']    # 文本内容
# result['data']['structure']  # 文档结构
```

### 4. OCRParserSkill (OCR 解析)

**功能：**
- 支持 MinerU 和 PaddleOCR 两种引擎
- 分批处理大文件（防止内存溢出）
- 输出 Markdown 格式
- **支持断点续传**（处理中断后可继续）

**使用示例：**
```python
from src.skills import OCRParserSkill

parser = OCRParserSkill(
    ocr_engine='paddleocr',      # 或 'mineru'
    batch_size=10,               # 每批处理 10 页
    output_format='markdown',
    checkpoint_dir='.checkpoints'
)

# 处理大文件，支持断点续传
result = await parser.run(
    "data/scanned_114_pages.pdf",
    resume=True  # 如果中断，下次从断点继续
)
```

**断点续传机制：**
- 每处理完一批页面，自动保存进度
- 如果处理失败，下次运行时自动从上次位置继续
- 处理完成后自动清理断点文件

### 5. SmartChunkerSkill (智能切分)

**功能：**
- 支持多种切分策略（smart, sentence, paragraph, fixed）
- 智能识别段落和句子边界
- 支持自定义 chunk_size 和 overlap
- 保留文档结构信息

**使用示例：**
```python
from src.skills import SmartChunkerSkill

chunker = SmartChunkerSkill(
    chunk_size=1000,           # 每块 1000 字符
    overlap=200,               # 重叠 200 字符
    strategy='smart',          # 智能切分
    respect_structure=True     # 尊重文档结构
)

result = await chunker.run(parse_data)
# result['data']['chunks']  # 切分后的块列表
```

**切分策略对比：**
- `smart`: 优先在段落/句子边界切分（推荐）
- `sentence`: 按句子切分
- `paragraph`: 按段落切分
- `fixed`: 固定长度切分（不考虑语义）

### 6. WorkflowManager (流程控制器)

**功能：**
- 自动串联所有 Skill
- 支持工作流级别的断点续传
- 生成详细的处理报告
- 支持批量处理

**使用示例：**
```python
from src.skills import WorkflowManager

manager = WorkflowManager(
    checkpoint_dir='.workflow_checkpoints',
    enable_checkpoint=True
)

# 处理单个文件
result = await manager.process_file(
    file_path="data/document.pdf",
    chunk_size=1000,
    overlap=200,
    chunking_strategy='smart',
    resume=True
)

# 批量处理目录
batch_result = await manager.process_directory(
    input_dir="data/documents",
    output_dir="data/output",
    chunk_size=1000,
    overlap=200
)
```

## 快速开始

### 安装依赖

```bash
# 基础依赖
pip install PyMuPDF python-docx

# OCR 依赖（根据需要选择）
pip install paddleocr  # PaddleOCR
pip install magic-pdf   # MinerU
```

### 最简单的使用方式

```python
import asyncio
from src.skills import WorkflowManager

async def main():
    manager = WorkflowManager()

    result = await manager.process_file(
        file_path="your_document.pdf",
        chunk_size=1000,
        overlap=200
    )

    if result['success']:
        print(f"成功处理，生成 {len(result['chunks'])} 个块")

        # 使用切分结果
        for chunk in result['chunks']:
            print(f"Chunk {chunk['chunk_id']}: {chunk['text'][:100]}...")

asyncio.run(main())
```

## 高级用法

### 1. 自定义工作流

如果需要更细粒度的控制，可以手动串联 Skills：

```python
from src.skills import (
    FileRouterSkill,
    NativeParserSkill,
    OCRParserSkill,
    SmartChunkerSkill
)

# Step 1: 路由
router = FileRouterSkill()
route_result = await router.run(file_path)

# Step 2: 解析
if route_result['data']['recommended_parser'] == 'ocr':
    parser = OCRParserSkill()
else:
    parser = NativeParserSkill()

parse_result = await parser.run(route_result['data'])

# Step 3: 切分
chunker = SmartChunkerSkill(chunk_size=800, overlap=150)
chunk_result = await chunker.run(parse_result['data'])
```

### 2. 处理超大文件（114 页 PDF）

```python
from src.skills import OCRParserSkill

# 配置 OCR 解析器
parser = OCRParserSkill(
    ocr_engine='paddleocr',
    batch_size=10,  # 每批 10 页，防止内存溢出
    checkpoint_dir='.checkpoints'
)

# 处理大文件
result = await parser.run(
    "large_document_114_pages.pdf",
    resume=True  # 支持断点续传
)

# 如果处理到第 50 页时失败，重新运行会从第 50 页继续
```

### 3. 对接 DataDistiller

切分完成后，可以直接对接现有的 DataDistiller：

```python
from src.skills import WorkflowManager
from src.data_prep.distiller import DataDistiller

# Step 1: 使用 Skill 系统处理文档
manager = WorkflowManager()
result = await manager.process_file("document.pdf")

# Step 2: 对每个 chunk 进行知识蒸馏
distiller = DataDistiller()

for chunk in result['chunks']:
    chunk_text = chunk['text']

    # 使用 Gemini 进行知识蒸馏
    distilled_data = distill_with_gemini(
        text=chunk_text,
        api_key="your_api_key",
        num_pairs=10
    )

    # 保存结果
    save_as_jsonl(distilled_data, f"output/chunk_{chunk['chunk_id']}.jsonl")
```

## 性能统计

每个 Skill 都会自动记录性能统计：

```python
skill = SmartChunkerSkill()

# 执行多次
await skill.run(data1)
await skill.run(data2)

# 查看统计
stats = skill.get_stats()
print(f"总执行次数: {stats['total_executions']}")
print(f"成功次数: {stats['success_count']}")
print(f"平均耗时: {stats['average_time']} 秒")
```

## 错误处理

所有 Skill 都有统一的错误处理机制：

```python
result = await skill.run(input_data)

if result['success']:
    data = result['data']
    # 处理成功
else:
    error = result['error']
    print(f"处理失败: {error}")
    # 可以根据错误类型进行重试或其他处理
```

## 断点续传详解

### OCR 级别的断点续传

```python
parser = OCRParserSkill(checkpoint_dir='.checkpoints')

# 第一次运行：处理到第 50 页时失败
result = await parser.run("large.pdf", resume=True)
# 断点文件保存在 .checkpoints/large_ocr_checkpoint.json

# 第二次运行：自动从第 50 页继续
result = await parser.run("large.pdf", resume=True)
```

### 工作流级别的断点续传

```python
manager = WorkflowManager(enable_checkpoint=True)

# 第一次运行：在解析步骤失败
result = await manager.process_file("doc.pdf", resume=True)
# 断点文件保存在 .workflow_checkpoints/doc_workflow.json

# 第二次运行：自动从解析步骤继续
result = await manager.process_file("doc.pdf", resume=True)
```

## 最佳实践

1. **处理小文件（< 20 页）**：直接使用 WorkflowManager
2. **处理大文件（> 100 页）**：使用 OCRParserSkill 的分批处理
3. **批量处理**：使用 WorkflowManager.process_directory()
4. **自定义需求**：手动串联 Skills
5. **生产环境**：启用断点续传，设置合理的 batch_size

## 常见问题

### Q: 如何判断 PDF 是扫描版还是原生版？
A: FileRouterSkill 会自动检测。它读取前 2 页，如果平均字符数 < 100，判定为扫描版。

### Q: OCR 处理很慢怎么办？
A: 调整 batch_size 参数，在内存和速度之间找平衡。推荐值：10-20 页/批。

### Q: 如何自定义切分逻辑？
A: 继承 SmartChunkerSkill 并重写 execute() 方法，或者直接使用不同的 strategy 参数。

### Q: 断点文件在哪里？
A: 默认在 `.checkpoints/` 和 `.workflow_checkpoints/` 目录。可以通过参数自定义。

### Q: 如何清理断点文件？
A: 处理成功后会自动清理。手动清理：删除对应的 JSON 文件即可。

## 示例代码

完整的示例代码请参考：
- `src/data_prep/skills/examples.py` - 5 个完整示例
- 每个 Skill 文件的 `if __name__ == "__main__"` 部分

## 技术支持

如有问题，请查看：
1. 代码中的详细注释
2. 每个 Skill 的 docstring
3. examples.py 中的示例代码
