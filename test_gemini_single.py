#!/usr/bin/env python3
"""测试单个 Gemini API key - 使用正确的 SDK 用法"""

import json
from pathlib import Path
import google.generativeai as genai

def test_api_key_with_genai_sdk(api_key):
    """使用正确的 SDK 测试 API key"""
    try:
        # 配置 API key
        genai.configure(api_key=api_key)

        # 尝试列出可用的模型
        models = genai.list_models()
        model_names = [m.name for m in models]

        # 尝试使用 flash 模型
        flash_models = [m for m in model_names if 'flash' in m.lower()]

        if flash_models:
            model_name = flash_models[0]
        else:
            # 使用默认模型
            model_name = 'models/gemini-pro'

        # 发送测试请求
        model = genai.GenerativeModel(model_name)
        response = model.generate_content("Hello, please respond with 'OK' if you receive this.")

        if response and response.text:
            return True, f"✓ 可用 (模型: {model_name})", response.text[:50]
        else:
            return False, "✗ 无响应", ""

    except Exception as e:
        error_msg = str(e)
        if "QUOTA_EXCEEDED" in error_msg or "quota" in error_msg.lower():
            return False, "✗ 配额已用完", error_msg
        elif "API_KEY" in error_msg or "invalid" in error_msg.lower() or "not found" in error_msg.lower():
            return False, "✗ API key 无效", error_msg
        elif "permission" in error_msg.lower():
            return False, "✗ 权限不足", error_msg
        else:
            return False, f"✗ 错误", error_msg[:200]

def main():
    """测试第一个可用的 key"""
    config_file = Path(__file__).parent / 'config' / 'api_config.json'
    with open(config_file, 'r') as f:
        config = json.load(f)
        api_keys = config.get('gemini', [])

    print("测试前3个 API keys...\n")

    for i, key_info in enumerate(api_keys[:3], 1):
        api_key = key_info['api_key']
        name = key_info.get('name', f'Key-{i}')
        api_key_preview = api_key[:20] + "..."

        print(f"[{i}] 测试 {name} ({api_key_preview})...")
        success, status, details = test_api_key_with_genai_sdk(api_key)

        print(f"  结果: {status}")
        if details:
            print(f"  详情: {details[:100]}")
        print()

if __name__ == "__main__":
    main()
