#!/usr/bin/env python3
"""测试 keys 7-9 使用正确的模型"""

import json
from pathlib import Path
from google import genai

def test_with_different_models(api_key):
    """使用不同的模型测试"""
    client = genai.Client(api_key=api_key)

    # 尝试不同的模型
    models_to_try = [
        "gemini-1.5-flash",
        "gemini-1.5-flash-001",
        "gemini-1.5-pro",
        "models/gemini-1.5-flash",
        "models/gemini-pro",
    ]

    for model in models_to_try:
        try:
            response = client.models.generate_content(
                model=model,
                contents="Hi"
            )
            if response and response.text:
                return True, f"✓ 可用 (模型: {model})", response.text[:50]
        except Exception as e:
            error_str = str(e)
            if "API key" in error_str or "invalid" in error_str.lower():
                return False, "✗ API key 无效", error_str[:100]
            # 如果是模型未找到，继续尝试下一个
            if "not found" not in error_str.lower():
                return False, f"✗ 错误 ({model})", error_str[:100]

    return False, "✗ 所有模型都失败", ""

def main():
    config_file = Path(__file__).parent / 'config' / 'api_config.json'
    with open(config_file, 'r') as f:
        config = json.load(f)
        api_keys = config.get('gemini', [])

    print("测试 Keys 7-9（使用不同模型）\n")

    # 只测试最后3个
    for i in range(6, 9):
        key_info = api_keys[i]
        api_key = key_info['api_key']
        name = key_info.get('name', f'Key-{i+1}')
        preview = api_key[:15] + "..."

        print(f"[{i+1}] {name} ({preview})")
        success, status, detail = test_with_different_models(api_key)

        print(f"  状态: {status}")
        if detail:
            print(f"  详情: {detail}")
        print()

if __name__ == "__main__":
    main()
