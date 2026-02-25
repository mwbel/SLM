"""Gradio UI应用"""

import gradio as gr
import os
import sys
from pathlib import Path

# 添加src到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

# 定位 slm-trainer 根目录
CURRENT_DIR = Path(__file__).resolve().parent
SLM_TRAINER_DIR = CURRENT_DIR.parent.parent
DATA_DIR = SLM_TRAINER_DIR / "data"
OUTPUTS_DIR = SLM_TRAINER_DIR / "outputs"
DOMAIN_KNOWLEDGE_DIR = SLM_TRAINER_DIR.parent / "domain_knowledge"


def list_files(directory, extension=None):
    """列出指定目录下的文件"""
    files = []
    dir_path = Path(directory)
    if not dir_path.exists():
        return files

    for f in dir_path.iterdir():
        if f.is_file() and (extension is None or f.name.endswith(extension)):
            files.append(str(f))
    return sorted(files)


def list_directories(directory):
    """列出指定目录下的子目录"""
    dirs = []
    dir_path = Path(directory)
    if not dir_path.exists():
        return dirs

    for f in dir_path.iterdir():
        if f.is_dir() and not f.name.startswith("."):
            dirs.append(str(f))
    return sorted(dirs)


BASE_MODELS = [
    "models/Qwen/Qwen2.5-1.5B",  # 升级到1.5B（推荐）
    "models/Qwen/Qwen2.5-3B",    # 更大模型（如需更高精度）
    "models/Qwen/Qwen2.5-0.5B",  # 轻量级（如需更快速度）
    "Qwen/Qwen2.5-1.5B",         # HuggingFace备用
    "Qwen/Qwen2.5-3B",
    "Qwen/Qwen2.5-0.5B",
]


def list_all_pdfs(root_dir):
    """递归列出所有PDF文件"""
    pdfs = []
    root = Path(root_dir)
    if not root.exists():
        return pdfs
    for path in root.rglob("*.pdf"):
        pdfs.append(str(path))
    return sorted(pdfs)


def find_citation(response, pdf_path):
    """在PDF中查找引用页码"""
    if not pdf_path or not os.path.exists(pdf_path):
        return None

    try:
        import fitz

        doc = fitz.open(pdf_path)
        best_page = -1
        max_score = 0

        # 简单算法：字符重叠率 (Jaccard Similarity)
        response_chars = set(response)
        if not response_chars:
            return None

        for i, page in enumerate(doc):
            text = page.get_text()
            page_chars = set(text)

            # 避免除以零
            if not len(response_chars):
                continue

            common = response_chars & page_chars
            score = len(common) / len(response_chars)

            # 阈值 0.15
            if score > max_score and score > 0.15:
                max_score = score
                best_page = i + 1

        doc.close()

        if best_page != -1:
            return best_page
        return None
    except Exception as e:
        print(f"Citation search failed: {e}")
        return None


