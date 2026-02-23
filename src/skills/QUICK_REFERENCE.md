# Skill 系统快速参考

## 🚀 5 分钟快速上手

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
        print(f"成功！生成 {len(result['chunks'])} 个块")

asyncio.run(main())
```

---

## 📦 导入速查

### 推荐方式（Facade Pattern）

```python
# 一行导入所有需要的组件
from src.skills import (
    FileRouterSkill,      # 文件路由
    NativeParserSkill,    # 原生解析
    OCRParserSkill,       # OCR 解析
    SmartChunkerSkill,    # 智能切分
    WorkflowManager,      # 工作流管理
    BaseSkillEnhanced,    # 增强版基类
    SkillRegistry,        # 注册中心
    SkillTemplate         # 开发模板
)
```

### 直接导入（不推荐，但可用）

```python
from src.data_prep.skills.classifiers import FileRouterSkill
from src.data_prep.skills.parsers import NativeParserSkill, OCRParserSkill
from src.data_prep.skills.transformers import SmartChunkerSkill
from src.data_prep.skills.workflow import WorkflowManager
```

---

## 🎯 常用场景

### 场景 1: 处理单个文件

```python
from src.skills import WorkflowManager

manager = WorkflowManager()
result = await manager.process_file("document.pdf")
```

### 场景 2: 批量处理目录

```python
from src.skills import WorkflowManager

manager = WorkflowManager()
result = await manager.process_directory(
    input_dir="data/documents",
    output_dir="data/output"
)
```

### 场景 3: 自定义工作流

```python
from src.skills import (
    FileRouterSkill,
    NativeParserSkill,
    SmartChunkerSkill
)

# Step 1: 路由
router = FileRouterSkill()
route_result = await router.run(file_path)

# Step 2: 解析
parser = NativeParserSkill()
parse_result = await parser.run(route_result['data'])

# Step 3: 切分
chunker = SmartChunkerSkill(chunk_size=800)
chunk_result = await chunker.run(parse_result['data'])
```

### 场景 4: OCR 处理大文件（支持断点续传）

```python
from src.skills import OCRParserSkill

parser = OCRParserSkill(
    ocr_engine='paddleocr',
    batch_size=10  # 每批 10 页
)

# 如果中断，下次会从断点继续
result = await parser.run("large_114_pages.pdf", resume=True)
```

---

## 🛠️ 开发新 Skill

### 3 步创建新 Skill

#### 步骤 1: 复制模板

```python
from src.skills import BaseSkillEnhanced

class MyNewSkill(BaseSkillEnhanced):
    def __init__(self, param: str = "default"):
        super().__init__(name="MyNewSkill")
        self.param = param
```

#### 步骤 2: 实现核心逻辑

```python
    async def execute(self, input_data, **kwargs):
        # 你的处理逻辑
        result = process(input_data)
        return result
```

#### 步骤 3: 添加验证（可选）

```python
    def validate_input(self, input_data, **kwargs):
        if not isinstance(input_data, dict):
            return False, "输入必须是字典"
        return True, None
```

---

## 📂 目录结构速查

```
skills/
├── classifiers/        # 文件识别、路由
│   └── file_router_skill.py
├── parsers/            # 文本提取、OCR
│   ├── native_parser_skill.py
│   └── ocr_parser_skill.py
├── transformers/       # 数据转换、切分
│   └── smart_chunker_skill.py
└── workflow/           # 流程控制
    └── workflow_manager.py
```

**规则**: 新 Skill 放入对应的功能目录

---

## 🔍 Skill 分类速查

| 类别 | 用途 | 何时使用 |
|------|------|---------|
| **Classifiers** | 识别、分类、路由 | 需要判断文件类型、决策处理路径 |
| **Parsers** | 提取文本、OCR | 需要从文档中提取内容 |
| **Transformers** | 清洗、切分、转换 | 需要修改或转换数据格式 |
| **Workflow** | 编排、控制 | 需要串联多个 Skill |

---

## ⚙️ 配置参数速查

### FileRouterSkill

```python
FileRouterSkill(
    scanned_pdf_threshold=100,  # 扫描版判定阈值
    check_pages=2               # 检测页数
)
```

### NativeParserSkill

```python
NativeParserSkill(
    preserve_formatting=True    # 是否保留格式
)
```

### OCRParserSkill

```python
OCRParserSkill(
    ocr_engine='paddleocr',     # 'paddleocr' 或 'mineru'
    batch_size=10,              # 批处理大小
    output_format='markdown',   # 输出格式
    checkpoint_dir='.checkpoints'  # 断点目录
)
```

### SmartChunkerSkill

```python
SmartChunkerSkill(
    chunk_size=1000,            # 块大小
    overlap=200,                # 重叠大小
    strategy='smart',           # 'smart', 'sentence', 'paragraph', 'fixed'
    respect_structure=True      # 是否保留结构
)
```

### WorkflowManager

```python
WorkflowManager(
    checkpoint_dir='.workflow_checkpoints',
    enable_checkpoint=True,     # 启用断点续传
    max_retries=3               # 最大重试次数
)
```

---

## 🐛 常见问题速查

### Q: ModuleNotFoundError

**问题**: `ModuleNotFoundError: No module named 'xxx'`

**解决**:
```bash
# 检查是否在项目根目录
cd /path/to/slm-trainer

