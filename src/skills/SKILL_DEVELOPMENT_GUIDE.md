# Skill 开发指南

## 📖 概述

本指南将帮助你快速开发新的 Skill，并遵循项目的最佳实践。

## 🏗️ Skill 分类

在开发新 Skill 之前，首先确定它属于哪个类别：

| 类别 | 目录 | 用途 | 示例 |
|------|------|------|------|
| **Classifiers** | `classifiers/` | 文件识别、分类、路由 | FileRouterSkill, FileTypeDetector |
| **Parsers** | `parsers/` | 文本提取、OCR、解析 | NativeParserSkill, OCRParserSkill |
| **Transformers** | `transformers/` | 数据清洗、切分、转换 | SmartChunkerSkill, TextCleaner |
| **Workflow** | `workflow/` | 流程控制、编排 | WorkflowManager, PipelineBuilder |

## 🚀 快速开始

### 步骤 1: 复制模板

```bash
# 假设你要创建一个新的 Transformer Skill
cd src/data_prep/skills/transformers/

# 复制模板
cp ../base_skill_enhanced.py my_new_skill.py
```

### 步骤 2: 修改模板

打开 `my_new_skill.py`，找到 `SkillTemplate` 类并重命名：

```python
"""
MyNewSkill - 简短描述

详细说明这个 Skill 的功能
"""

import asyncio
from typing import Dict, Any, Optional
from ..base_skill_enhanced import BaseSkill


class MyNewSkill(BaseSkill):
    """
    你的 Skill 描述
    """

    def __init__(self, custom_param: str = "default"):
        """
        初始化 Skill

        Args:
            custom_param: 自定义参数说明
        """
        super().__init__(name="MyNewSkill")
        self.custom_param = custom_param

    def validate_input(self, input_data: Any, **kwargs) -> tuple[bool, Optional[str]]:
        """
        验证输入数据

        Args:
            input_data: 输入数据
            **kwargs: 额外参数

        Returns:
            (is_valid, error_message)
        """
        # 调用父类的基础验证
        is_valid, error_msg = super().validate_input(input_data, **kwargs)
        if not is_valid:
            return is_valid, error_msg

        # 添加你的验证逻辑
        if not isinstance(input_data, dict):
            return False, "输入必须是字典类型"

        return True, None

    async def execute(self, input_data: Any, **kwargs) -> Any:
        """
        执行核心逻辑

        Args:
            input_data: 输入数据
            **kwargs: 额外参数

        Returns:
            处理结果
        """
        # 实现你的核心逻辑
        self.logger.info(f"开始处理: {input_data}")

        # 你的处理代码
        result = {
            'processed': True,
            'data': input_data
        }

        return result

    def handle_error(self, error: Exception, input_data: Any, **kwargs) -> Optional[Any]:
        """
        处理错误（可选）

        Args:
            error: 捕获的异常
            input_data: 输入数据
            **kwargs: 额外参数

        Returns:
            恢复结果（如果可以恢复）
        """
        super().handle_error(error, input_data, **kwargs)

        # 添加自定义错误恢复逻辑
        if isinstance(error, ValueError):
            self.logger.warning("捕获到 ValueError，返回默认结果")
            return {'processed': False, 'error': 'recovered'}

        return None
```

### 步骤 3: 注册到模块

编辑对应目录的 `__init__.py`：

```python
# transformers/__init__.py
from .smart_chunker_skill import SmartChunkerSkill
from .my_new_skill import MyNewSkill  # 添加这行

__all__ = [
    'SmartChunkerSkill',
    'MyNewSkill',  # 添加这行
]
```

### 步骤 4: 导出到主入口

编辑 `skills/__init__.py`：

```python
# Transformers (数据转换与切分)
from .transformers.smart_chunker_skill import SmartChunkerSkill
from .transformers.my_new_skill import MyNewSkill  # 添加这行

__all__ = [
    # ... 其他导出
    'SmartChunkerSkill',
    'MyNewSkill',  # 添加这行
]
```

### 步骤 5: 编写测试

在文件末尾添加测试代码：

