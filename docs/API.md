# API 文档

## 配置加载器 (ConfigLoader)

### 初始化
```python
from src.utils import ConfigLoader

config = ConfigLoader("config.yaml")
```

### 方法

#### get(key, default=None)
获取配置项，支持嵌套键访问

```python
base_model = config.get("model.base_model")
batch_size = config.get("training.batch_size", 4)
```

#### set(key, value)
设置配置项

```python
config.set("training.batch_size", 8)
config.set("model.base_model", "Qwen/Qwen2.5-1.5B")
```

#### save(output_path=None)
保存配置到文件

```python
config.save()  # 保存到原文件
config.save("config_new.yaml")  # 保存到新文件
```

## 训练器 (Trainer)

### 初始化
```python
from src.training import Trainer

trainer = Trainer(
    model_name="Qwen/Qwen2.5-0.5B",
    config=config.config
)
```

### 方法

#### train(train_data)
执行训练

```python
train_data = [
    {
        "instruction": "问题",
        "input": "",
        "output": "答案"
    }
]
trainer.train(train_data)
```

#### save_model(output_path)
保存模型

```python
trainer.save_model("./models/my_model")
```

## 推理引擎 (InferenceEngine)

### 初始化
```python
from src.inference import InferenceEngine

engine = InferenceEngine(model_path="./models/my_model")
engine.load_model()
```

### 方法

#### generate(prompt, max_length=512)
生成回复

```python
response = engine.generate("你好", max_length=256)
print(response)
```

## 模型导出器 (ModelExporter)

### 初始化
```python
from src.export import ModelExporter

exporter = ModelExporter(model_path="./models/my_model")
```

### 方法

#### merge_lora_weights(output_path)
合并LoRA权重

```python
exporter.merge_lora_weights("./models/merged_model")
```

#### export_to_gguf(output_path, quantization="Q4_K_M")
导出为GGUF格式

```python
exporter.export_to_gguf("./models/model.gguf", quantization="Q4_K_M")
```

#### export_to_ollama(model_name)
导出到Ollama

```python
exporter.export_to_ollama("my-slm")
```

## 模型管理器 (ModelManager)

### 初始化
```python
from src.management import ModelManager

manager = ModelManager(models_dir="./models")
```

### 方法

#### list_models()
列出所有模型

```python
models = manager.list_models()
for model in models:
    print(f"{model['name']} - {model['description']}")
```

#### register_model(model_path, name, description="", base_model="", training_config=None)
注册新模型

```python
model_id = manager.register_model(
    model_path="./outputs/checkpoint-100",
    name="客服助手v1",
    description="客服领域微调模型",
    base_model="Qwen2.5-0.5B"
)
```

#### delete_model(model_id, delete_files=True)
删除模型

```python
manager.delete_model(model_id, delete_files=True)
```

## 日志工具

### 基础日志
```python
from src.utils import setup_logger

logger = setup_logger(
    name="my_app",
    log_file="./outputs/logs/app.log",
    level=logging.INFO
)

logger.info("开始训练")
logger.error("训练失败")
```

### 训练日志
```python
from src.utils.logger import TrainingLogger

train_logger = TrainingLogger(log_dir="./outputs/logs")
train_logger.log_epoch(epoch=1, loss=0.5, metrics={"accuracy": 0.95})
train_logger.save_metrics()
```
