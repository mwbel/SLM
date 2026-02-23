"""
BaseSkill - 所有 Skill 的抽象基类

提供统一的接口和通用功能：
- 日志记录
- 错误捕获
- 性能耗时统计
"""

import time
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from datetime import datetime


class BaseSkill(ABC):
    """
    Skill 抽象基类

    所有具体的 Skill 必须继承此类并实现 execute() 方法
    """

    def __init__(self, name: Optional[str] = None, log_level: int = logging.INFO):
        """
        初始化 BaseSkill

        Args:
            name: Skill 名称（默认使用类名）
            log_level: 日志级别（默认 INFO）
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

    async def run(self, input_data: Any, **kwargs) -> Dict[str, Any]:
        """
        运行 Skill（带日志、错误处理和性能统计）

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

        try:
            # 执行核心逻辑
            result = await self.execute(input_data, **kwargs)

            # 计算耗时
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
            # 错误处理
            execution_time = time.time() - start_time
            self.execution_stats['error_count'] += 1
            self.execution_stats['last_error'] = str(e)
            self.execution_stats['last_execution_time'] = datetime.now()

            self.logger.error(
                f"❌ {self.name} 执行失败: {str(e)} "
                f"(耗时: {execution_time:.2f}秒)"
            )

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
