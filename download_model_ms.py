"""使用ModelScope下载模型"""
from modelscope import snapshot_download

print("开始从ModelScope下载 Qwen2.5-0.5B 模型...")

try:
    model_dir = snapshot_download(
        'Qwen/Qwen2.5-0.5B',
        cache_dir='~/.cache/modelscope'
    )
    print(f"\n✅ 模型下载完成！")
    print(f"路径: {model_dir}")
except Exception as e:
    print(f"\n❌ 下载失败: {e}")
    import traceback
    traceback.print_exc()
