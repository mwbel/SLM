"""
APIManagerSkill - API 配置与轮询管理器

负责：
1. 管理多个 API 密钥（Gemini、DeepSeek 等）
2. 实现 API 轮询机制（避免单个 API 限流）
3. 自动故障转移（某个 API 失败时切换到下一个）
4. 统计 API 使用情况
5. 支持配置文件和环境变量
"""

import os
import json
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
from .base_skill import BaseSkill


class APIManagerSkill(BaseSkill):
    """
    API 管理 Skill

    管理多个 API 密钥，实现轮询和故障转移
    """

    def __init__(self,
                 config_file: Optional[str] = None,
                 auto_rotate: bool = True,
                 failure_threshold: int = 3,
                 cooldown_minutes: int = 5):
        """
        初始化 APIManagerSkill

        Args:
            config_file: API 配置文件路径（JSON 格式）
            auto_rotate: 是否自动轮询 API
            failure_threshold: 失败阈值（连续失败多少次后暂停使用该 API）
            cooldown_minutes: 冷却时间（分钟，失败后多久可以重新尝试）
        """
        super().__init__(name="APIManager")

        self.auto_rotate = auto_rotate
        self.failure_threshold = failure_threshold
        self.cooldown_minutes = cooldown_minutes

        # API 配置
        self.apis: Dict[str, List[Dict[str, Any]]] = {
            'gemini': [],
            'deepseek': [],
            'openai': []
        }

        # API 状态跟踪
        self.api_stats: Dict[str, Dict[str, Any]] = {}

        # 当前使用的 API 索引
        self.current_index: Dict[str, int] = {
            'gemini': 0,
            'deepseek': 0,
            'openai': 0
        }

        # 加载配置
        if config_file:
            self._load_config(config_file)
        else:
            self._load_from_env()

        self.logger.info(f"✅ API 管理器初始化完成")
        self._log_api_summary()

    def _load_config(self, config_file: str):
        """
        从配置文件加载 API 配置

        配置文件格式（JSON）：
        {
            "gemini": [
                {
                    "api_key": "key1",
                    "model": "gemini-1.5-flash",
                    "name": "Gemini-Account-1",
                    "priority": 1
                }
            ],
            "deepseek": [
                {
                    "api_key": "key1",
                    "model": "deepseek-chat",
                    "name": "DeepSeek-Account-1",
                    "priority": 1
                }
            ]
        }
        """
        config_path = Path(config_file)
        if not config_path.exists():
            self.logger.warning(f"配置文件不存在: {config_file}，将从环境变量加载")
            self._load_from_env()
            return

        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)

            for provider, api_list in config.items():
                if provider in self.apis:
                    for api_config in api_list:
                        self._add_api(provider, api_config)

            self.logger.info(f"✅ 从配置文件加载 API: {config_file}")

        except Exception as e:
            self.logger.error(f"加载配置文件失败: {e}")
            self._load_from_env()

    def _load_from_env(self):
        """从环境变量加载 API 配置"""
        # Gemini
        gemini_keys = self._get_env_keys('GEMINI_API_KEY')
        for i, key in enumerate(gemini_keys, 1):
            self._add_api('gemini', {
                'api_key': key,
                'model': os.getenv('GEMINI_MODEL', 'gemini-1.5-flash'),
                'name': f'Gemini-Env-{i}',
                'priority': 1
            })

        # DeepSeek
        deepseek_keys = self._get_env_keys('DEEPSEEK_API_KEY')
        for i, key in enumerate(deepseek_keys, 1):
            self._add_api('deepseek', {
                'api_key': key,
                'model': os.getenv('DEEPSEEK_MODEL', 'deepseek-chat'),
                'name': f'DeepSeek-Env-{i}',
                'priority': 1
            })

        # OpenAI
        openai_keys = self._get_env_keys('OPENAI_API_KEY')
        for i, key in enumerate(openai_keys, 1):
            self._add_api('openai', {
                'api_key': key,
                'model': os.getenv('OPENAI_MODEL', 'gpt-4'),
                'name': f'OpenAI-Env-{i}',
                'priority': 1
            })

        if not any(self.apis.values()):
            self.logger.warning("⚠️  未找到任何 API 配置")

    def _get_env_keys(self, env_prefix: str) -> List[str]:
        """
        获取环境变量中的 API 密钥

        支持格式：
        - GEMINI_API_KEY=key1
        - GEMINI_API_KEY_1=key1
        - GEMINI_API_KEY_2=key2
        """
        keys = []

        # 单个密钥
        key = os.getenv(env_prefix)
        if key:
            keys.append(key)

        # 多个密钥（带编号）
        i = 1
        while True:
            key = os.getenv(f"{env_prefix}_{i}")
            if key:
                keys.append(key)
                i += 1
            else:
                break

        return keys

    def _add_api(self, provider: str, config: Dict[str, Any]):
        """添加 API 配置"""
        api_id = f"{provider}_{len(self.apis[provider])}"

        self.apis[provider].append(config)

        # 初始化统计信息
        self.api_stats[api_id] = {
            'provider': provider,
            'name': config.get('name', api_id),
            'total_calls': 0,
            'success_calls': 0,
            'failed_calls': 0,
            'consecutive_failures': 0,
            'last_success': None,
            'last_failure': None,
            'cooldown_until': None,
            'is_active': True
        }

    def _log_api_summary(self):
        """记录 API 配置摘要"""
        total = sum(len(apis) for apis in self.apis.values())
        self.logger.info(f"📊 API 配置摘要:")
        self.logger.info(f"   总计: {total} 个 API")
        for provider, apis in self.apis.items():
            if apis:
                self.logger.info(f"   {provider}: {len(apis)} 个")

    async def execute(self, input_data: Any, **kwargs) -> Dict[str, Any]:
        """
        执行 API 管理操作

        Args:
            input_data: 操作类型
                - 'get_api': 获取可用的 API
                - 'report_success': 报告 API 调用成功
                - 'report_failure': 报告 API 调用失败
                - 'get_stats': 获取统计信息
            **kwargs: 额外参数
                - provider: str, API 提供商
                - api_id: str, API ID

        Returns:
            操作结果
        """
        operation = input_data

        if operation == 'get_api':
            provider = kwargs.get('provider')
            return self.get_available_api(provider)

        elif operation == 'report_success':
            api_id = kwargs.get('api_id')
            self.report_success(api_id)
            return {'status': 'success'}

        elif operation == 'report_failure':
            api_id = kwargs.get('api_id')
            error = kwargs.get('error', 'Unknown error')
            self.report_failure(api_id, error)
            return {'status': 'failure_reported'}

        elif operation == 'get_stats':
            return self.get_statistics()

        else:
            raise ValueError(f"不支持的操作: {operation}")

    def get_available_api(self, provider: str) -> Optional[Dict[str, Any]]:
        """
        获取可用的 API

        Args:
            provider: API 提供商 ('gemini', 'deepseek', 'openai')

        Returns:
            API 配置字典，如果没有可用的返回 None
        """
        if provider not in self.apis or not self.apis[provider]:
            self.logger.warning(f"没有配置 {provider} API")
            return None

        apis = self.apis[provider]
        start_index = self.current_index[provider]

        # 尝试所有 API（轮询）
        for i in range(len(apis)):
            index = (start_index + i) % len(apis)
            api_id = f"{provider}_{index}"

            # 检查 API 是否可用
            if self._is_api_available(api_id):
                # 更新当前索引（如果启用自动轮询）
                if self.auto_rotate:
                    self.current_index[provider] = (index + 1) % len(apis)

                api_config = apis[index].copy()
                api_config['api_id'] = api_id

                self.logger.info(f"🔑 使用 API: {self.api_stats[api_id]['name']}")
                return api_config

        self.logger.error(f"❌ 没有可用的 {provider} API")
        return None

    def _is_api_available(self, api_id: str) -> bool:
        """检查 API 是否可用"""
        stats = self.api_stats[api_id]

        # 检查是否被禁用
        if not stats['is_active']:
            return False

        # 检查是否在冷却期
        if stats['cooldown_until']:
            if datetime.now() < stats['cooldown_until']:
                return False
            else:
                # 冷却期结束，重置状态
                stats['cooldown_until'] = None
                stats['consecutive_failures'] = 0
                self.logger.info(f"🔄 API 冷却期结束: {stats['name']}")

        return True

    def report_success(self, api_id: str):
        """报告 API 调用成功"""
        if api_id not in self.api_stats:
            return

        stats = self.api_stats[api_id]
        stats['total_calls'] += 1
        stats['success_calls'] += 1
        stats['consecutive_failures'] = 0
        stats['last_success'] = datetime.now()

        self.logger.debug(f"✅ API 调用成功: {stats['name']}")

    def report_failure(self, api_id: str, error: str):
        """报告 API 调用失败"""
        if api_id not in self.api_stats:
            return

        stats = self.api_stats[api_id]
        stats['total_calls'] += 1
        stats['failed_calls'] += 1
        stats['consecutive_failures'] += 1
        stats['last_failure'] = datetime.now()

        self.logger.warning(
            f"⚠️  API 调用失败: {stats['name']} "
            f"(连续失败 {stats['consecutive_failures']} 次)"
        )

        # 检查是否需要进入冷却期
        if stats['consecutive_failures'] >= self.failure_threshold:
            stats['cooldown_until'] = datetime.now() + timedelta(minutes=self.cooldown_minutes)
            self.logger.warning(
                f"🚫 API 进入冷却期: {stats['name']} "
                f"(冷却 {self.cooldown_minutes} 分钟)"
            )

    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        total_calls = sum(s['total_calls'] for s in self.api_stats.values())
        total_success = sum(s['success_calls'] for s in self.api_stats.values())
        total_failed = sum(s['failed_calls'] for s in self.api_stats.values())

        api_details = []
        for api_id, stats in self.api_stats.items():
            success_rate = (
                stats['success_calls'] / stats['total_calls'] * 100
                if stats['total_calls'] > 0 else 0
            )

            api_details.append({
                'api_id': api_id,
                'name': stats['name'],
                'provider': stats['provider'],
                'total_calls': stats['total_calls'],
                'success_calls': stats['success_calls'],
                'failed_calls': stats['failed_calls'],
                'success_rate': round(success_rate, 2),
                'consecutive_failures': stats['consecutive_failures'],
                'is_active': stats['is_active'],
                'in_cooldown': stats['cooldown_until'] is not None
            })

        return {
            'total_apis': len(self.api_stats),
            'total_calls': total_calls,
            'total_success': total_success,
            'total_failed': total_failed,
            'overall_success_rate': round(total_success / total_calls * 100, 2) if total_calls > 0 else 0,
            'api_details': api_details
        }

    def save_config(self, output_file: str):
        """
        保存当前配置到文件

        Args:
            output_file: 输出文件路径
        """
        config = {}
        for provider, apis in self.apis.items():
            if apis:
                config[provider] = [
                    {
                        'api_key': api['api_key'],
                        'model': api['model'],
                        'name': api['name'],
                        'priority': api.get('priority', 1)
                    }
                    for api in apis
                ]

        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)

        self.logger.info(f"✅ 配置已保存到: {output_file}")


