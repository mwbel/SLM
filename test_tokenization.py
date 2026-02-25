#!/usr/bin/env python3
"""测试tokenization和labels设置是否正确"""

import sys
from pathlib import Path

# 添加src到路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test():
    try:
        from transformers import AutoTokenizer

        # 加载tokenizer
        model_path = "models/Qwen/Qwen2.5-0.5B"
        tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=False)
        tokenizer.pad_token = tokenizer.eos_token

        # 测试数据
        instruction = "同一家单位发票单张多少需要合同？"
        output = "同一家单位发票单张或累计金额3000元及以上的需要协议，10000元及以上的需要合同。"

        # 完整文本
        text = f"问题：{instruction}\n回答：{output}"

        print("=" * 70)
        print("测试 Tokenization 和 Labels")
        print("=" * 70)
        print(f"\n原始问题: {instruction}")
        print(f"原始回答: {output}")
        print(f"\n完整文本:\n{text}")

        # Tokenize完整文本
        tokenized = tokenizer(text, return_tensors=None)
        print(f"\n完整文本 token 长度: {len(tokenized['input_ids'])}")

        # 计算prompt长度
        prompt_text = f"问题：{instruction}\n回答："
        prompt_tokens = tokenizer(prompt_text, add_special_tokens=False)["input_ids"]
        prompt_length = len(prompt_tokens)

        print(f"\nPrompt文本: {repr(prompt_text)}")
        print(f"Prompt token 长度: {prompt_length}")
        print(f"Prompt tokens (前20个): {prompt_tokens[:20]}")

        # 查看完整tokens的结构
        full_tokens = tokenized['input_ids']
        print(f"\n完整 tokens (前30个): {full_tokens[:30]}")
        print(f"完整 tokens (prompt部分): {full_tokens[:prompt_length]}")
        print(f"完整 tokens (回答部分): {full_tokens[prompt_length:prompt_length+20]}")

        # 验证prompt部分是否匹配
        prompt_matches = full_tokens[:prompt_length] == prompt_tokens
        print(f"\n✓ Prompt部分匹配: {prompt_matches}")

        if not prompt_matches:
            print("\n⚠️  警告: Prompt tokens不匹配！")
            print(f"期望: {prompt_tokens[:20]}")
            print(f"实际: {full_tokens[:20]}")

        # 模拟labels设置
        labels = full_tokens.copy()
        labels[:prompt_length] = [-100] * prompt_length

        print(f"\nLabels (前30个): {labels[:30]}")
        print(f"Labels中-100的数量: {sum(1 for l in labels if l == -100)}")
        print(f"Labels中非-100的数量: {sum(1 for l in labels if l != -100)}")

        # 解码验证
        decoded_prompt = tokenizer.decode(full_tokens[:prompt_length], skip_special_tokens=False)
        decoded_answer = tokenizer.decode(full_tokens[prompt_length:], skip_special_tokens=False)

        print(f"\n解码的Prompt: {repr(decoded_prompt)}")
        print(f"解码的回答: {repr(decoded_answer[:100])}")

        return True

    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test()