def create_ui():
    """创建Gradio界面"""

    def process_file(file, num_pairs, progress=gr.Progress()):
        """处理上传的文件"""
        if file is None:
            return "请先上传文件", ""

        try:
            progress(0, desc="开始处理...")

            # 延迟导入，避免启动时加载
            from data_prep import DataDistiller

            progress(0.2, desc="初始化数据蒸馏器...")
            # 初始化数据蒸馏器
            distiller = DataDistiller()

            # 获取上传文件路径
            file_path = file.name

            progress(0.4, desc="分析文档结构...")
            from data_prep.distiller import extract_text

            text = extract_text(file_path)
            total_len = len(text)

            # 智能分块策略：根据目标生成数量动态调整分块大小
            # 目标：让模型在每个小块上生成约 10-15 条数据，避免"偷懒"
            target_pairs = int(num_pairs)
            pairs_per_chunk = 15  # 这是一个模型比较舒适生成的数量

            # 计算需要的块数
            target_chunks = max(1, int(target_pairs / pairs_per_chunk))

            # 计算分块大小
            chunk_size = int(total_len / target_chunks)

            # 边界限制 (限制在 1000-6000 字符之间，保证上下文完整性)
            chunk_size = max(1000, min(chunk_size, 6000))

            progress(0.5, desc=f"执行分块处理 (每块约 {chunk_size} 字符)...")

            # 使用分块处理
            output_path = distiller.process_file_chunked(
                file_path=file_path,
                output_dir=str(DATA_DIR),
                num_pairs_per_chunk=pairs_per_chunk,
                chunk_size=chunk_size,
                overlap=200,
            )

            progress(0.8, desc="生成训练数据...")
            # 读取生成的JSONL内容预览
            preview = ""
            with open(output_path, "r", encoding="utf-8") as f:
                lines = f.readlines()[:3]  # 只显示前3条
                preview = "\n".join(lines)

            progress(1.0, desc="完成！")
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

    def start_training(
        data_file, model_name, epochs, batch_size, learning_rate, progress=gr.Progress()
    ):
        """开始训练"""
        trainer = None
        try:
            import yaml
            import json
            import torch
            from training import Trainer
            from utils import setup_logger

            progress(0, desc="检查训练数据...")
            # 检查数据文件
            if not data_file or not os.path.exists(data_file):
                return "❌ 请先选择有效的训练数据文件"

            progress(0.1, desc="加载配置...")
            # 加载配置
            config_path = Path(__file__).parent.parent.parent / "config.yaml"
            with open(config_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)

            # 更新配置
            config["model"]["base_model"] = model_name
            config["training"]["num_epochs"] = int(epochs)
            config["training"]["batch_size"] = int(batch_size)
            config["training"]["learning_rate"] = float(learning_rate)

            progress(0.2, desc="加载训练数据...")
            # 加载训练数据
            train_data = []
            with open(data_file, "r", encoding="utf-8") as f:
                for line in f:
                    train_data.append(json.loads(line.strip()))

            status = f"📊 训练数据: {len(train_data)} 条样本\n"
            status += f"🤖 基座模型: {model_name}\n"
            status += f"📈 训练轮数: {epochs}\n"
            status += f"📦 批次大小: {batch_size}\n"
            status += f"🎯 学习率: {learning_rate}\n\n"

            progress(0.3, desc="初始化训练器(加载模型)...")
            status += "🚀 正在初始化训练器...\n"

            # 初始化训练器
            trainer = Trainer(model_name=model_name, config=config)

            progress(0.5, desc="训练器初始化完成")
            status += "✅ 训练器初始化完成\n\n"
            status += "🏃 开始训练...\n"

            progress(0.6, desc="执行训练...")
            # 开始训练
            trainer.train(train_data)

            progress(0.9, desc="训练完成,保存模型...")
            status += "✅ 训练完成！\n\n"

            # 保存模型
            output_path = str(OUTPUTS_DIR / "trained_model")
            trainer.save_model(output_path)

            progress(1.0, desc="完成！")
            status += f"💾 模型已保存到: {output_path}\n"

            return status

        except Exception as e:
            import traceback

            error_detail = traceback.format_exc()
            return f"❌ 训练失败: {str(e)}\n\n详细错误:\n{error_detail}"
        finally:
            # 清理资源
            if trainer:
                try:
                    # 清理GPU内存
                    if torch.cuda.is_available():
                        torch.cuda.empty_cache()
                except Exception:
                    pass  # 忽略清理过程中的错误

    with gr.Blocks(title="SLM Trainer") as app:
        gr.Markdown("# SLM Trainer - 垂直小模型训练工具")

        with gr.Tab("数据准备"):
            gr.Markdown("## 📄 文档上传与知识蒸馏")
            gr.Markdown("上传PDF或TXT文件，使用Gemini API自动提取知识并生成训练数据")

            with gr.Row():
                with gr.Column():
                    file_input = gr.File(
                        label="上传文件 (PDF/TXT)", file_types=[".pdf", ".txt"]
                    )
                    num_pairs_input = gr.Number(
                        label="生成样本数量",
                        value=100,
                        minimum=10,
                        maximum=1000,
                        step=10,
                    )
                    process_btn = gr.Button("🚀 开始处理", variant="primary")

                with gr.Column():
                    status_output = gr.Textbox(
                        label="处理状态", lines=6, interactive=False
                    )

            gr.Markdown("### 生成数据预览")
            preview_output = gr.Textbox(
                label="JSONL预览 (前3条)", lines=10, interactive=False
            )

            gr.Markdown("### API密钥状态")
            api_status_btn = gr.Button("🔍 查看密钥状态")
            api_status_output = gr.Textbox(
                label="密钥使用情况", lines=15, interactive=False
            )

            # 绑定事件
            process_btn.click(
                fn=process_file,
                inputs=[file_input, num_pairs_input],
                outputs=[status_output, preview_output],
            )

            api_status_btn.click(
                fn=get_api_status, inputs=[], outputs=[api_status_output]
            )

        with gr.Tab("模型训练"):
            gr.Markdown("## 🎯 模型训练")
            gr.Markdown("配置训练参数并开始微调模型")

            with gr.Row():
                with gr.Column():
                    with gr.Row():
                        data_file_input = gr.Dropdown(
                            label="训练数据文件路径",
                            choices=list_files(DATA_DIR, ".jsonl"),
                            value=(
                                list_files(DATA_DIR, ".jsonl")[0]
                                if list_files(DATA_DIR, ".jsonl")
                                else None
                            ),
                            allow_custom_value=True,
                            interactive=True,
                            scale=3,
                        )
                        refresh_data_btn = gr.Button("🔄", scale=0, min_width=50)

                    model_name_input = gr.Dropdown(
                        label="基座模型",
                        choices=BASE_MODELS,
                        value="models/Qwen/Qwen2.5-1.5B",  # 更新为1.5B
                        allow_custom_value=True,
                        interactive=True,
                    )

                with gr.Column():
                    epochs_input = gr.Number(
                        label="训练轮数", value=3, minimum=1, maximum=10
                    )
                    batch_size_input = gr.Number(
                        label="批次大小", value=2, minimum=1, maximum=8
                    )
                    learning_rate_input = gr.Number(
                        label="学习率", value=0.0002, minimum=0.00001, maximum=0.001
                    )

            train_btn = gr.Button("🚀 开始训练", variant="primary", size="lg")
            progress = gr.Textbox(label="训练进度", lines=15, interactive=False)

            # 绑定刷新按钮
            def refresh_data_files():
                files = list_files(DATA_DIR, ".jsonl")
                return gr.Dropdown(choices=files, value=files[0] if files else None)

            refresh_data_btn.click(fn=refresh_data_files, outputs=[data_file_input])

            # 绑定训练按钮
            train_btn.click(
                fn=start_training,
                inputs=[
                    data_file_input,
                    model_name_input,
                    epochs_input,
                    batch_size_input,
                    learning_rate_input,
                ],
                outputs=[progress],
            )

        with gr.Tab("模型测试"):
            gr.Markdown("## 💬 模型对话测试")
            gr.Markdown("加载训练好的模型进行对话测试")

            with gr.Row():
                with gr.Column(scale=1):
                    with gr.Row():
                        model_path_input = gr.Dropdown(
                            label="模型路径",
                            choices=list_directories(OUTPUTS_DIR),
                            value=str(OUTPUTS_DIR / "trained_model"),
                            allow_custom_value=True,
                            interactive=True,
                            scale=3,
                        )
                        refresh_model_btn = gr.Button("🔄", scale=0, min_width=50)

                    base_model_input = gr.Dropdown(
                        label="基座模型",
                        choices=BASE_MODELS,
                        value="models/Qwen/Qwen2.5-1.5B",  # 更新为1.5B
                        allow_custom_value=True,
                        interactive=True,
                    )

                    ref_doc_input = gr.Dropdown(
                        label="参考文档 (用于生成引用链接)",
                        choices=list_all_pdfs(DOMAIN_KNOWLEDGE_DIR),
                        value=None,
                        allow_custom_value=True,
                        interactive=True,
                    )
                    load_model_btn = gr.Button("🚀 加载模型", variant="primary")
                    model_status = gr.Textbox(
                        label="模型状态", value="未加载", interactive=False, lines=3
                    )
                    clear_btn = gr.Button("🗑️ 清空对话")

                with gr.Column(scale=2):
                    chatbot = gr.Chatbot(type="messages", height=500)
                    msg = gr.Textbox(
                        label="输入消息", placeholder="输入您的问题...", lines=2
                    )
                    with gr.Row():
                        send_btn = gr.Button("发送", variant="primary")
                        stop_btn = gr.Button("停止")

            # 绑定事件
            load_model_btn.click(
                fn=load_model_for_chat,
                inputs=[model_path_input, base_model_input],
                outputs=[model_status],
            )

            msg.submit(
                fn=chat_with_model,
                inputs=[msg, chatbot, ref_doc_input],
                outputs=[chatbot, msg],
            )

            send_btn.click(
                fn=chat_with_model,
                inputs=[msg, chatbot, ref_doc_input],
                outputs=[chatbot, msg],
            )

            clear_btn.click(fn=lambda: [], inputs=[], outputs=[chatbot])

            # 绑定刷新按钮
            def refresh_model_dirs():
                dirs = list_directories(OUTPUTS_DIR)
                default_model = str(OUTPUTS_DIR / "reimbursement_model")
                return gr.Dropdown(
                    choices=dirs,
                    value=(
                        default_model
                        if default_model in dirs
                        else (dirs[0] if dirs else None)
                    ),
                )

            refresh_model_btn.click(fn=refresh_model_dirs, outputs=[model_path_input])

    return app


