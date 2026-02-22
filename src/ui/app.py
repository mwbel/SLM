"""Gradio UI应用"""

import gradio as gr
import os
import sys
from pathlib import Path

# 添加src到路径
sys.path.insert(0, str(Path(__file__).parent.parent))


def create_ui():
    """创建Gradio界面"""

    def process_file(file):
        """处理上传的文件"""
        if file is None:
            return "请先上传文件", ""

        try:
            # 延迟导入，避免启动时加载
            from data_prep import DataDistiller

            # 初始化数据蒸馏器
            distiller = DataDistiller()

            # 获取上传文件路径
            file_path = file.name

            # 处理文件
            output_path = distiller.process_file(
                file_path=file_path,
                output_dir="data",
                num_pairs=15
            )

            # 读取生成的JSONL内容预览
            preview = ""
            with open(output_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()[:3]  # 只显示前3条
                preview = "\n".join(lines)

            status = f"✅ 处理完成！\n\n文件: {Path(file_path).name}\n输出: {output_path}\n生成对话对数量: {len(lines)}"

            return status, preview

        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()
            return f"❌ 处理失败: {str(e)}\n\n详细错误:\n{error_detail}", ""

    def get_api_status():
        """获取API密钥状态"""
        try:
            from data_prep import DataDistiller
            distiller = DataDistiller()
            return distiller.get_status_report()
        except Exception as e:
            return f"无法获取状态: {str(e)}"

    with gr.Blocks(title="SLM Trainer") as app:
        gr.Markdown("# SLM Trainer - 垂直小模型训练工具")

        with gr.Tab("数据准备"):
            gr.Markdown("## 📄 文档上传与知识蒸馏")
            gr.Markdown("上传PDF或TXT文件，使用Gemini API自动提取知识并生成训练数据")

            with gr.Row():
                with gr.Column():
                    file_input = gr.File(label="上传文件 (PDF/TXT)", file_types=[".pdf", ".txt"])
                    process_btn = gr.Button("🚀 开始处理", variant="primary")

                with gr.Column():
                    status_output = gr.Textbox(label="处理状态", lines=6, interactive=False)

            gr.Markdown("### 生成数据预览")
            preview_output = gr.Textbox(label="JSONL预览 (前3条)", lines=10, interactive=False)

            gr.Markdown("### API密钥状态")
            api_status_btn = gr.Button("🔍 查看密钥状态")
            api_status_output = gr.Textbox(label="密钥使用情况", lines=15, interactive=False)

            # 绑定事件
            process_btn.click(
                fn=process_file,
                inputs=[file_input],
                outputs=[status_output, preview_output]
            )

            api_status_btn.click(
                fn=get_api_status,
                inputs=[],
                outputs=[api_status_output]
            )

        with gr.Tab("模型训练"):
            gr.Markdown("## 🎯 模型训练")
            gr.Markdown("配置训练参数并开始微调模型（功能开发中）")

            train_btn = gr.Button("开始训练", variant="primary")
            progress = gr.Textbox(label="训练进度", lines=5)

        with gr.Tab("模型测试"):
            gr.Markdown("## 💬 模型对话测试")
            gr.Markdown("加载训练好的模型进行对话测试（功能开发中）")

            chatbot = gr.Chatbot(type="messages")
            msg = gr.Textbox(label="输入消息")
            send_btn = gr.Button("发送")

    return app
