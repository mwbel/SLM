"""模型推理模块"""

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel
from pathlib import Path
import platform


class ModelInferencer:
    """模型推理器 - 用于加载和推理训练好的模型"""

    def __init__(self, model_path: str, base_model: str = "models/Qwen/Qwen2.5-1.5B"):
        """
        初始化推理器

        Args:
            model_path: 训练好的模型路径（LoRA权重）
            base_model: 基座模型名称
        """
        self.model_path = Path(model_path)
        self.base_model = base_model
        self.model = None
        self.tokenizer = None
        self.device = self._get_device()

    def _get_device(self):
        """
        自动检测可用设备
        优先级: CUDA GPU > Apple MPS > CPU

        Returns:
            str: 设备类型 ('cuda', 'mps', 或 'cpu')
        """
        # 优先检测CUDA GPU
        if torch.cuda.is_available():
            return "cuda"
        # 其次检测Apple MPS (macOS GPU加速)
        elif torch.backends.mps.is_available() and platform.system() == "Darwin":
            return "mps"
        # 最后回退到CPU
        else:
            return "cpu"

    def load_model(self):
        """加载模型"""
        print(f"正在加载模型...")

        # 显示设备信息
        if self.device == "cuda":
            gpu_name = torch.cuda.get_device_name(0)
            print(f"🖥️  设备: CUDA GPU ({gpu_name})")
        elif self.device == "mps":
            print(f"🖥️  设备: Apple MPS (Metal Performance Shaders)")
        else:
            print(f"🖥️  设备: CPU")

        # 检查模型路径
        if not self.model_path.exists():
            raise FileNotFoundError(f"模型路径不存在: {self.model_path}")

        # 禁用tqdm进度条以避免在Gradio上下文中出现BrokenPipeError
        import os
        disable_tqdm = os.environ.get('DISABLE_TQDM', '1')  # 默认禁用

        from transformers import utils
        utils.logging.set_verbosity_error()  # 禁用详细日志
        os.environ['TRANSFORMERS_NO_PROGRESS_BAR'] = '1'  # 禁用进度条

        # 智能检测基座模型路径
        # 1. 首先检查是否是本地路径
        local_path = Path(self.base_model)
        if local_path.exists():
            print(f"使用本地基座模型: {local_path.absolute()}")
            base_model_path = str(local_path.absolute())
        # 2. 检查ModelScope缓存
        elif (Path.home() / ".cache/modelscope" / self.base_model).exists():
            modelscope_path = Path.home() / ".cache/modelscope" / self.base_model
            print(f"从ModelScope缓存加载基座模型: {modelscope_path}")
            base_model_path = str(modelscope_path)
        else:
            print(f"⚠️  本地模型不存在，尝试从HuggingFace下载: {self.base_model}")
            base_model_path = self.base_model

        # 加载tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(
            base_model_path,
            trust_remote_code=False,
            local_files_only=True  # 强制使用本地文件
        )
        self.tokenizer.pad_token = self.tokenizer.eos_token

        # 加载基座模型
        print("加载基座模型...")
        base_model = AutoModelForCausalLM.from_pretrained(
            base_model_path,
            torch_dtype=torch.float32 if self.device == "cpu" else torch.float16,
            device_map="auto" if self.device != "cpu" else None,
            trust_remote_code=False,
            local_files_only=True,  # 强制使用本地文件
        )

        # 加载LoRA权重
        print(f"加载LoRA权重: {self.model_path}")
        self.model = PeftModel.from_pretrained(base_model, str(self.model_path))

        # 合并权重以提高推理速度
        print("合并LoRA权重...")
        self.model = self.model.merge_and_unload()

        # 移动到设备
        if self.device == "cpu":
            self.model = self.model.to("cpu")

        self.model.eval()
        print("✅ 模型加载完成！")

    def generate(
        self,
        prompt: str,
        max_new_tokens: int = 256,
        temperature: float = 0.7,
        top_p: float = 0.9,
        top_k: int = 50,
        repetition_penalty: float = 1.2,
        add_prompt_format: bool = True
    ) -> str:
        """
        生成回复

        Args:
            prompt: 输入提示
            max_new_tokens: 最大生成token数
            temperature: 温度参数
            top_p: nucleus sampling参数
            top_k: top-k sampling参数
            repetition_penalty: 重复惩罚系数
            add_prompt_format: 是否自动添加"问题：回答："格式（默认True）

        Returns:
            生成的文本
        """
        if self.model is None or self.tokenizer is None:
            raise RuntimeError("模型未加载，请先调用load_model()")

        # 格式化输入（如果需要）
        if add_prompt_format:
            formatted_prompt = f"问题：{prompt}\n回答："
        else:
            formatted_prompt = prompt

        # Tokenize
        inputs = self.tokenizer(
            formatted_prompt,
            return_tensors="pt",
            truncation=True,
            max_length=512
        )

        # 移动到设备
        if self.device != "cpu":
            inputs = {k: v.to(self.device) for k, v in inputs.items()}

        # 生成
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                temperature=temperature,
                top_p=top_p,
                top_k=top_k,
                repetition_penalty=repetition_penalty,
                do_sample=True,
                pad_token_id=self.tokenizer.eos_token_id,
                eos_token_id=self.tokenizer.eos_token_id,
                no_repeat_ngram_size=3,  # 防止3-gram重复
            )

        # 获取输入长度
        input_length = inputs["input_ids"].shape[1]

        # 解码 (只解码新生成的token)
        new_tokens = outputs[0][input_length:]
        generated_text = self.tokenizer.decode(new_tokens, skip_special_tokens=True)

        # 防止模型生成下一个问题
        if "问题：" in generated_text:
            generated_text = generated_text.split("问题：")[0]

        return generated_text.strip()

    def chat(self, message: str, history: list = None) -> tuple:
        """
        对话接口（兼容Gradio）

        注意：对于财务报销规则等独立问题，不使用多轮对话上下文
        这样可以避免上下文截断问题，并保持与评估脚本一致的行为

        Args:
            message: 用户消息
            history: 对话历史（保留用于UI显示，但不用于推理）

        Returns:
            更新后的历史
        """
        if history is None:
            history = []

        # 直接使用当前问题生成回复（不使用历史上下文）
        # 使用与评估脚本相同的参数
        response = self.generate(
            message,
            max_new_tokens=300,  # 与评估脚本一致
            temperature=0.1,     # 与评估脚本一致
            top_p=0.95,          # 与评估脚本一致
            repetition_penalty=1.0,  # 与评估脚本一致
            add_prompt_format=True  # 使用"问题：回答："格式
        )

        # 更新历史
        history.append({"role": "user", "content": message})
        history.append({"role": "assistant", "content": response})

        return history

    def unload_model(self):
        """卸载模型释放内存"""
        if self.model is not None:
            del self.model
            self.model = None
        if self.tokenizer is not None:
            del self.tokenizer
            self.tokenizer = None

        # 清理GPU内存
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

        print("模型已卸载")
