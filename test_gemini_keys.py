#!/usr/bin/env python3
"""测试 Gemini API keys 是否可用"""

import json
from pathlib import Path
from google import genai
from google.genai import types

def load_api_keys():
    """从配置文件加载 API keys"""
    config_file = Path(__file__).parent / 'config' / 'api_config.json'
    with open(config_file, 'r') as f:
        config = json.load(f)
        return config.get('gemini', [])

def test_api_key(api_key_info):
    """测试单个 API key"""
    api_key = api_key_info['api_key']
    model = api_key_info.get('model', 'gemini-1.5-flash')
    name = api_key_info.get('name', 'Unknown')

    try:
        # 初始化客户端
        client = genai.Client(api_key=api_key)

        # 发送一个简单的测试请求
        response = client.models.generate_content(
            model=model,
            contents="Hello, please respond with 'OK' if you receive this."
        )

        # 检查响应
        if response and response.text:
            return True, "✓ 可用", response.text[:50]
        else:
            return False, "✗ 无响应", ""

    except Exception as e:
        error_msg = str(e)
        if "QUOTA_EXCEEDED" in error_msg or "quota" in error_msg.lower():
            return False, "✗ 配额已用完", error_msg
        elif "API_KEY" in error_msg or "invalid" in error_msg.lower():
            return False, "✗ API key 无效", error_msg
        elif "permission" in error_msg.lower():
            return False, "✗ 权限不足", error_msg
        else:
            return False, f"✗ 错误", error_msg

def main():
    """主测试函数"""
    print("=" * 60)
    print("Gemini API Keys 测试")
    print("=" * 60)

    # 加载 API keys
    api_keys = load_api_keys()
    print(f"\n找到 {len(api_keys)} 个 API key\n")

    # 测试每个 key
    results = []
    for i, key_info in enumerate(api_keys, 1):
        name = key_info.get('name', f'Key-{i}')
        api_key_preview = key_info['api_key'][:20] + "..."

        print(f"[{i}/{len(api_keys)}] 测试 {name} ({api_key_preview})...")
        success, status, details = test_api_key(key_info)

        results.append({
            'index': i,
            'name': name,
            'success': success,
            'status': status,
            'details': details
        })

        print(f"  结果: {status}")
        if details and len(details) > 0:
            print(f"  详情: {details[:100]}")
        print()

    # 汇总报告
    print("=" * 60)
    print("测试结果汇总")
    print("=" * 60)

    available_count = sum(1 for r in results if r['success'])
    total_count = len(results)

    print(f"\n总计: {available_count}/{total_count} 个 API key 可用\n")

    for result in results:
        status_icon = "✓" if result['success'] else "✗"
        print(f"{status_icon} [{result['index']}] {result['name']}: {result['status']}")

    print("\n" + "=" * 60)

    if available_count == 0:
        print("⚠️  警告: 所有 API keys 都不可用！")
        print("建议:")
        print("  1. 检查 API keys 是否正确")
        print("  2. 确认 Google Cloud 配额是否充足")
        print("  3. 检查网络连接")
    elif available_count < total_count:
        print(f"⚠️  部分可用: {available_count} 个可用，{total_count - available_count} 个不可用")
    else:
        print("✅ 所有 API keys 都可用！")

    print("=" * 60)

if __name__ == "__main__":
    main()
