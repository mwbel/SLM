#!/usr/bin/env python3
"""
使用 ModelScope 下载 Qwen2.5-3B 模型
ModelScope 是阿里云提供的，国内访问速度快
"""

import os
import sys
from pathlib import Path

def download_model():
    """使用 ModelScope 下载模型"""

    print("=" * 70)
    print("使用 ModelScope 下载 Qwen2.5-3B 模型")
    print("=" * 70)

    print("\n模型信息：")
    print("  名称: Qwen/Qwen2.5-3B")
    print("  大小: ~6 GB")
    print("  参数量: 3B (30亿)")
    print("  下载源: ModelScope (阿里云，国内快速)")
    print("  预计时间: 10-30 分钟")

    # 设置缓存目录
    cache_dir = Path("./models")
    cache_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n保存位置: {cache_dir.absolute()}")

    try:
        from modelscope import snapshot_download

        print("\n开始下载...")
        print("(这可能需要几分钟，请耐心等待...)\n")

        # 下载模型
        model_dir = snapshot_download(
            'Qwen/Qwen2.5-3B',
            cache_dir=cache_dir,
            revision='master'
        )

        print("\n" + "=" * 70)
        print("✅ 模型下载成功！")
        print("=" * 70)
        print(f"\n模型路径: {model_dir}")

        # 列出下载的文件
        model_path = Path(model_dir)
        print("\n下载的文件:")
        for file in sorted(model_path.iterdir()):
            if file.is_file():
                size_mb = file.stat().st_size / (1024 * 1024)
                print(f"  ✓ {file.name} ({size_mb:.1f} MB)")

        print("\n下一步:")
        print("  1. 更新 config.yaml 使用新模型:")
        print(f"     model:")
        print(f"       base_model: \"{model_dir}\"")
        print("  2. 开始训练你的垂直领域模型！")

        return model_dir

    except ImportError:
        print("\n❌ ModelScope 未安装")
        print("请运行: pip3 install modelscope")
        return None
    except Exception as e:
        print(f"\n❌ 下载失败: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    model_dir = download_model()

    if model_dir:
        print("\n✅ 完成！模型已下载到本地")
        sys.exit(0)
    else:
        print("\n❌ 下载失败，请检查网络连接")
        sys.exit(1)
