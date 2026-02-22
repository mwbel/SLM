"""Gradio UI应用"""

import gradio as gr

def create_ui():
    """创建Gradio界面"""

    with gr.Blocks() as app:
        gr.Markdown("# SLM Trainer")

        with gr.Tab("数据准备"):
            file_input = gr.File(label="上传文件")
            process_btn = gr.Button("处理数据")

        with gr.Tab("模型训练"):
            train_btn = gr.Button("开始训练")
            progress = gr.Progress()

        with gr.Tab("模型测试"):
            chatbot = gr.Chatbot()
            msg = gr.Textbox(label="输入")
            send_btn = gr.Button("发送")

    return app