# 运行测试
python3 src/data_prep/skills/test_imports.py
```

### Q: 如何查看 Skill 统计信息？

```python
skill = MySkill()
await skill.run(data)

# 查看统计
stats = skill.get_stats()
print(f"成功率: {stats['success_rate']:.1f}%")
print(f"平均耗时: {stats['average_time']:.2f}秒")
```

### Q: 如何处理错误？

```python
result = await skill.run(data)

if result['success']:
    # 处理成功
    data = result['data']
else:
    # 处理失败
    error = result['error']
    print(f"错误: {error}")
```

### Q: 如何实现断点续传？

```python
# OCR 级别
parser = OCRParserSkill(checkpoint_dir='.checkpoints')
result = await parser.run("large.pdf", resume=True)

# Workflow 级别
manager = WorkflowManager(enable_checkpoint=True)
result = await manager.process_file("doc.pdf", resume=True)
```

---

## 📊 性能优化速查

### 1. 使用异步

```python
# ✅ 好
async def execute(self, input_data, **kwargs):
    result = await async_operation()
    return result

# ❌ 不好
def execute(self, input_data, **kwargs):
    result = sync_operation()
    return result
```

### 2. 分批处理大文件

```python
for batch in range(0, total, batch_size):
    batch_result = await process_batch(batch)
    all_results.extend(batch_result)
```

### 3. 使用断点续传

```python
# 保存进度
self._save_checkpoint({'last_page': page_num})

# 恢复进度
if checkpoint_exists:
    start_page = checkpoint['last_page'] + 1
```

---

## 📚 文档速查

| 文档 | 用途 | 何时阅读 |
|------|------|---------|
| `README.md` | 使用文档 | 第一次使用 |
| `INSTALL.md` | 安装指南 | 安装依赖时 |
| `MIGRATION_GUIDE.md` | 迁移指南 | 从 v1.0 升级 |
| `SKILL_DEVELOPMENT_GUIDE.md` | 开发指南 | 开发新 Skill |
| `ARCHITECTURE.md` | 架构文档 | 理解设计 |
| `REFACTORING_REPORT.md` | 重构报告 | 了解变更 |
| `QUICK_REFERENCE.md` | 本文档 | 快速查询 |

---

## 🔗 有用的命令

### 运行测试

```bash
python3 src/data_prep/skills/test_imports.py
```

### 运行示例

```bash
python3 src/data_prep/skills/examples.py
```

### 测试单个 Skill

```bash
python3 -m src.data_prep.skills.parsers.ocr_parser_skill
```

### 检查依赖

```bash
python3 -c "from src.skills import *; print('✅ 所有导入成功')"
```

---

## 💡 最佳实践

### ✅ 推荐

```python
# 使用 Facade Pattern
from src.skills import OCRParserSkill

# 使用增强版基类
from src.skills import BaseSkillEnhanced

# 添加输入验证
def validate_input(self, input_data, **kwargs):
    return True, None

# 添加错误恢复
def handle_error(self, error, input_data, **kwargs):
    return default_value
```

### ❌ 避免

```python
# 不要直接导入内部路径
from src.data_prep.skills.parsers.ocr_parser_skill import OCRParserSkill

# 不要跳过输入验证
async def execute(self, input_data, **kwargs):
    # 直接处理，没有验证
    pass

# 不要忽略错误
try:
    result = process()
except:
    pass  # 不要这样做
```

---

## 🎯 下一步

1. **新用户**: 运行 `examples.py` 查看示例
2. **开发者**: 阅读 `SKILL_DEVELOPMENT_GUIDE.md`
3. **架构师**: 阅读 `ARCHITECTURE.md`
4. **遇到问题**: 查看 `MIGRATION_GUIDE.md` 的常见问题

---

## 📞 获取帮助

1. 运行测试: `python3 src/data_prep/skills/test_imports.py`
2. 查看文档: 阅读对应的 `.md` 文件
3. 查看示例: 运行 `examples.py`
4. 查看源码: 每个 Skill 都有详细注释

---

**版本**: v2.0
**更新日期**: 2026-02-23
**状态**: ✅ 生产就绪
