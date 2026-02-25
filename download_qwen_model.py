#!/usr/bin/env python3
"""
下载 Qwen2.5-0.5B 模型
支持使用镜像站点加速下载
"""

import os
import sys
from pathlib import Path

def download_model_with_mirror():
    """使用镜像下载模型"""

    # 设置 HuggingFace 镜像（中国大陆可用）
    mirrors = [
        "https://hf-mirror.com",  # 主要镜像
        "https://huggingface.co",  # 官方源
    ]

    model_id = "Qwen/Qwen2.5-0.5B"

    print("=" * 70)
    print("下载 Qwen2.5-0.5B 模型")
    print("=" * 70)
    print(f"\n模型: {model_id}")
    print(f"大小: ~1 GB (500M 参数，FP32 精度)")
    print(f"预计时间: 5-15 分钟 (取决于网络速度)\n")

    # 尝试不同的镜像
    for i, mirror in enumerate(mirrors, 1):
        print(f"尝试镜像 #{i}: {mirror}")

        # 设置环境变量
        os.environ['HF_ENDPOINT'] = mirror

        try:
            from transformers import AutoModelForCausalLM, AutoTokenizer
            from huggingface_hub import snapshot_download

            # 下载模型到缓存目录
            print("  开始下载...")
            cache_dir = Path.home() / '.cache' / 'huggingface' / 'hub'

            # 使用 snapshot_download 下载完整模型
            model_path = snapshot_download(
                repo_id=model_id,
                cache_dir=cache_dir,
                local_dir=None,  # 使用缓存
                local_dir_use_symlinks=False,
                resume_download=True
            )

            print(f"\n✅ 模型下载成功！")
            print(f"   路径: {model_path}")

            # 测试加载
            print("\n测试加载模型...")
            tokenizer = AutoTokenizer.from_pretrained(model_id)
            model = AutoModelForCausalLM.from_pretrained(
                model_id,
                torch_dtype="auto",
                device_map="auto"
            )

            print("✅ 模型加载成功！")
            print(f"   参数量: {model.num_parameters() / 1e6:.1f}M")
            print(f"   数据类型: {model.dtype}")

            return True

        except Exception as e:
            error_msg = str(e)
            print(f"  ❌ 失败: {error_msg[:100]}")

            if i < len(mirrors):
                print(f"  尝试下一个镜像...\n")
            else:
                print("\n所有镜像都失败了。")
                return False

def download_model_manual():
    """
    手动下载说明
    """
    print("\n" + "=" * 70)
    print("手动下载说明")
    print("=" * 70)

    print("""
如果自动下载失败，你可以手动下载模型：

方法 1: 使用 huggingface-cli (推荐)
--------------------------------------
# 安装 huggingface-cli
pip3 install -U "huggingface_hub[cli]"

# 使用镜像下载
HF_ENDPOINT=https://hf-mirror.com huggingface-cli download Qwen/Qwen2.5-0.5B --local-dir models/Qwen2.5-0.5B

方法 2: 使用 git clone
--------------------------------------
# 安装 git-lfs
brew install git-lfs
git lfs install

# 克隆模型仓库
git clone https://hf-mirror.com/Qwen/Qwen2.5-0.5B models/Qwen2.5-0.5B

方法 3: 直接下载文件
--------------------------------------
1. 访问: https://hf-mirror.com/Qwen/Qwen2.5-0.5B/tree/main
2. 下载以下文件到 models/Qwen2.5-0.5B/:
   - config.json
   - model.safetensors (或 pytorch_model.bin)
   - tokenizer.json
   - tokenizer_config.json
   - special_tokens_map.json
   - vocab.json
   - merges.txt

下载完成后，修改配置文件 config.yaml:
model:
  base_model: "models/Qwen2.5-0.5B"
""")

if __name__ == "__main__":
    print("""
╔═══════════════════════════════════════════════════════════════╗
║                 Qwen2.5-0.5B 模型下载工具                      ║
╚═══════════════════════════════════════════════════════════════╝
""")

    # 自动下载
    success = download_model_with_mirror()

    if not success:
        # 显示手动下载说明
        download_model_manual()

        print("\n" + "=" * 70)
        print("💡 提示")
        print("=" * 70)
        print("""
1. 确保网络连接正常
2. 如果在中国大陆，建议使用 VPN 或镜像站点
3. 模型文件较大 (~1GB)，请耐心等待
4. 下载成功后，模型会缓存到 ~/.cache/huggingface/hub/
        """)
