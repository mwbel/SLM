"""API密钥轮换管理器"""

import time
from typing import List, Optional
from datetime import datetime, timedelta


class APIKeyRotator:
    """API密钥轮换器 - 自动切换多个API密钥"""

    def __init__(self, api_keys: List[str], cooldown_minutes: int = 60):
        """
        初始化API密钥轮换器

        Args:
            api_keys: API密钥列表
            cooldown_minutes: 密钥冷却时间（分钟），默认60分钟
        """
        if not api_keys:
            raise ValueError("API密钥列表不能为空")

        self.api_keys = api_keys
        self.current_index = 0
        self.cooldown_minutes = cooldown_minutes

        # 记录每个密钥的使用情况
        self.key_status = {
            key: {
                'last_used': None,
                'error_count': 0,
                'total_calls': 0,
                'is_available': True
            }
            for key in api_keys
        }

    def get_current_key(self) -> str:
        """
        获取当前可用的API密钥

        Returns:
            当前API密钥
        """
        return self.api_keys[self.current_index]

    def mark_success(self):
        """标记当前密钥调用成功"""
        current_key = self.get_current_key()
        self.key_status[current_key]['last_used'] = datetime.now()
        self.key_status[current_key]['total_calls'] += 1
        self.key_status[current_key]['error_count'] = 0  # 重置错误计数

    def mark_quota_exceeded(self):
        """
        标记当前密钥配额已用完，切换到下一个密钥

        Returns:
            新的API密钥
        """
        current_key = self.get_current_key()

        # 标记当前密钥不可用
        self.key_status[current_key]['is_available'] = False
        self.key_status[current_key]['last_used'] = datetime.now()

        print(f"API密钥 {current_key[:20]}... 配额已用完，切换到下一个密钥")

        # 切换到下一个可用密钥
        return self._rotate_to_next_available()

    def mark_error(self, error_message: str = ""):
        """
        标记当前密钥出错

        Args:
            error_message: 错误信息
        """
        current_key = self.get_current_key()
        self.key_status[current_key]['error_count'] += 1

        # 如果错误次数过多，标记为不可用
        if self.key_status[current_key]['error_count'] >= 3:
            print(f"API密钥 {current_key[:20]}... 错误次数过多，暂时禁用")
            self.key_status[current_key]['is_available'] = False
            self._rotate_to_next_available()

    def _rotate_to_next_available(self) -> str:
        """
        轮换到下一个可用的密钥

        Returns:
            下一个可用的API密钥

        Raises:
            RuntimeError: 所有密钥都不可用
        """
        # 首先检查是否有冷却完成的密钥
        self._check_cooldown()

        # 尝试找到下一个可用密钥
        attempts = 0
        while attempts < len(self.api_keys):
            self.current_index = (self.current_index + 1) % len(self.api_keys)
            current_key = self.get_current_key()

            if self.key_status[current_key]['is_available']:
                print(f"切换到API密钥 #{self.current_index + 1}")
                return current_key

            attempts += 1

        # 所有密钥都不可用
        raise RuntimeError(
            f"所有API密钥都已用完或不可用。请等待 {self.cooldown_minutes} 分钟后重试，"
            "或添加更多API密钥。"
        )

    def _check_cooldown(self):
        """检查并恢复冷却完成的密钥"""
        now = datetime.now()
        cooldown_delta = timedelta(minutes=self.cooldown_minutes)

        for key, status in self.key_status.items():
            if not status['is_available'] and status['last_used']:
                # 检查是否已经冷却完成
                if now - status['last_used'] >= cooldown_delta:
                    status['is_available'] = True
                    status['error_count'] = 0
                    print(f"API密钥 {key[:20]}... 冷却完成，已恢复可用")

    def get_status_report(self) -> str:
        """
        获取所有密钥的状态报告

        Returns:
            状态报告字符串
        """
        report = "\n=== API密钥状态报告 ===\n"

        for i, key in enumerate(self.api_keys):
            status = self.key_status[key]
            key_preview = f"{key[:20]}..."

            report += f"\n密钥 #{i + 1}: {key_preview}\n"
            report += f"  状态: {'✓ 可用' if status['is_available'] else '✗ 不可用'}\n"
            report += f"  总调用次数: {status['total_calls']}\n"
            report += f"  错误次数: {status['error_count']}\n"

            if status['last_used']:
                report += f"  最后使用: {status['last_used'].strftime('%Y-%m-%d %H:%M:%S')}\n"
            else:
                report += f"  最后使用: 未使用\n"

            if not status['is_available'] and status['last_used']:
                cooldown_end = status['last_used'] + timedelta(minutes=self.cooldown_minutes)
                remaining = cooldown_end - datetime.now()
                if remaining.total_seconds() > 0:
                    report += f"  冷却剩余: {int(remaining.total_seconds() / 60)} 分钟\n"

        report += f"\n当前使用: 密钥 #{self.current_index + 1}\n"
        report += "=" * 30 + "\n"

        return report

    def reset_all_keys(self):
        """重置所有密钥状态（用于测试或强制重置）"""
        for key in self.api_keys:
            self.key_status[key]['is_available'] = True
            self.key_status[key]['error_count'] = 0
        print("所有API密钥状态已重置")


# 预配置的密钥列表 - 从环境变量读取
# 优先使用环境变量，不再从配置文件读取以避免API密钥泄露
import os

DEFAULT_API_KEYS = []

# 从环境变量读取 API keys（支持多种格式）
def _load_gemini_keys_from_env():
    """从环境变量加载 Gemini API keys"""
    keys = []

    # 方式1: GEMINI_API_KEY_1, GEMINI_API_KEY_2, ...
    i = 1
    while True:
        key = os.environ.get(f'GEMINI_API_KEY_{i}')
        if key:
            keys.append(key.strip())
            i += 1
        else:
            break

    # 方式2: GEMINI_API_KEYS (逗号分隔)
    if not keys:
        env_keys = os.environ.get('GEMINI_API_KEYS', '')
        if env_keys:
            keys = [k.strip() for k in env_keys.split(',') if k.strip()]

    # 方式3: 单个 GEMINI_API_KEY
    if not keys:
        single_key = os.environ.get('GEMINI_API_KEY', '')
        if single_key:
            keys = [single_key.strip()]

    return keys

DEFAULT_API_KEYS = _load_gemini_keys_from_env()


def create_default_rotator(cooldown_minutes: int = 60) -> Optional[APIKeyRotator]:
    """
    创建使用默认密钥列表的轮换器

    Args:
        cooldown_minutes: 冷却时间（分钟）

    Returns:
        配置好的APIKeyRotator实例，如果没有配置密钥则返回None
    """
    if not DEFAULT_API_KEYS:
        return None
    return APIKeyRotator(DEFAULT_API_KEYS, cooldown_minutes)


# 使用示例
if __name__ == "__main__":
    # 创建轮换器
    rotator = create_default_rotator(cooldown_minutes=60)

    # 获取当前密钥
    current_key = rotator.get_current_key()
    print(f"当前密钥: {current_key[:20]}...")

    # 模拟成功调用
    rotator.mark_success()

    # 模拟配额用完
    rotator.mark_quota_exceeded()

    # 查看状态
    print(rotator.get_status_report())