```python
# 使用示例
if __name__ == "__main__":
    import asyncio

    async def test_my_skill():
        """测试 MyNewSkill"""
        skill = MyNewSkill(custom_param="test")

        # 测试正常执行
        result = await skill.run({'data': 'test'})
        print(f"结果: {result}")

        # 查看统计
        print(f"统计: {skill.get_stats()}")

    asyncio.run(test_my_skill())
```

运行测试：
```bash
python -m src.data_prep.skills.transformers.my_new_skill
```

## 📋 完整示例：创建一个文本清洗 Skill

```python
"""
TextCleanerSkill - 文本清洗器

负责清洗和规范化文本：
1. 移除多余空白
2. 统一换行符
3. 移除特殊字符
4. 规范化标点符号
"""

import asyncio
import re
from typing import Dict, Any, Optional
from ..base_skill_enhanced import BaseSkill


class TextCleanerSkill(BaseSkill):
    """
    文本清洗 Skill

    清洗和规范化文本内容
    """

    def __init__(self,
                 remove_extra_spaces: bool = True,
                 normalize_newlines: bool = True,
                 remove_special_chars: bool = False):
        """
        初始化 TextCleanerSkill

        Args:
            remove_extra_spaces: 是否移除多余空白
            normalize_newlines: 是否统一换行符
            remove_special_chars: 是否移除特殊字符
        """
        super().__init__(name="TextCleaner")
        self.remove_extra_spaces = remove_extra_spaces
        self.normalize_newlines = normalize_newlines
        self.remove_special_chars = remove_special_chars

    def validate_input(self, input_data: Any, **kwargs) -> tuple[bool, Optional[str]]:
        """验证输入"""
        is_valid, error_msg = super().validate_input(input_data, **kwargs)
        if not is_valid:
            return is_valid, error_msg

        # 检查输入类型
        if not isinstance(input_data, (str, dict)):
            return False, "输入必须是字符串或包含 'content' 字段的字典"

        # 如果是字典，检查必需字段
        if isinstance(input_data, dict) and 'content' not in input_data:
            return False, "输入字典必须包含 'content' 字段"

        return True, None

    async def execute(self, input_data: Any, **kwargs) -> Dict[str, Any]:
        """执行文本清洗"""
        # 提取文本
        if isinstance(input_data, str):
            text = input_data
            metadata = {}
        else:
            text = input_data['content']
            metadata = input_data.get('metadata', {})

        original_length = len(text)
        self.logger.info(f"开始清洗文本，原始长度: {original_length}")

        # 清洗步骤
        cleaned_text = text

        # 1. 统一换行符
        if self.normalize_newlines:
            cleaned_text = cleaned_text.replace('\r\n', '\n').replace('\r', '\n')
            self.logger.debug("已统一换行符")

        # 2. 移除多余空白
        if self.remove_extra_spaces:
            # 移除行首行尾空白
            cleaned_text = '\n'.join(line.strip() for line in cleaned_text.split('\n'))
            # 压缩多个空格为一个
            cleaned_text = re.sub(r' +', ' ', cleaned_text)
            # 压缩多个换行为最多两个
            cleaned_text = re.sub(r'\n{3,}', '\n\n', cleaned_text)
            self.logger.debug("已移除多余空白")

        # 3. 移除特殊字符（可选）
        if self.remove_special_chars:
            # 保留中英文、数字、常用标点
            cleaned_text = re.sub(r'[^\w\s\u4e00-\u9fff。，、；：？！""''（）《》【】…—\-\.,;:?!()\[\]\'\"]+', '', cleaned_text)
            self.logger.debug("已移除特殊字符")

        cleaned_length = len(cleaned_text)
        reduction = original_length - cleaned_length

        self.logger.info(
            f"清洗完成，清洗后长度: {cleaned_length}, "
            f"减少: {reduction} 字符 ({reduction/original_length*100:.1f}%)"
        )

        return {
            'content': cleaned_text,
            'metadata': {
                **metadata,
                'original_length': original_length,
                'cleaned_length': cleaned_length,
                'reduction': reduction,
                'reduction_rate': reduction / original_length if original_length > 0 else 0
            }
        }

    def handle_error(self, error: Exception, input_data: Any, **kwargs) -> Optional[Any]:
        """错误处理"""
        super().handle_error(error, input_data, **kwargs)

        # 对于编码错误，尝试使用替换策略
        if isinstance(error, UnicodeDecodeError):
            self.logger.warning("检测到编码错误，尝试使用替换策略")
            try:
                if isinstance(input_data, str):
                    # 已经是字符串，无法恢复
                    return None
                else:
                    # 尝试重新解码
                    return {'content': input_data.get('content', ''), 'metadata': {}}
            except:
                return None

        return None


# 使用示例
if __name__ == "__main__":
    import asyncio

    async def test_text_cleaner():
        """测试文本清洗器"""
        cleaner = TextCleanerSkill(
            remove_extra_spaces=True,
            normalize_newlines=True,
            remove_special_chars=False
        )

        # 测试文本
        test_text = """
        这是一段    有很多     空格的文本。


        还有很多换行。



        以及一些特殊字符：@#$%^&*
        """

        print("原始文本:")
        print(repr(test_text))

        # 执行清洗
        result = await cleaner.run(test_text)

        if result['success']:
            print("\n清洗后文本:")
            print(repr(result['data']['content']))
            print(f"\n元数据: {result['data']['metadata']}")
        else:
            print(f"\n清洗失败: {result['error']}")

        # 查看统计
        print(f"\n统计信息: {cleaner.get_stats()}")

    asyncio.run(test_text_cleaner())
```

