"""训练器"""

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from transformers import Trainer as HFTrainer, TrainingArguments
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from datasets import Dataset
import platform
import os
from pathlib import Path


class Trainer:
    """QLoRA训练器"""

    def __init__(self, model_name: str, config: dict):
        self.model_name = model_name
        self.config = config

        # 尝试从本地路径加载模型
        # 1. 检查是否是相对路径（如 models/Qwen/...）
        local_path = Path(model_name)
        if local_path.exists():
            print(f"✅ 使用本地模型: {local_path.absolute()}")
            model_path = str(local_path.absolute())
        # 2. 检查ModelScope缓存
        elif (Path.home() / ".cache/modelscope" / model_name).exists():
            modelscope_path = Path.home() / ".cache/modelscope" / model_name
            print(f"✅ 从ModelScope缓存加载模型: {modelscope_path}")
            model_path = str(modelscope_path)
        else:
            print(f"⚠️  本地模型不存在，尝试从HuggingFace下载")
            model_path = model_name

        # 设置环境变量优先使用ModelScope
        os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

        # 自动检测设备（优先级：CUDA > MPS > CPU）
        device_info = self._detect_device()
        use_quantization = device_info["use_quantization"]

        print(f"🖥️  设备检测: {device_info['device_name']}")
        if device_info['device_type'] == 'cuda':
            print(f"   ✅ 使用CUDA GPU加速 (支持4-bit量化)")
        elif device_info['device_type'] == 'mps':
            print(f"   ✅ 使用Apple MPS加速 (Metal Performance Shaders)")
        else:
            print(f"   ⚠️  使用CPU模式 (训练速度较慢)")

        if use_quantization:
            # 4-bit量化配置（仅CUDA GPU）
            from transformers import BitsAndBytesConfig

            bnb_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_compute_dtype=torch.float16,
            )

            # 加载模型和tokenizer
            self.model = AutoModelForCausalLM.from_pretrained(
                model_path,
                quantization_config=bnb_config,
                device_map="auto",
                trust_remote_code=False,
                local_files_only=True,  # 强制使用本地文件
            )
        else:
            # 非量化模式（MPS或CPU）
            self.model = AutoModelForCausalLM.from_pretrained(
                model_path,
                torch_dtype=torch.float32,
                device_map=device_info["device_map"],
                trust_remote_code=False,
                local_files_only=True,  # 强制使用本地文件
            )

        self.tokenizer = AutoTokenizer.from_pretrained(
            model_path,
            trust_remote_code=False,
            local_files_only=True  # 强制使用本地文件
        )
        self.tokenizer.pad_token = self.tokenizer.eos_token

        # 准备模型用于训练
        if use_quantization:
            self.model = prepare_model_for_kbit_training(self.model)

        # LoRA配置
        lora_config = LoraConfig(
            r=config.get("lora", {}).get("rank", 8),
            lora_alpha=config.get("lora", {}).get("alpha", 16),
            lora_dropout=config.get("lora", {}).get("dropout", 0.05),
            target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
            task_type="CAUSAL_LM",
        )
        self.model = get_peft_model(self.model, lora_config)

        # 打印可训练参数
        self.model.print_trainable_parameters()

    def _detect_device(self):
        """
        自动检测可用设备
        优先级: CUDA GPU > Apple MPS > CPU

        Returns:
            dict: 包含设备信息的字典
                - device_type: 'cuda', 'mps', 或 'cpu'
                - device_name: 设备描述名称
                - device_map: 用于模型加载的device_map参数
                - use_quantization: 是否使用4-bit量化
        """
        # 优先检测CUDA GPU
        if torch.cuda.is_available():
            gpu_name = torch.cuda.get_device_name(0)
            return {
                "device_type": "cuda",
                "device_name": f"CUDA GPU ({gpu_name})",
                "device_map": "auto",
                "use_quantization": True
            }

        # 其次检测Apple MPS (macOS GPU加速)
        if torch.backends.mps.is_available() and platform.system() == "Darwin":
            return {
                "device_type": "mps",
                "device_name": "Apple MPS (Metal Performance Shaders)",
                "device_map": "auto",
                "use_quantization": False
            }

        # 最后回退到CPU
        return {
            "device_type": "cpu",
            "device_name": "CPU",
            "device_map": "cpu",
            "use_quantization": False
        }

    def train(self, train_data: list):
        """执行训练"""
        # 准备数据集
        dataset = Dataset.from_list(train_data)

        def tokenize_function(examples):
            # 格式化为对话格式
            instruction = examples.get("instruction", "")
            output = examples.get("output", "")
            text = f"问题：{instruction}\n回答：{output}"

            # 对文本进行tokenization
            tokenized = self.tokenizer(
                text,
                truncation=True,
                max_length=self.config.get("model", {}).get("max_seq_length", 512),
                padding="max_length",
                return_tensors=None,
            )

            # 创建labels：只训练"回答"部分，将"问题"部分设为-100
            labels = tokenized["input_ids"].copy()

            # 找到"回答："的位置
            prompt_length = len(self.tokenizer(f"问题：{instruction}\n回答：", add_special_tokens=False)["input_ids"])

            # 将问题部分的labels设为-100（PyTorch会忽略这些位置的loss）
            labels[:prompt_length] = [-100] * prompt_length

            tokenized["labels"] = labels

            return tokenized

        tokenized_dataset = dataset.map(tokenize_function, batched=False)

        # 训练参数
        training_args = TrainingArguments(
            output_dir=self.config.get("paths", {}).get("output_dir", "./outputs"),
            num_train_epochs=self.config.get("training", {}).get("num_epochs", 3),
            per_device_train_batch_size=self.config.get("training", {}).get(
                "batch_size", 1
            ),
            gradient_accumulation_steps=self.config.get("training", {}).get(
                "gradient_accumulation_steps", 4
            ),
            learning_rate=float(
                self.config.get("training", {}).get("learning_rate", 2e-4)
            ),
            warmup_steps=self.config.get("training", {}).get("warmup_steps", 10),
            logging_steps=1,
            save_strategy="epoch",
            save_total_limit=2,
            fp16=False,  # macOS不支持fp16
            report_to="none",
        )

        # 创建训练器
        trainer = HFTrainer(
            model=self.model, args=training_args, train_dataset=tokenized_dataset
        )

        # 执行训练
        trainer.train()

    def save_model(self, output_path: str):
        """保存模型"""
        os.makedirs(output_path, exist_ok=True)  # 确保目录存在
        self.model.save_pretrained(output_path)
        self.tokenizer.save_pretrained(output_path)
