#!/usr/bin/env python3
"""
使用 ModelScope 下载 Qwen2.5-1.5B 模型
"""

import os
from pathlib import Path

def download_qwen_15b():
    """下载 Qwen2.5-1.5B 模型"""

    print("=" * 70)
    print("下载 Qwen2.5-1.5B 模型（升级版）")
    print("=" * 70)

    print("\n模型信息：")
    print("  名称: Qwen/Qwen2.5-1.5B")
    print("  大小: ~1.2 GB (约为0.5B模型的2.5倍)")
    print("  参数量: 1.5B (15亿参数)")
    print("  性能: 比0.5B模型强3倍以上")
    print("  下载源: ModelScope (阿里云，国内快速)")
    print("  预计时间: 10-20 分钟")

    # 设置缓存目录
    cache_dir = Path("./models")
    cache_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n保存位置: {cache_dir.absolute()}")

    try:
        from modelscope import snapshot_download

        print("\n开始下载...")
        print("(这可能需要10-20分钟，请耐心等待...)\n")

        # 下载模型
        model_dir = snapshot_download(
            'Qwen/Qwen2.5-1.5B',
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
        total_size = 0
        for file in sorted(model_path.iterdir()):
            if file.is_file():
                size_mb = file.stat().st_size / (1024 * 1024)
                total_size += size_mb
                print(f"  ✓ {file.name} ({size_mb:.1f} MB)")

        print(f"\n总大小: {total_size:.1f} MB ({total_size/1024:.2f} GB)")

        print("\n优势：")
        print("  • 更强的知识记忆能力")
        print("  • 更好的推理和理解能力")
        print("  • 更准确的回答质量")
        print("  • 仍然保持轻量（1.2GB）")

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
    model_dir = download_qwen_15b()

    if model_dir:
        print("\n✅ 完成！模型已下载到本地")
        print("\n下一步:")
        print("  1. 更新 config.yaml 中的模型路径")
        print("  2. 重新训练模型以应用新基座")
    else:
        print("\n❌ 下载失败，请检查网络连接")
