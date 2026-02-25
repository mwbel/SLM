#!/usr/bin/env python3
"""测试新的 Gemini API keys 是否可用"""

import os
from google import genai

def test_api_key(api_key, index):
    """测试单个 API key"""
    try:
        # 创建客户端
        client = genai.Client(api_key=api_key)

        # 测试生成内容
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents="Hi"
        )

        if response and response.text:
            return True, "✓ 可用", response.text[:50]
        else:
            return False, "✗ 无响应", ""

    except Exception as e:
        error_str = str(e)
        if "API key" in error_str and ("invalid" in error_str.lower() or "not found" in error_str.lower()):
            return False, "✗ API key 无效", error_str[:100]
        elif "expired" in error_str.lower():
            return False, "✗ API key 已过期", error_str[:100]
        elif "quota" in error_str.lower():
            return False, "✗ 配额用尽", error_str[:100]
        else:
            return False, f"✗ 错误", error_str[:150]

def main():
    print("=" * 70)
    print("测试新的 Gemini API Keys")
    print("=" * 70)

    # 从环境变量读取 keys
    keys = []
    i = 1
    while True:
        key = os.environ.get(f'GEMINI_API_KEY_{i}')
        if key:
            keys.append(key)
            i += 1
        else:
            break

    if not keys:
        print("❌ 未找到任何 API keys！")
        return

    print(f"\n找到 {len(keys)} 个 API key\n")

    # 测试每个 key
    available_count = 0
    for i, key in enumerate(keys, 1):
        key_preview = key[:15] + "..." + key[-4:]
        print(f"[{i}/{len(keys)}] Key #{i} ({key_preview})")

        success, status, detail = test_api_key(key, i)

        print(f"  状态: {status}")
        if success:
            print(f"  详情: {detail}")
            available_count += 1
        elif detail:
            print(f"  错误: {detail[:100]}")
        print()

    # 汇总
    print("=" * 70)
    print(f"结果: {available_count}/{len(keys)} 个 API key 可用")
    print("=" * 70)

    if available_count == len(keys):
        print("\n🎉 所有 API keys 都可用！")
    elif available_count > 0:
        print(f"\n⚠️  部分可用: {available_count} 个可用，{len(keys) - available_count} 个不可用")
    else:
        print("\n❌ 所有 API keys 都不可用！")

if __name__ == "__main__":
    main()
