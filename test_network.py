#!/usr/bin/env python3
"""测试网络连接和模型下载"""

import sys
import os
import requests
from pathlib import Path


def test_network_connectivity():
    """测试网络连接"""
    print("🔍 测试网络连接状况...")

    # 测试站点列表
    test_sites = [
        ("HuggingFace", "https://huggingface.co"),
        ("HuggingFace镜像", "https://hf-mirror.com"),
        ("ModelScope", "https://modelscope.cn"),
    ]

    results = {}

    for name, url in test_sites:
        try:
            print(f"📡 测试连接到 {name}...")
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                results[name] = "✅ 连接成功"
                print(f"✅ {name} 连接成功")
            else:
                results[name] = f"⚠️  HTTP {response.status_code}"
                print(f"⚠️  {name} HTTP {response.status_code}")
        except Exception as e:
            results[name] = f"❌ 连接失败: {str(e)}"
            print(f"❌ {name} 连接失败: {str(e)}")

    return results


def test_model_download():
    """测试模型下载"""
    print("\n🔍 测试模型下载...")

    # 设置环境变量使用镜像
    os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

    try:
        from transformers import AutoTokenizer

        model_name = "Qwen/Qwen2.5-0.5B"
        print(f"📥 尝试下载模型tokenizer: {model_name}")

        # 尝试下载tokenizer（比完整模型小）
        tokenizer = AutoTokenizer.from_pretrained(
            model_name, trust_remote_code=False, local_files_only=False
        )

        print("✅ Tokenizer下载成功")
        return True

    except Exception as e:
        print(f"❌ Tokenizer下载失败: {str(e)}")
        return False


def test_modelscope_cache():
    """测试ModelScope缓存"""
    print("\n🔍 测试ModelScope缓存...")

    modelscope_cache = Path.home() / ".cache/modelscope"
    if modelscope_cache.exists():
        print(f"✅ ModelScope缓存目录存在: {modelscope_cache}")

        # 列出缓存的模型
        model_dirs = [d for d in modelscope_cache.iterdir() if d.is_dir()]
        if model_dirs:
            print(f"📁 缓存的模型数量: {len(model_dirs)}")
            for model_dir in model_dirs[:5]:  # 只显示前5个
                print(f"   - {model_dir.name}")
        else:
            print("📁 缓存目录为空")
        return True
    else:
        print(f"❌ ModelScope缓存目录不存在: {modelscope_cache}")
        return False


def main():
    """主函数"""
    print("=" * 60)
    print("🌐 网络连接和模型下载测试")
    print("=" * 60)

    # 测试网络连接
    network_results = test_network_connectivity()

    # 测试ModelScope缓存
    modelscope_ok = test_modelscope_cache()

    # 测试模型下载
    download_ok = test_model_download()

    print("\n" + "=" * 60)
    print("📊 测试结果总结")
    print("=" * 60)

    print("\n🌐 网络连接测试:")
    for name, result in network_results.items():
        print(f"   {name}: {result}")

    print(f"\n📁 ModelScope缓存: {'✅' if modelscope_ok else '❌'}")
    print(f"📥 模型下载测试: {'✅' if download_ok else '❌'}")

    # 给出建议
    print("\n💡 建议:")
    if (
        "HuggingFace镜像" in network_results
        and "✅" in network_results["HuggingFace镜像"]
    ):
        print("   - 可以使用HuggingFace镜像 (hf-mirror.com) 下载模型")

    if "ModelScope" in network_results and "✅" in network_results["ModelScope"]:
        print("   - 可以使用ModelScope下载模型")

    if not download_ok:
        print("   - 模型下载失败，请检查网络连接或配置代理")

    if modelscope_ok:
        print("   - 建议优先使用ModelScope缓存中的模型")

    print("\n🔧 配置建议:")
    print("   - 设置环境变量: export HF_ENDPOINT=https://hf-mirror.com")
    print("   - 或在代码中设置: os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'")

    return download_ok


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
