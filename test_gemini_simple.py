#!/usr/bin/env python3
"""简单的 Gemini API Key 测试 - 使用 google-genai SDK"""

import json
from pathlib import Path
from google import genai

def test_gemini_key(api_key):
    """测试单个 API key"""
    try:
        # 创建客户端
        client = genai.Client(api_key=api_key)

        # 测试生成内容
        response = client.models.generate_content(
            model="gemini-2.0-flash-exp",
            contents="Hello"
        )

        if response and response.text:
            return True, "✓ 可用", response.text[:100]
        else:
            return False, "✗ 无响应", ""

    except Exception as e:
        error_str = str(e)
        # 判断错误类型
        if "API key" in error_str and ("invalid" in error_str.lower() or "not found" in error_str.lower()):
            return False, "✗ API key 无效", error_str[:100]
        elif "expired" in error_str.lower():
            return False, "✗ API key 已过期", error_str[:100]
        elif "quota" in error_str.lower():
            return False, "✗ 配额用尽", error_str[:100]
        elif "permission" in error_str.lower():
            return False, "✗ 权限不足", error_str[:100]
        else:
            return False, "✗ 未知错误", error_str[:150]

def main():
    print("=" * 70)
    print("Gemini API Keys 快速测试")
    print("=" * 70)

    # 加载配置
    config_file = Path(__file__).parent / 'config' / 'api_config.json'
    with open(config_file, 'r') as f:
        config = json.load(f)
        api_keys = config.get('gemini', [])

    print(f"\n找到 {len(api_keys)} 个 API key\n")

    # 测试每个 key
    available_count = 0
    for i, key_info in enumerate(api_keys, 1):
        api_key = key_info['api_key']
        name = key_info.get('name', f'Key-{i}')
        preview = api_key[:15] + "..."

        print(f"[{i}/{len(api_keys)}] {name} ({preview})")
        success, status, detail = test_gemini_key(api_key)

        print(f"  状态: {status}")
        if detail:
            print(f"  详情: {detail}")
        print()

        if success:
            available_count += 1

    # 汇总
    print("=" * 70)
    print(f"结果: {available_count}/{len(api_keys)} 个 API key 可用")
    print("=" * 70)

if __name__ == "__main__":
    main()