# 使用示例
if __name__ == "__main__":
    import asyncio

    async def test_api_manager():
        """测试 API 管理器"""
        print("\n" + "="*60)
        print("测试 APIManagerSkill")
        print("="*60)

        # 创建 API 管理器
        manager = APIManagerSkill(
            auto_rotate=True,
            failure_threshold=3,
            cooldown_minutes=5
        )

        # 获取可用的 Gemini API
        print("\n1. 获取 Gemini API:")
        api = manager.get_available_api('gemini')
        if api:
            print(f"   ✅ API ID: {api['api_id']}")
            print(f"   模型: {api['model']}")

            # 模拟成功调用
            manager.report_success(api['api_id'])

        # 获取统计信息
        print("\n2. 统计信息:")
        result = await manager.run('get_stats')
        if result['success']:
            stats = result['data']
            print(f"   总 API 数: {stats['total_apis']}")
            print(f"   总调用数: {stats['total_calls']}")
            print(f"   成功率: {stats['overall_success_rate']}%")

            print("\n   API 详情:")
            for api_detail in stats['api_details']:
                print(f"   - {api_detail['name']}: {api_detail['total_calls']} 次调用")

        # 保存配置
        print("\n3. 保存配置:")
        manager.save_config('config/api_config.json')

    asyncio.run(test_api_manager())
