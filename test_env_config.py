#!/usr/bin/env python3
"""测试环境变量配置是否正确"""

import os
import sys
from pathlib import Path

# 添加src到路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_env_variables():
    """测试环境变量配置"""
    print("=" * 70)
    print("环境变量配置测试")
    print("=" * 70)

    # 测试 Gemini API keys
    print("\n📝 检查 Gemini API Keys...")

    gemini_keys = []

    # 方式1: GEMINI_API_KEY_1, GEMINI_API_KEY_2, ...
    i = 1
    while True:
        key = os.environ.get(f'GEMINI_API_KEY_{i}')
        if key:
            gemini_keys.append(key)
            print(f"  ✓ 找到 GEMINI_API_KEY_{i}: {key[:15]}...{key[-4:]}")
            i += 1
        else:
            break

    # 方式2: GEMINI_API_KEYS (逗号分隔)
    if not gemini_keys:
        env_keys = os.environ.get('GEMINI_API_KEYS', '')
        if env_keys:
            gemini_keys = [k.strip() for k in env_keys.split(',') if k.strip()]
            print(f"  ✓ 找到 GEMINI_API_KEYS: {len(gemini_keys)} 个 keys")

    # 方式3: 单个 GEMINI_API_KEY
    if not gemini_keys:
        single_key = os.environ.get('GEMINI_API_KEY', '')
        if single_key:
            gemini_keys = [single_key]
            print(f"  ✓ 找到 GEMINI_API_KEY: {single_key[:15]}...{single_key[-4:]}")

    if not gemini_keys:
        print("  ⚠️  未找到任何 Gemini API keys！")
        print("\n💡 如何配置:")
        print("     方式1: export GEMINI_API_KEY_1='your-key-here'")
        print("     方式2: export GEMINI_API_KEYS='key1,key2,key3'")
        print("     方式3: 创建 .env 文件（参考 .env.example）")
        return False
    else:
        print(f"\n✅ 总共找到 {len(gemini_keys)} 个 Gemini API key(s)")

    # 测试导入 APIKeyRotator
    print("\n📦 测试导入 APIKeyRotator...")
    try:
        from utils.api_key_rotator import create_default_rotator, DEFAULT_API_KEYS

        if DEFAULT_API_KEYS:
            print(f"  ✓ DEFAULT_API_KEYS 已加载: {len(DEFAULT_API_KEYS)} 个 keys")
            print(f"  ✓ 第一个 key: {DEFAULT_API_KEYS[0][:15]}...{DEFAULT_API_KEYS[0][-4:]}")

            rotator = create_default_rotator()
            if rotator:
                print(f"  ✓ APIKeyRotator 创建成功")
                print(f"  ✓ 当前使用: key #{rotator.current_index + 1}")
            else:
                print(f"  ⚠️  APIKeyRotator 创建失败")
        else:
            print(f"  ⚠️  DEFAULT_API_KEYS 为空")

    except Exception as e:
        print(f"  ❌ 导入失败: {e}")
        return False

    # 测试 DataDistiller
    print("\n📦 测试导入 DataDistiller...")
    try:
        from data_prep import DataDistiller

        # 尝试创建实例（使用环境变量）
        distiller = DataDistiller(use_rotation=True)
        print(f"  ✓ DataDistiller 创建成功")

        if distiller.rotator:
            print(f"  ✓ API key 轮换器已启用")
            print(f"  ✓ 可用 keys: {len(distiller.rotator.api_keys)} 个")
        else:
            print(f"  ⚠️  未配置 API keys，将使用智谱 AI")

    except Exception as e:
        print(f"  ❌ 创建失败: {e}")
        import traceback
        traceback.print_exc()
        return False

    print("\n" + "=" * 70)
    print("✅ 环境变量配置测试通过！")
    print("=" * 70)

    return True


if __name__ == "__main__":
    success = test_env_variables()

    if not success:
        print("\n⚠️  环境变量配置不完整")
        print("\n请参考以下步骤配置:")
        print("  1. 复制 .env.example 为 .env")
        print("  2. 在 .env 中填入你的 API keys")
        print("  3. 运行: source .env  (Linux/Mac)")
        print("  4. 或者: export GEMINI_API_KEY_1='your-key'")
        sys.exit(1)
    else:
        print("\n🎉 所有测试通过！可以开始使用了。")
        sys.exit(0)
