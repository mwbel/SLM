"""训练器"""

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from transformers import Trainer as HFTrainer, TrainingArguments
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from datasets import Dataset

class Trainer:
    """QLoRA训练器"""

    def __init__(self, model_name: str, config: dict):
        self.model_name = model_name
        self.config = config

        # 4-bit量化配置
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.float16
        )

        # 加载模型和tokenizer
        self.model = AutoModelForCausalLM.from_pretrained(
            model_name,
            quantization_config=bnb_config,
            device_map="auto"
        )
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.tokenizer.pad_token = self.tokenizer.eos_token

        # 准备模型用于训练
        self.model = prepare_model_for_kbit_training(self.model)

        # LoRA配置
        lora_config = LoraConfig(
            r=config.get('lora', {}).get('rank', 8),
            lora_alpha=config.get('lora', {}).get('alpha', 16),
            lora_dropout=config.get('lora', {}).get('dropout', 0.05),
            target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
            task_type="CAUSAL_LM"
        )
        self.model = get_peft_model(self.model, lora_config)

    def train(self, train_data: list):
        """执行训练"""
        # 准备数据集
        dataset = Dataset.from_list(train_data)

        def tokenize_function(examples):
            texts = [f"{ex.get('instruction', '')}\n{ex.get('input', '')}\n{ex.get('output', '')}"
                    for ex in [examples]]
            return self.tokenizer(texts[0], truncation=True, max_length=512)

        tokenized_dataset = dataset.map(tokenize_function, batched=False)

        # 训练参数
        training_args = TrainingArguments(
            output_dir=self.config.get('paths', {}).get('output_dir', './outputs'),
            num_train_epochs=self.config.get('training', {}).get('num_epochs', 3),
            per_device_train_batch_size=self.config.get('training', {}).get('batch_size', 4),
            learning_rate=self.config.get('training', {}).get('learning_rate', 2e-4),
            warmup_steps=self.config.get('training', {}).get('warmup_steps', 10),
            logging_steps=10,
            save_strategy="epoch"
        )

        # 创建训练器
        trainer = HFTrainer(
            model=self.model,
            args=training_args,
            train_dataset=tokenized_dataset
        )

        # 执行训练
        trainer.train()

    def save_model(self, output_path: str):
        """保存模型"""
        self.model.save_pretrained(output_path)
        self.tokenizer.save_pretrained(output_path)
