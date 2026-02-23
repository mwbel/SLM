"""手动下载模型"""
import os
from huggingface_hub import snapshot_download

# 设置镜像
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'

print("开始下载 Qwen/Qwen2.5-0.5B 模型...")
print("使用镜像: https://hf-mirror.com")

try:
    model_path = snapshot_download(
        repo_id="Qwen/Qwen2.5-0.5B",
        resume_download=True,
        max_workers=4
    )
    print(f"\n✅ 模型下载完成！")
    print(f"路径: {model_path}")
except Exception as e:
    print(f"\n❌ 下载失败: {e}")
    import traceback
    traceback.print_exc()
