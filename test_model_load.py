#!/usr/bin/env python3
"""测试本地模型加载"""

import sys
from pathlib import Path

# 添加src到路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_model_loading():
    """测试模型加载"""
    print("=" * 70)
    print("测试本地模型加载")
    print("=" * 70)

    # 模型路径
    model_path = "models/Qwen/Qwen2___5-0___5B"

    print(f"\n模型路径: {model_path}")

    try:
        from transformers import AutoModelForCausalLM, AutoTokenizer
        import torch

        print("\n1. 加载 Tokenizer...")
        tokenizer = AutoTokenizer.from_pretrained(model_path)
        print("   ✓ Tokenizer 加载成功")

        print("\n2. 加载模型...")
        model = AutoModelForCausalLM.from_pretrained(
            model_path,
            torch_dtype="auto",
            device_map="auto"
        )
        print("   ✓ 模型加载成功")

        print(f"\n3. 模型信息:")
        print(f"   参数量: {model.num_parameters() / 1e6:.1f}M")
        print(f"   数据类型: {model.dtype}")
        print(f"   设备: {model.device}")

        print("\n4. 测试推理...")
        prompt = "你好，请介绍一下你自己。"
        inputs = tokenizer(prompt, return_tensors="pt")
        outputs = model.generate(
            **inputs,
            max_new_tokens=50,
            temperature=0.7
        )
        response = tokenizer.decode(outputs[0], skip_special_tokens=True)
        print(f"   输入: {prompt}")
        print(f"   输出: {response[:100]}...")

        print("\n" + "=" * 70)
        print("✅ 本地模型测试通过！")
        print("=" * 70)
        print("\n模型已准备好用于训练！")

        return True

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_model_loading()
    sys.exit(0 if success else 1)
