# Skill 系统重构迁移指南

## 📋 目录结构变更

### 旧结构 (v1.0)
```
src/data_prep/skills/
├── __init__.py
├── base_skill.py
├── file_router_skill.py
├── native_parser_skill.py
├── ocr_parser_skill.py
├── smart_chunker_skill.py
├── workflow_manager.py
├── examples.py
├── README.md
└── INSTALL.md
```

### 新结构 (v2.0)
```
src/data_prep/skills/
├── __init__.py                    # 统一入口 (Facade Pattern)
├── base_skill.py                  # 原始基类
├── base_skill_enhanced.py         # 增强版基类
├── classifiers/                   # 文件识别与路由
│   ├── __init__.py
│   └── file_router_skill.py
├── parsers/                       # 文本提取与 OCR
│   ├── __init__.py
│   ├── native_parser_skill.py
│   └── ocr_parser_skill.py
├── transformers/                  # 数据转换与切分
│   ├── __init__.py
│   └── smart_chunker_skill.py
├── workflow/                      # 流程控制
│   ├── __init__.py
│   └── workflow_manager.py
├── examples.py
├── README.md
└── INSTALL.md
```

## 🔄 Import 路径变更对照表

### 外部调用（推荐方式 - 无需修改）

**旧代码：**
```python
from src.skills import FileRouterSkill
from src.skills import NativeParserSkill
from src.skills import OCRParserSkill
from src.skills import SmartChunkerSkill
from src.skills import WorkflowManager
```

**新代码（完全兼容）：**
```python
# 完全相同！得益于 Facade Pattern
from src.skills import FileRouterSkill
from src.skills import NativeParserSkill
from src.skills import OCRParserSkill
from src.skills import SmartChunkerSkill
from src.skills import WorkflowManager
```

✅ **外部调用者无需修改任何代码！**

### 内部 Skill 之间的引用

**旧代码：**
```python
# 在 workflow_manager.py 中
from .base_skill import BaseSkill
from .file_router_skill import FileRouterSkill
from .native_parser_skill import NativeParserSkill
```

**新代码：**
```python
# 在 workflow/workflow_manager.py 中
from ..base_skill import BaseSkill
from ..classifiers.file_router_skill import FileRouterSkill
from ..parsers.native_parser_skill import NativeParserSkill
```

### 新增的增强版基类

**新功能：**
```python
# 使用增强版基类（推荐新 Skill 使用）
from src.skills import BaseSkillEnhanced, SkillRegistry, SkillTemplate

# 或者直接从模块导入
from src.data_prep.skills.base_skill_enhanced import BaseSkill, SkillRegistry
```

## 🛠️ VS Code 中的迁移步骤

### 步骤 1: 备份（可选但推荐）
```bash
cd src/data_prep/skills
git add .
git commit -m "backup before refactoring"
```

### 步骤 2: 文件已自动迁移
✅ 所有文件已经移动到正确的位置
✅ 所有 import 路径已经更新

### 步骤 3: 验证迁移结果

运行以下命令检查是否有遗漏的 import 错误：

```bash
# 检查所有 Python 文件的 import
cd /Users/Min369/Documents/同步空间/Manju/Projects/垂直小模型/slm-trainer
python -m py_compile src/data_prep/skills/**/*.py
```

### 步骤 4: 测试导入

创建测试文件 `test_imports.py`：

```python
"""测试所有 Skill 是否可以正常导入"""

def test_imports():
    """测试导入"""
    print("测试 Skill 系统导入...")

    # 测试基础类
    from src.skills import BaseSkill, BaseSkillEnhanced
    print("✅ BaseSkill 导入成功")

    # 测试 Classifiers
    from src.skills import FileRouterSkill
    print("✅ FileRouterSkill 导入成功")

    # 测试 Parsers
    from src.skills import NativeParserSkill, OCRParserSkill
    print("✅ Parsers 导入成功")

    # 测试 Transformers
    from src.skills import SmartChunkerSkill
    print("✅ SmartChunkerSkill 导入成功")

    # 测试 Workflow
    from src.skills import WorkflowManager
    print("✅ WorkflowManager 导入成功")

    # 测试注册中心
    from src.skills import SkillRegistry
    print("✅ SkillRegistry 导入成功")

    print("\n🎉 所有导入测试通过！")

if __name__ == "__main__":
    test_imports()
```

