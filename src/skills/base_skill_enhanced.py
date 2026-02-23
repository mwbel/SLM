"""
BaseSkill - 增强版 Skill 抽象基类

提供统一的接口和通用功能：
- 日志记录
- 错误捕获与恢复
- 性能耗时统计
- 输入验证
- 自动注册
"""

import time
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, List
from datetime import datetime


class SkillRegistry:
    """Skill 注册中心"""
    _registry: Dict[str, 'BaseSkill'] = {}

    @classmethod
    def register(cls, skill: 'BaseSkill'):
        """注册 Skill"""
        cls._registry[skill.name] = skill

    @classmethod
    def get_skill(cls, name: str) -> Optional['BaseSkill']:
        """获取已注册的 Skill"""
        return cls._registry.get(name)

    @classmethod
    def list_skills(cls) -> List[str]:
        """列出所有已注册的 Skill"""
        return list(cls._registry.keys())


class BaseSkill(ABC):
    """
    Skill 抽象基类（增强版）

    所有具体的 Skill 必须继承此类并实现：
    - execute(): 核心执行逻辑
    - validate_input(): 输入验证逻辑（可选）
    - handle_error(): 错误处理逻辑（可选）
    """

    def __init__(self,
                 name: Optional[str] = None,
                 log_level: int = logging.INFO,
                 auto_register: bool = True):
        """
        初始化 BaseSkill

        Args:
            name: Skill 名称（默认使用类名）
            log_level: 日志级别（默认 INFO）
            auto_register: 是否自动注册到 SkillRegistry（默认 True）
        """
        self.name = name or self.__class__.__name__
        self.logger = self._setup_logger(log_level)
        self.execution_stats = {
            'total_executions': 0,
            'total_time': 0.0,
            'success_count': 0,
            'error_count': 0,
            'last_execution_time': None,
            'last_error': None
        }

        # 自动注册到注册中心
        if auto_register:
            SkillRegistry.register(self)
            self.logger.debug(f"✅ {self.name} 已注册到 SkillRegistry")

    def _setup_logger(self, log_level: int) -> logging.Logger:
        """
        设置日志记录器

        Args:
            log_level: 日志级别

        Returns:
            配置好的 Logger 对象
        """
        logger = logging.getLogger(f"Skill.{self.name}")
        logger.setLevel(log_level)

        # 避免重复添加 handler
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger

    @abstractmethod
    async def execute(self, input_data: Any, **kwargs) -> Any:
        """
        执行 Skill 的核心逻辑（抽象方法）

        子类必须实现此方法

        Args:
            input_data: 输入数据
            **kwargs: 额外的参数

        Returns:
            处理后的输出数据

        Raises:
            NotImplementedError: 子类未实现此方法
        """
        raise NotImplementedError(f"{self.name} 必须实现 execute() 方法")

    def validate_input(self, input_data: Any, **kwargs) -> tuple[bool, Optional[str]]:
        """
        验证输入数据（可选重写）

        子类可以重写此方法来实现自定义的输入验证逻辑

        Args:
            input_data: 输入数据
            **kwargs: 额外的参数

        Returns:
            (is_valid, error_message): 验证结果和错误信息
        """
        # 默认实现：检查输入是否为 None
        if input_data is None:
            return False, "输入数据不能为 None"
        return True, None

    def handle_error(self, error: Exception, input_data: Any, **kwargs) -> Optional[Any]:
        """
        处理错误（可选重写）

        子类可以重写此方法来实现自定义的错误恢复逻辑

        Args:
            error: 捕获的异常
            input_data: 输入数据
            **kwargs: 额外的参数

        Returns:
            恢复后的结果（如果可以恢复），否则返回 None
        """
        # 默认实现：记录错误，不进行恢复
        self.logger.error(f"错误处理: {type(error).__name__}: {str(error)}")
        return None

    async def run(self, input_data: Any, **kwargs) -> Dict[str, Any]:
        """
        运行 Skill（带日志、验证、错误处理和性能统计）

        这是对外的统一接口，会自动调用 execute() 方法

        Args:
            input_data: 输入数据
            **kwargs: 额外的参数

        Returns:
            包含执行结果的字典：
            {
                'success': bool,           # 是否成功
                'data': Any,               # 输出数据
                'error': str,              # 错误信息（如果失败）
                'execution_time': float,   # 执行耗时（秒）
                'skill_name': str          # Skill 名称
            }
        """
        start_time = time.time()
        self.execution_stats['total_executions'] += 1

        self.logger.info(f"🚀 开始执行 {self.name}")

        # Step 1: 输入验证
        is_valid, error_message = self.validate_input(input_data, **kwargs)
        if not is_valid:
            execution_time = time.time() - start_time
            self.execution_stats['error_count'] += 1
            self.execution_stats['last_error'] = error_message
            self.execution_stats['last_execution_time'] = datetime.now()

            self.logger.error(f"❌ 输入验证失败: {error_message}")

            return {
                'success': False,
                'data': None,
                'error': f"输入验证失败: {error_message}",
                'execution_time': execution_time,
                'skill_name': self.name
            }

        try:
            # Step 2: 执行核心逻辑
            result = await self.execute(input_data, **kwargs)

            # Step 3: 计算耗时
            execution_time = time.time() - start_time
            self.execution_stats['total_time'] += execution_time
            self.execution_stats['success_count'] += 1
            self.execution_stats['last_execution_time'] = datetime.now()

            self.logger.info(
                f"✅ {self.name} 执行成功 "
                f"(耗时: {execution_time:.2f}秒)"
            )

            return {
                'success': True,
                'data': result,
                'error': None,
                'execution_time': execution_time,
                'skill_name': self.name
            }

        except Exception as e:
            # Step 4: 错误处理
            execution_time = time.time() - start_time
            self.execution_stats['error_count'] += 1
            self.execution_stats['last_error'] = str(e)
            self.execution_stats['last_execution_time'] = datetime.now()

            self.logger.error(
                f"❌ {self.name} 执行失败: {str(e)} "
                f"(耗时: {execution_time:.2f}秒)"
            )

            # 尝试错误恢复
            recovery_result = self.handle_error(e, input_data, **kwargs)

            if recovery_result is not None:
                self.logger.info(f"🔄 错误已恢复，返回恢复结果")
                return {
                    'success': True,
                    'data': recovery_result,
                    'error': None,
                    'execution_time': execution_time,
                    'skill_name': self.name,
                    'recovered': True
                }

            return {
                'success': False,
                'data': None,
                'error': str(e),
                'execution_time': execution_time,
                'skill_name': self.name
            }

    def get_stats(self) -> Dict[str, Any]:
        """
        获取执行统计信息

        Returns:
            统计信息字典
        """
        avg_time = (
            self.execution_stats['total_time'] / self.execution_stats['total_executions']
            if self.execution_stats['total_executions'] > 0
            else 0.0
        )

        return {
            'skill_name': self.name,
            'total_executions': self.execution_stats['total_executions'],
            'success_count': self.execution_stats['success_count'],
            'error_count': self.execution_stats['error_count'],
            'success_rate': (
                self.execution_stats['success_count'] / self.execution_stats['total_executions'] * 100
                if self.execution_stats['total_executions'] > 0
                else 0.0
            ),
            'total_time': round(self.execution_stats['total_time'], 2),
            'average_time': round(avg_time, 2),
            'last_execution_time': self.execution_stats['last_execution_time'],
            'last_error': self.execution_stats['last_error']
        }

    def reset_stats(self):
        """重置统计信息"""
        self.execution_stats = {
            'total_executions': 0,
            'total_time': 0.0,
            'success_count': 0,
            'error_count': 0,
            'last_execution_time': None,
            'last_error': None
        }
        self.logger.info(f"📊 {self.name} 统计信息已重置")

    def __repr__(self) -> str:
        """字符串表示"""
        return f"<{self.name} Skill>"


