#!/usr/bin/env python3
"""
简单的智谱AI推理器 - 不需要本地模型
使用智谱AI API进行推理，无需下载大型模型文件
"""

import os
import json
from pathlib import Path
from typing import List, Dict, Optional

try:
    import zhipuai
    ZHIPUAI_AVAILABLE = True
except ImportError:
    ZHIPUAI_AVAILABLE = False

class SimpleInference:
    """简单的推理器 - 使用智谱AI"""

    def __init__(self, api_key: str = None):
        """
        初始化推理器

        Args:
            api_key: 智谱AI API密钥
        """
        if not ZHIPUAI_AVAILABLE:
            raise ImportError(
                "请安装 zhipuai 包: pip3 install zhipuai"
            )

        # 从参数或环境变量获取 API key
        self.api_key = api_key or os.environ.get('ZHIPU_API_KEY')
        if not self.api_key:
            raise ValueError(
                "请提供智谱AI API密钥: \n"
                "1. 设置环境变量: export ZHIPU_API_KEY='your-key'\n"
                "2. 或在 .env 文件中添加: ZHIPU_API_KEY=your-key"
            )

        # 初始化客户端
        zhipuai.api_key = self.api_key

    def generate(self, prompt: str, temperature: float = 0.7, max_tokens: int = 2000) -> str:
        """
        生成文本

        Args:
            prompt: 输入提示
            temperature: 温度参数 (0-1)
            max_tokens: 最大生成token数

        Returns:
            生成的文本
        """
        try:
            response = zhipuai.model_api.invoke(
                model="glm-4-flash",
                prompt=prompt,
                temperature=temperature,
                max_tokens=max_tokens
            )

            if response['code'] == 200:
                return response['data']['choices'][0]['content']
            else:
                raise Exception(f"API错误: {response}")

        except Exception as e:
            raise Exception(f"智谱AI调用失败: {e}")

    def chat(self, messages: List[Dict[str, str]], temperature: float = 0.7) -> str:
        """
        对话生成

        Args:
            messages: 对话历史 [{"role": "user", "content": "..."}]
            temperature: 温度参数

        Returns:
            生成的回复
        """
        try:
            response = zhipuai.model_api.invoke(
                model="glm-4-flash",
                messages=messages,
                temperature=temperature
            )

            if response['code'] == 200:
                return response['data']['choices'][0]['content']
            else:
                raise Exception(f"API错误: {response}")

        except Exception as e:
            raise Exception(f"智谱AI调用失败: {e}")

    def generate_training_data(self, text: str, num_pairs: int = 10) -> List[Dict]:
        """
        从文本生成训练数据

        Args:
            text: 输入文本
            num_pairs: 生成的对话对数量

        Returns:
            训练数据列表
        """
        prompt = f"""你是一位专业的教学设计师。请从以下文本中提取 {num_pairs} 组有价值的知识点，并生成问答对话对。

文本内容：
{text}

要求：
1. 提取至少 {num_pairs} 组知识点
2. 为每个知识点生成一个自然的问题和详细的回答
3. 问题应该多样化（概念解释、操作步骤、最佳实践等）
4. 回答应该准确、详细、专业

输出格式（JSON数组）：
[
  {{"instruction": "问题内容", "input": "", "output": "详细的回答内容"}},
  ...
]

现在请生成："""

        response = self.generate(prompt, temperature=0.7, max_tokens=4000)

        # 解析JSON
        try:
            data = json.loads(response)
            if isinstance(data, list):
                return data
            else:
                raise ValueError("响应不是JSON数组")
        except json.JSONDecodeError:
            # 尝试提取JSON部分
            start = response.find('[')
            end = response.rfind(']') + 1
            if start != -1 and end > start:
                json_str = response[start:end]
                return json.loads(json_str)
            else:
                raise ValueError("无法解析JSON响应")

    def answer_question(self, question: str, context: str = "") -> str:
        """
        回答问题

        Args:
            question: 问题
            context: 背景文本（可选）

        Returns:
            回答
        """
        if context:
            prompt = f"""基于以下背景信息回答问题：

背景信息：
{context}

问题：{question}

请提供详细、准确的回答："""
        else:
            prompt = f"问题：{question}\n\n请提供详细、准确的回答："

        return self.generate(prompt, temperature=0.7)


# 使用示例
if __name__ == "__main__":
    # 示例1: 基本使用
    print("=" * 70)
    print("智谱AI简单推理器示例")
    print("=" * 70)

    # 检查API密钥
    api_key = os.environ.get('ZHIPU_API_KEY')
    if not api_key:
        print("\n⚠️ 请先设置智谱AI API密钥：")
        print("   export ZHIPU_API_KEY='your-key-here'")
        print("\n或编辑 .env 文件添加：")
        print("   ZHIPU_API_KEY=your-key-here")
        exit(1)

    # 创建推理器
    inferencer = SimpleInference(api_key=api_key)

    # 示例2: 生成文本
    print("\n1. 生成文本示例：")
    prompt = "请简单解释什么是机器学习"
    response = inferencer.generate(prompt)
    print(f"   问题: {prompt}")
    print(f"   回答: {response[:200]}...")

    # 示例3: 生成训练数据
    print("\n2. 生成训练数据示例：")
    text = """
    Python是一种高级编程语言，由Guido van Rossum于1991年创建。
    它具有简洁的语法和强大的功能，被广泛应用于Web开发、数据分析、人工智能等领域。
    Python的设计哲学强调代码的可读性和简洁的语法。
    """
    try:
        training_data = inferencer.generate_training_data(text, num_pairs=3)
        print(f"   生成了 {len(training_data)} 组训练数据")
        for i, item in enumerate(training_data, 1):
            print(f"   {i}. {item['instruction'][:50]}...")
    except Exception as e:
        print(f"   生成失败: {e}")

    print("\n" + "=" * 70)
    print("✅ 测试完成！")
    print("=" * 70)