# 全局变量存储推理器
_inferencer = None


def load_model_for_chat(model_path: str, base_model: str):
    """加载模型用于对话"""
    global _inferencer
    try:
        from inference import ModelInferencer

        # 卸载旧模型
        if _inferencer is not None:
            _inferencer.unload_model()

        # 加载新模型
        _inferencer = ModelInferencer(model_path, base_model)
        _inferencer.load_model()

        return f"✅ 模型加载成功！\n路径: {model_path}\n设备: {_inferencer.device}"

    except Exception as e:
        import traceback

        error_detail = traceback.format_exc()
        return f"❌ 模型加载失败: {str(e)}\n\n详细错误:\n{error_detail}"


def chat_with_model(message: str, history: list, ref_doc: str = None):
    """与模型对话"""
    global _inferencer

    if not message or not message.strip():
        return history, ""

    if _inferencer is None:
        # 如果模型未加载，返回提示
        history.append({"role": "user", "content": message})
        history.append(
            {
                "role": "assistant",
                "content": "⚠️ 模型未加载，请先点击'加载模型'按钮加载模型。",
            }
        )
        return history, ""

    try:
        # 调用推理器生成回复
        updated_history = _inferencer.chat(message, history)

        # 如果指定了参考文档，尝试查找引用
        if ref_doc and os.path.exists(ref_doc):
            # 获取最新回复
            last_response = updated_history[-1]["content"]

            # 查找页码
            page = find_citation(last_response, ref_doc)

            if page:
                doc_name = Path(ref_doc).name
                # 添加引用链接 (Gradio支持 file=路径 的链接)
                # 格式: [显示文本](/file=绝对路径#page=页码)
                citation = f"\n\n> 📚 **参考来源**: [{doc_name} 第 {page} 页](/file={ref_doc}#page={page})"
                updated_history[-1]["content"] += citation

        return updated_history, ""

    except Exception as e:
        import traceback

        error_detail = traceback.format_exc()
        history.append({"role": "user", "content": message})
        history.append(
            {
                "role": "assistant",
                "content": f"❌ 生成回复失败: {str(e)}\n\n{error_detail}",
            }
        )
        return history, ""