# Skill 开发模板
class SkillTemplate(BaseSkill):
    """
    Skill 开发模板

    复制此模板来创建新的 Skill
    """

    def __init__(self, custom_param: str = "default"):
        """
        初始化 Skill

        Args:
            custom_param: 自定义参数
        """
        super().__init__(name="SkillTemplate")
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

        # 添加自定义验证逻辑
        # 例如：检查输入类型
        if not isinstance(input_data, dict):
            return False, "输入必须是字典类型"

        # 例如：检查必需字段
        if 'required_field' not in input_data:
            return False, "输入缺少必需字段: required_field"

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
        self.logger.info(f"处理输入: {input_data}")

        # 示例：简单的数据转换
        result = {
            'processed': True,
            'input': input_data,
            'param': self.custom_param
        }

        return result

    def handle_error(self, error: Exception, input_data: Any, **kwargs) -> Optional[Any]:
        """
        处理错误

        Args:
            error: 捕获的异常
            input_data: 输入数据
            **kwargs: 额外参数

        Returns:
            恢复结果（如果可以恢复）
        """
        # 调用父类的默认错误处理
        super().handle_error(error, input_data, **kwargs)

        # 添加自定义错误恢复逻辑
        # 例如：对于特定类型的错误，返回默认值
        if isinstance(error, ValueError):
            self.logger.warning("捕获到 ValueError，返回默认结果")
            return {'processed': False, 'error': 'recovered'}

        # 无法恢复，返回 None
        return None


# 使用示例
if __name__ == "__main__":
    import asyncio

    async def test_skill_template():
        """测试 Skill 模板"""
        skill = SkillTemplate(custom_param="test")

        # 测试正常执行
        result = await skill.run({'required_field': 'value'})
        print(f"结果: {result}")

        # 测试输入验证失败
        result = await skill.run("invalid_input")
        print(f"验证失败: {result}")

        # 测试错误恢复
        result = await skill.run({'required_field': 'value'})
        print(f"错误恢复: {result}")

        # 查看统计
        print(f"\n统计信息: {skill.get_stats()}")

        # 查看注册的 Skills
        print(f"\n已注册的 Skills: {SkillRegistry.list_skills()}")

    asyncio.run(test_skill_template())
