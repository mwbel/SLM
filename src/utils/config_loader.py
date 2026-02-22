"""配置加载器"""

import yaml
from pathlib import Path
from typing import Dict, Any


class ConfigLoader:
    """加载和管理配置文件"""

    def __init__(self, config_path: str = "config.yaml"):
        """
        初始化配置加载器

        Args:
            config_path: 配置文件路径
        """
        self.config_path = Path(config_path)
        self.config = {}
        if self.config_path.exists():
            self.load()

    def load(self) -> Dict[str, Any]:
        """
        加载配置文件

        Returns:
            配置字典
        """
        with open(self.config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        return self.config

    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置项

        Args:
            key: 配置键（支持点号分隔的嵌套键，如 'model.base_model'）
            default: 默认值

        Returns:
            配置值
        """
        keys = key.split('.')
        value = self.config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
            if value is None:
                return default
        return value

    def set(self, key: str, value: Any):
        """
        设置配置项

        Args:
            key: 配置键（支持点号分隔的嵌套键）
            value: 配置值
        """
        keys = key.split('.')
        config = self.config
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        config[keys[-1]] = value

    def save(self, output_path: str = None):
        """
        保存配置到文件

        Args:
            output_path: 输出路径，默认为原配置文件路径
        """
        path = Path(output_path) if output_path else self.config_path
        with open(path, 'w', encoding='utf-8') as f:
            yaml.dump(self.config, f, allow_unicode=True, default_flow_style=False)

    def update(self, updates: Dict[str, Any]):
        """
        批量更新配置

        Args:
            updates: 更新的配置字典
        """
        self._deep_update(self.config, updates)

    def _deep_update(self, base: Dict, updates: Dict):
        """递归更新嵌套字典"""
        for key, value in updates.items():
            if isinstance(value, dict) and key in base and isinstance(base[key], dict):
                self._deep_update(base[key], value)
            else:
                base[key] = value