运行测试：
```bash
python test_imports.py
```

## 📝 需要手动修改的文件清单

### ✅ 已自动完成的修改

1. ✅ `classifiers/file_router_skill.py` - import 路径已更新
2. ✅ `parsers/native_parser_skill.py` - import 路径已更新
3. ✅ `parsers/ocr_parser_skill.py` - import 路径已更新
4. ✅ `transformers/smart_chunker_skill.py` - import 路径已更新
5. ✅ `workflow/workflow_manager.py` - import 路径已更新
6. ✅ `__init__.py` - 统一入口已实现

### ⚠️ 可能需要手动检查的文件

1. **examples.py** - 如果有引用 Skill 的示例代码
2. **测试文件** - `tests/` 目录下的测试文件
3. **主程序** - 任何使用 Skill 系统的主程序文件

## 🔍 查找需要修改的文件

在 VS Code 中使用全局搜索：

### 搜索 1: 查找旧的 import 语句
```
搜索: from .base_skill import
替换: from ..base_skill import
```

### 搜索 2: 查找直接引用的 Skill
```
搜索: from .file_router_skill
搜索: from .native_parser_skill
搜索: from .ocr_parser_skill
搜索: from .smart_chunker_skill
搜索: from .workflow_manager
```

### 搜索 3: 查找外部引用
```
搜索: from src.data_prep.skills.file_router_skill
搜索: from src.data_prep.skills.native_parser_skill
```

## 🚨 常见问题与解决方案

### 问题 1: ModuleNotFoundError: No module named 'base_skill'

**原因：** import 路径使用了相对导入但层级不对

**解决：**
```python
# 错误
from .base_skill import BaseSkill

# 正确（在子目录中）
from ..base_skill import BaseSkill
```

### 问题 2: ImportError: cannot import name 'FileRouterSkill'

**原因：** 子模块的 `__init__.py` 没有正确导出

**解决：** 检查 `classifiers/__init__.py` 是否包含：
```python
from .file_router_skill import FileRouterSkill
__all__ = ['FileRouterSkill']
```

### 问题 3: 循环导入 (Circular Import)

**原因：** 模块之间相互引用

**解决：**
```python
# 使用延迟导入
def some_function():
    from ..parsers.native_parser_skill import NativeParserSkill
    # 使用 NativeParserSkill
```

## 📦 更新 examples.py

如果 `examples.py` 中有直接引用，需要更新：

**旧代码：**
```python
from src.data_prep.skills.file_router_skill import FileRouterSkill
```

**新代码：**
```python
# 推荐方式（使用 Facade）
from src.skills import FileRouterSkill

# 或者直接引用（不推荐）
from src.data_prep.skills.classifiers.file_router_skill import FileRouterSkill
```

## ✅ 验证清单

完成迁移后，请检查以下项目：

- [ ] 所有 Skill 文件已移动到正确的子目录
- [ ] 所有 `__init__.py` 文件已创建并正确导出
- [ ] 所有内部 import 路径已更新（使用 `..` 相对导入）
- [ ] 主 `__init__.py` 实现了 Facade Pattern
- [ ] 运行 `test_imports.py` 通过
- [ ] 运行现有的单元测试通过
- [ ] examples.py 可以正常运行
- [ ] 外部调用代码无需修改即可工作

## 🎯 迁移后的优势

1. **更清晰的组织结构** - 按功能分类，易于查找
2. **更好的扩展性** - 新增 Skill 只需放入对应目录
3. **统一的入口** - 外部调用者无需关心内部结构
4. **向后兼容** - 旧代码无需修改
5. **更强的基类** - 增强版 BaseSkill 提供更多功能

## 📚 下一步

1. 阅读 `base_skill_enhanced.py` 了解新功能
2. 使用 `SkillTemplate` 创建新的 Skill
3. 查看 `SKILL_DEVELOPMENT_GUIDE.md` 学习最佳实践
4. 运行 `examples.py` 查看使用示例

## 🆘 需要帮助？

如果遇到问题：
1. 检查本文档的"常见问题"部分
2. 运行 `test_imports.py` 定位问题
3. 查看 Git diff 了解具体变更
4. 参考 `examples.py` 中的正确用法
