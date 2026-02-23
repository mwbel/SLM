"""智谱AI API客户端"""

import json
from typing import List, Dict


def distill_with_zhipu(text: str, api_key: str, num_pairs: int = 10) -> List[Dict]:
    """
    使用智谱AI API进行知识蒸馏

    Args:
        text: 输入文本
        api_key: 智谱AI API密钥
        num_pairs: 生成的对话对数量（默认10组）

    Returns:
        对话对列表，格式: [{"instruction": "...", "input": "", "output": "..."}]

    Raises:
        Exception: API调用失败
    """
    try:
        from zhipuai import ZhipuAI
    except ImportError:
        raise ImportError("请安装智谱AI SDK: pip install zhipuai")

    # 初始化客户端
    client = ZhipuAI(api_key=api_key)

    # System Prompt - 领域专家角色
    system_prompt = f"""你是一位专业的领域知识专家和教学设计师。你的任务是从给定的文本中提取核心知识点，并生成高质量的问答对话对，用于训练小型语言模型。

要求：
1. 仔细阅读并理解输入文本的核心内容
2. 提取至少 {num_pairs} 组有价值的知识点
3. 为每个知识点生成一个自然的问题（instruction）和详细的回答（output）
4. 问题应该多样化，包括：概念解释、操作步骤、最佳实践、常见问题等
5. 回答应该准确、详细、专业，基于文本内容
6. input字段保持为空字符串

输出格式（严格的JSON数组）：
[
  {{
    "instruction": "问题内容",
    "input": "",
    "output": "详细的回答内容"
  }}
]

现在请处理以下文本：

{text}
"""

    try:
        # 调用智谱AI API (使用GLM-4-Flash模型)
        response = client.chat.completions.create(
            model="glm-4-flash",
            messages=[
                {"role": "user", "content": system_prompt}
            ],
            temperature=0.7,
            top_p=0.95,
            max_tokens=8192,
        )

        # 获取响应文本
        response_text = response.choices[0].message.content.strip()

        # 尝试提取JSON（可能被markdown代码块包裹）
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        response_text = response_text.strip()

        # 如果响应被截断，尝试修复
        if not response_text.endswith(']'):
            last_complete = response_text.rfind('},')
            if last_complete > 0:
                response_text = response_text[:last_complete+1] + '\n]'

        # 解析JSON
        result = json.loads(response_text)

        # 验证格式
        if not isinstance(result, list):
            raise ValueError("智谱AI返回的不是JSON数组格式")

        # 验证每个对话对的格式
        for item in result:
            if not all(key in item for key in ["instruction", "input", "output"]):
                raise ValueError("对话对缺少必需字段: instruction, input, output")

        return result

    except json.JSONDecodeError as e:
        raise Exception(f"解析智谱AI响应失败: {e}\n响应内容: {response_text}")
    except Exception as e:
        raise Exception(f"智谱AI API调用失败: {e}")