## 🎯 最佳实践

### 1. 命名规范

- **类名**: 使用 `PascalCase`，以 `Skill` 结尾
  - ✅ `TextCleanerSkill`
  - ❌ `text_cleaner` 或 `TextCleaner`

- **文件名**: 使用 `snake_case`，以 `_skill.py` 结尾
  - ✅ `text_cleaner_skill.py`
  - ❌ `TextCleanerSkill.py` 或 `text_cleaner.py`

### 2. 文档字符串

每个 Skill 必须包含：
- 模块级 docstring（文件顶部）
- 类级 docstring
- 所有公共方法的 docstring

```python
"""
SkillName - 简短描述

详细说明：
1. 功能点 1
2. 功能点 2
3. 功能点 3
"""

class MySkill(BaseSkill):
    """
    一句话描述

    详细说明这个 Skill 的用途和特点
    """

    def __init__(self, param: str):
        """
        初始化说明

        Args:
            param: 参数说明
        """
        pass
```

### 3. 输入验证

始终实现 `validate_input()` 方法：

```python
def validate_input(self, input_data: Any, **kwargs) -> tuple[bool, Optional[str]]:
    """验证输入"""
    # 1. 调用父类验证
    is_valid, error_msg = super().validate_input(input_data, **kwargs)
    if not is_valid:
        return is_valid, error_msg

    # 2. 类型检查
    if not isinstance(input_data, expected_type):
        return False, f"输入类型错误，期望 {expected_type}"

    # 3. 必需字段检查
    if 'required_field' not in input_data:
        return False, "缺少必需字段: required_field"

    # 4. 值范围检查
    if input_data['value'] < 0:
        return False, "值必须为正数"

    return True, None
```

### 4. 错误处理

实现 `handle_error()` 进行错误恢复：

```python
def handle_error(self, error: Exception, input_data: Any, **kwargs) -> Optional[Any]:
    """错误处理"""
    super().handle_error(error, input_data, **kwargs)

    # 针对特定错误类型进行恢复
    if isinstance(error, SpecificError):
        self.logger.warning("检测到特定错误，尝试恢复")
        return default_result

    # 无法恢复
    return None
```

### 5. 日志记录

合理使用日志级别：

```python
async def execute(self, input_data: Any, **kwargs) -> Any:
    # DEBUG: 详细的调试信息
    self.logger.debug(f"处理参数: {kwargs}")

    # INFO: 重要的执行步骤
    self.logger.info(f"开始处理，输入大小: {len(input_data)}")

    # WARNING: 可恢复的问题
    self.logger.warning("检测到潜在问题，使用默认值")

    # ERROR: 严重错误（通常在 handle_error 中）
    self.logger.error(f"处理失败: {error}")
```

### 6. 性能考虑

- 对于耗时操作，添加进度日志
- 对于大数据，考虑分批处理
- 使用异步操作提升性能

