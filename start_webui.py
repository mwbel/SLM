#!/usr/bin/env python3
"""
启动Gradio Web界面
提供友好的Web UI进行模型训练和测试
"""

import sys
import os
from pathlib import Path

# 添加src到路径
sys.path.insert(0, str(Path(__file__).parent / "src"))


def main():
    """启动Web UI"""
    print("=" * 70)
    print("🚀 启动 SLM Trainer Web 界面")
    print("=" * 70)
    print()

    # 导入Gradio应用
    try:
        from ui.app import create_ui

        # 创建UI
        print("📦 创建Web界面...")
        app = create_ui()

        print("✅ Web界面准备就绪！")
        print()
        print("=" * 70)
        print("🌐 Web服务信息")
        print("=" * 70)
        print()
        print("📍 访问地址:")
        print("   - 本地访问: http://127.0.0.1:7860")
        print("   - 局域网访问: http://本机IP:7860")
        print()
        print("💡 功能模块:")
        print("   1. 📄 数据准备 - 上传文档，生成训练数据")
        print("   2. 🎯 模型训练 - 配置参数，训练模型")
        print("   3. 💬 模型测试 - 对话测试，验证效果")
        print()
        print("📝 训练好的模型位置:")
        print("   - outputs/qwen2_5-3b-trained/")
        print()
        print("⚠️  按 Ctrl+C 停止服务")
        print("=" * 70)
        print()

        # 启动服务
        app.launch(
            server_name="0.0.0.0",  # 允许局域网访问
            server_port=7860,
            share=False,  # 不创建公网链接
            show_error=True,
            quiet=False,
        )

    except ImportError as e:
        print(f"❌ 导入失败: {e}")
        print()
        print("💡 请确保已安装所有依赖:")
        print("   pip3 install -r requirements.txt")
        return False

    except Exception as e:
        print(f"❌ 启动失败: {e}")
        import traceback

        traceback.print_exc()
        return False

    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