```python
async def execute(self, input_data: Any, **kwargs) -> Any:
    items = input_data['items']
    total = len(items)

    results = []
    for i, item in enumerate(items):
        # 处理单个项目
        result = await self._process_item(item)
        results.append(result)

        # 每处理 10% 输出一次进度
        if (i + 1) % (total // 10) == 0:
            progress = (i + 1) / total * 100
            self.logger.info(f"进度: {progress:.0f}% ({i+1}/{total})")

    return results
```

### 7. 测试

每个 Skill 都应该包含测试代码：

```python
if __name__ == "__main__":
    import asyncio

    async def test_skill():
        """测试 Skill"""
        skill = MySkill()

        # 测试用例 1: 正常情况
        result = await skill.run(valid_input)
        assert result['success']

        # 测试用例 2: 边界情况
        result = await skill.run(edge_case_input)
        assert result['success']

        # 测试用例 3: 错误情况
        result = await skill.run(invalid_input)
        assert not result['success']

        # 查看统计
        stats = skill.get_stats()
        print(f"成功率: {stats['success_rate']:.1f}%")

    asyncio.run(test_skill())
```

## 📚 进阶主题

### 1. Skill 之间的组合

```python
class CompositeSkill(BaseSkill):
    """组合多个 Skill"""

    def __init__(self):
        super().__init__(name="CompositeSkill")
        self.skill1 = Skill1()
        self.skill2 = Skill2()

    async def execute(self, input_data: Any, **kwargs) -> Any:
        # 串联执行
        result1 = await self.skill1.run(input_data)
        if not result1['success']:
            raise Exception(f"Skill1 失败: {result1['error']}")

        result2 = await self.skill2.run(result1['data'])
        if not result2['success']:
            raise Exception(f"Skill2 失败: {result2['error']}")

        return result2['data']
```

### 2. 使用 SkillRegistry

```python
from src.skills import SkillRegistry

# 获取已注册的 Skill
skill = SkillRegistry.get_skill("MySkill")

# 列出所有 Skill
all_skills = SkillRegistry.list_skills()
print(f"已注册的 Skills: {all_skills}")
```

### 3. 自定义配置

```python
class ConfigurableSkill(BaseSkill):
    """支持配置文件的 Skill"""

    def __init__(self, config_path: Optional[str] = None):
        super().__init__(name="ConfigurableSkill")

        if config_path:
            self.load_config(config_path)
        else:
            self.use_default_config()

    def load_config(self, config_path: str):
        """从文件加载配置"""
        import json
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        self.logger.info(f"已加载配置: {config_path}")

    def use_default_config(self):
        """使用默认配置"""
        self.config = {
            'param1': 'default1',
            'param2': 'default2'
        }
```

## ✅ 检查清单

开发完成后，请确认：

- [ ] 类名以 `Skill` 结尾
- [ ] 文件名以 `_skill.py` 结尾
- [ ] 继承自 `BaseSkill` 或 `BaseSkillEnhanced`
- [ ] 实现了 `execute()` 方法
- [ ] 实现了 `validate_input()` 方法
- [ ] 添加了完整的 docstring
- [ ] 添加了日志记录
- [ ] 编写了测试代码
- [ ] 注册到子模块的 `__init__.py`
- [ ] 导出到主 `__init__.py`
- [ ] 运行测试通过

## 🆘 常见问题

### Q: 应该继承 BaseSkill 还是 BaseSkillEnhanced？

A: 新 Skill 推荐使用 `BaseSkillEnhanced`，它提供了更多功能（输入验证、错误恢复、自动注册）。

### Q: 如何在 Skill 中调用其他 Skill？

A: 在 `__init__` 中创建其他 Skill 的实例，然后在 `execute` 中调用它们的 `run()` 方法。

### Q: 如何处理大文件？

A: 使用分批处理，参考 `OCRParserSkill` 的实现。

### Q: 如何实现断点续传？

A: 参考 `OCRParserSkill` 的 checkpoint 机制。

## 📖 参考资料

- `base_skill_enhanced.py` - 增强版基类实现
- `parsers/ocr_parser_skill.py` - 复杂 Skill 示例
- `transformers/smart_chunker_skill.py` - 数据转换示例
- `workflow/workflow_manager.py` - 流程控制示例
