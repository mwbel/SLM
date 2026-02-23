"""
DataDistillerSkill - 数据蒸馏器

负责：
1. 将 Markdown 文本转化为高质量的 Question-Answer 对
2. 集成 Gemini 2.0 或 DeepSeek API
3. 支持断点续传（处理中断后可继续）
4. 自动追加保存到 JSONL 文件
"""

import asyncio
import json
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
from .base_skill import BaseSkill
from .api_manager import APIManagerSkill


class DataDistillerSkill(BaseSkill):
    """
    数据蒸馏 Skill

    将文档内容转化为高质量的 QA 对，用于训练小模型
    """

    # 财务报销制度专业 Prompt 模板
    SYSTEM_PROMPT = """你是一位资深的财务管理专家，专门负责企业财务报销制度的培训和咨询工作。你拥有超过15年的财务管理经验，精通各类企业的报销流程、财务合规要求和审计标准。

你的任务是根据提供的财务报销制度文档，生成高质量的问答对，用于培训企业员工和财务人员。

要求：
1. 问题必须具体、实用，涵盖员工在实际报销过程中可能遇到的场景
2. 答案必须准确、专业，严格基于文档内容，不得编造或推测
3. 答案要包含具体的金额、时限、流程步骤等关键信息
4. 如果文档中没有明确说明，答案中要诚实地指出"文档未明确规定"
5. 使用清晰、易懂的语言，避免过于复杂的财务术语
6. 每个问答对要独立完整，不依赖上下文

生成的问答对将用于训练AI助手，帮助员工快速了解报销制度。"""

    USER_PROMPT_TEMPLATE = """请根据以下财务报销制度文档内容，生成 {num_qa} 个高质量的问答对。

文档内容：
```
{content}
```

要求：
1. 问题类型要多样化：包括"如何办理"、"需要什么材料"、"金额限制"、"审批流程"、"时间要求"等
2. 覆盖文档中的关键信息点
3. 问题要自然，像真实员工会问的那样
4. 答案要准确、完整，包含所有必要的细节

请以 JSON 格式返回，格式如下：
```json
[
    {{
        "question": "具体的问题",
        "answer": "详细的答案"
    }},
    ...
]
```

只返回 JSON 数组，不要包含其他内容。"""

    def __init__(self,
                 api_manager: Optional[APIManagerSkill] = None,
                 api_provider: str = 'gemini',
                 api_config_file: Optional[str] = None,
                 output_file: str = 'data/output/dataset.jsonl',
                 checkpoint_dir: str = '.checkpoints',
                 chunk_size: int = 2000,
                 qa_per_chunk: int = 5,
                 max_retries: int = 3):
        """
        初始化 DataDistillerSkill

        Args:
            api_manager: APIManagerSkill 实例（如果为 None，自动创建）
            api_provider: API 提供商 ('gemini', 'deepseek', 'openai')
            api_config_file: API 配置文件路径（可选）
            output_file: 输出 JSONL 文件路径
            checkpoint_dir: 断点文件保存目录
            chunk_size: 文本切片大小（字符数）
            qa_per_chunk: 每个切片生成的 QA 对数量
            max_retries: API 调用失败时的最大重试次数
        """
        super().__init__(name="DataDistiller")

        self.api_provider = api_provider.lower()
        self.chunk_size = chunk_size
        self.qa_per_chunk = qa_per_chunk
        self.max_retries = max_retries

        # 设置输出文件
        self.output_file = Path(output_file)
        self.output_file.parent.mkdir(parents=True, exist_ok=True)

        # 设置断点目录
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

        # 初始化或使用提供的 API 管理器
        if api_manager:
            self.api_manager = api_manager
            self.logger.info("✅ 使用提供的 API 管理器")
        else:
            self.api_manager = APIManagerSkill(
                config_file=api_config_file,
                auto_rotate=True,
                failure_threshold=3,
                cooldown_minutes=5
            )
            self.logger.info("✅ 创建新的 API 管理器")

        # 当前使用的 API 配置
        self.current_api = None
        self.current_client = None

    def _get_api_client(self):
        """
        获取 API 客户端（通过 API 管理器）

        Returns:
            (client, api_config) 元组
        """
        # 从 API 管理器获取可用 API
        api_config = self.api_manager.get_available_api(self.api_provider)

        if not api_config:
            raise RuntimeError(f"没有可用的 {self.api_provider} API")

        # 如果 API 配置改变，重新初始化客户端
        if not self.current_api or self.current_api['api_id'] != api_config['api_id']:
            self.current_api = api_config
            self.current_client = self._init_client(api_config)
            self.logger.info(f"🔄 切换到 API: {api_config.get('name', api_config['api_id'])}")

        return self.current_client, self.current_api

    def _init_client(self, api_config: Dict[str, Any]):
        """
        初始化 API 客户端

        Args:
            api_config: API 配置字典

        Returns:
            初始化的客户端
        """
        api_key = api_config['api_key']
        model_name = api_config['model']

        if self.api_provider == 'gemini':
            try:
                import google.generativeai as genai
                genai.configure(api_key=api_key)
                client = genai.GenerativeModel(model_name)
                self.logger.info(f"✅ Gemini 客户端初始化成功，模型: {model_name}")
                return client
            except ImportError:
                raise ImportError(
                    "需要安装 google-generativeai 库\n"
                    "安装方法: pip install google-generativeai"
                )

        elif self.api_provider == 'deepseek':
            try:
                from openai import OpenAI
                client = OpenAI(
                    api_key=api_key,
                    base_url="https://api.deepseek.com"
                )
                self.logger.info(f"✅ DeepSeek 客户端初始化成功，模型: {model_name}")
                return client
            except ImportError:
                raise ImportError(
                    "需要安装 openai 库\n"
                    "安装方法: pip install openai"
                )

        elif self.api_provider == 'openai':
            try:
                from openai import OpenAI
                client = OpenAI(api_key=api_key)
                self.logger.info(f"✅ OpenAI 客户端初始化成功，模型: {model_name}")
                return client
            except ImportError:
                raise ImportError(
                    "需要安装 openai 库\n"
                    "安装方法: pip install openai"
                )
        else:
            raise ValueError(f"不支持的 API 提供商: {self.api_provider}")

    async def execute(self, input_data: Any, **kwargs) -> Dict[str, Any]:
        """
        执行数据蒸馏

        Args:
            input_data: 输入数据，可以是：
                - str: Markdown 文本内容
                - dict: 包含 'content' 字段的字典（parser_pdf_ocr 的输出）
            **kwargs: 额外参数
                - resume: bool, 是否从断点恢复（默认 True）
                - source_file: str, 源文件名（用于断点标识）

        Returns:
            {
                'total_qa_pairs': int,      # 生成的 QA 对总数
                'output_file': str,          # 输出文件路径
                'chunks_processed': int,     # 处理的文本块数
                'api_calls': int,            # API 调用次数
                'failed_chunks': int         # 失败的文本块数
            }
        """
        # 解析输入数据
        if isinstance(input_data, dict):
            content = input_data.get('content', '')
            source_file = input_data.get('file_path', 'unknown')
        else:
            content = str(input_data)
            source_file = kwargs.get('source_file', 'unknown')

        if not content:
            raise ValueError("输入内容为空")

        resume = kwargs.get('resume', True)

        self.logger.info(f"📝 开始数据蒸馏")
        self.logger.info(f"   内容长度: {len(content)} 字符")
        self.logger.info(f"   切片大小: {self.chunk_size} 字符")
        self.logger.info(f"   每片生成: {self.qa_per_chunk} 个 QA 对")

        # 切分文本
        chunks = self._split_content(content)
        self.logger.info(f"   切分为 {len(chunks)} 个文本块")

        # 检查断点
        checkpoint_file = self.checkpoint_dir / f"{Path(source_file).stem}_distill_checkpoint.json"
        start_chunk = 0

        if resume and checkpoint_file.exists():
            checkpoint = self._load_checkpoint(checkpoint_file)
            start_chunk = checkpoint.get('last_processed_chunk', 0) + 1
            self.logger.info(f"🔄 从断点恢复，起始块: {start_chunk + 1}/{len(chunks)}")

        # 处理每个文本块
        total_qa_pairs = 0
        api_calls = 0
        failed_chunks = 0

        for i in range(start_chunk, len(chunks)):
            chunk = chunks[i]
            self.logger.info(f"\n🔄 处理文本块 {i + 1}/{len(chunks)}")

            try:
                # 调用 API 生成 QA 对
                qa_pairs = await self._generate_qa_pairs(chunk, self.qa_per_chunk)
                api_calls += 1

                if qa_pairs:
                    # 保存到 JSONL 文件
                    self._append_to_jsonl(qa_pairs)
                    total_qa_pairs += len(qa_pairs)
                    self.logger.info(f"   ✅ 生成 {len(qa_pairs)} 个 QA 对")
                else:
                    failed_chunks += 1
                    self.logger.warning(f"   ⚠️  未生成 QA 对")

                # 保存断点
                self._save_checkpoint(checkpoint_file, {
                    'source_file': source_file,
                    'total_chunks': len(chunks),
                    'last_processed_chunk': i,
                    'total_qa_pairs': total_qa_pairs,
                    'timestamp': datetime.now().isoformat()
                })

            except Exception as e:
                failed_chunks += 1
                self.logger.error(f"   ❌ 处理失败: {e}")

                # 保存断点（失败时也保存）
                self._save_checkpoint(checkpoint_file, {
                    'source_file': source_file,
                    'total_chunks': len(chunks),
                    'last_processed_chunk': i - 1,  # 回退到上一个成功的块
                    'total_qa_pairs': total_qa_pairs,
                    'last_error': str(e),
                    'timestamp': datetime.now().isoformat()
                })

                # 如果失败次数过多，抛出异常
                if failed_chunks > len(chunks) * 0.3:  # 超过 30% 失败
                    raise RuntimeError(f"失败率过高: {failed_chunks}/{i + 1}")

        # 清理断点文件（全部完成）
        if checkpoint_file.exists():
            checkpoint_file.unlink()
            self.logger.info("✅ 处理完成，已清理断点文件")

        return {
            'total_qa_pairs': total_qa_pairs,
            'output_file': str(self.output_file),
            'chunks_processed': len(chunks) - start_chunk,
            'api_calls': api_calls,
            'failed_chunks': failed_chunks
        }

    def _split_content(self, content: str) -> List[str]:
        """
        切分文本内容

        Args:
            content: 文本内容

        Returns:
            文本块列表
        """
        chunks = []
        lines = content.split('\n')
        current_chunk = []
        current_size = 0

        for line in lines:
            line_size = len(line)

            # 如果当前块加上这一行会超过限制，保存当前块
            if current_size + line_size > self.chunk_size and current_chunk:
                chunks.append('\n'.join(current_chunk))
                current_chunk = []
                current_size = 0

            current_chunk.append(line)
            current_size += line_size + 1  # +1 for newline

        # 添加最后一个块
        if current_chunk:
            chunks.append('\n'.join(current_chunk))

        return chunks

    async def _generate_qa_pairs(self, content: str, num_qa: int) -> List[Dict[str, str]]:
        """
        调用 API 生成 QA 对

        Args:
            content: 文本内容
            num_qa: 要生成的 QA 对数量

        Returns:
            QA 对列表
        """
        prompt = self.USER_PROMPT_TEMPLATE.format(
            content=content,
            num_qa=num_qa
        )

        for attempt in range(self.max_retries):
            try:
                # 获取 API 客户端
                client, api_config = self._get_api_client()
                api_id = api_config['api_id']

                # 调用 API
                if self.api_provider == 'gemini':
                    response = await self._call_gemini(client, prompt)
                elif self.api_provider == 'deepseek':
                    response = await self._call_deepseek(client, api_config['model'], prompt)
                elif self.api_provider == 'openai':
                    response = await self._call_openai(client, api_config['model'], prompt)
                else:
                    raise ValueError(f"不支持的 API 提供商: {self.api_provider}")

                # 解析 JSON 响应
                qa_pairs = self._parse_response(response)

                # 报告成功
                self.api_manager.report_success(api_id)

                return qa_pairs

            except Exception as e:
                # 报告失败
                if self.current_api:
                    self.api_manager.report_failure(self.current_api['api_id'], str(e))

                self.logger.warning(f"   API 调用失败 (尝试 {attempt + 1}/{self.max_retries}): {e}")

                if attempt < self.max_retries - 1:
                    # 重试前等待（指数退避）
                    await asyncio.sleep(2 ** attempt)
                    # 清除当前 API，下次重试时会获取新的
                    self.current_api = None
                    self.current_client = None
                else:
                    raise

        return []

    async def _call_gemini(self, client, prompt: str) -> str:
        """调用 Gemini API"""
        response = client.generate_content(
            [self.SYSTEM_PROMPT, prompt],
            generation_config={
                'temperature': 0.7,
                'top_p': 0.95,
                'max_output_tokens': 8192,
            }
        )
        return response.text

    async def _call_deepseek(self, client, model: str, prompt: str) -> str:
        """调用 DeepSeek API"""
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": self.SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=8192
        )
        return response.choices[0].message.content

    async def _call_openai(self, client, model: str, prompt: str) -> str:
        """调用 OpenAI API"""
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": self.SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=8192
        )
        return response.choices[0].message.content

    def _parse_response(self, response: str) -> List[Dict[str, str]]:
        """
        解析 API 响应，提取 QA 对

        Args:
            response: API 响应文本

        Returns:
            QA 对列表
        """
        # 尝试提取 JSON
        import re

        # 查找 JSON 数组
        json_match = re.search(r'\[[\s\S]*\]', response)
        if json_match:
            json_str = json_match.group(0)
            try:
                qa_pairs = json.loads(json_str)

                # 验证格式
                if isinstance(qa_pairs, list):
                    valid_pairs = []
                    for pair in qa_pairs:
                        if isinstance(pair, dict) and 'question' in pair and 'answer' in pair:
                            valid_pairs.append({
                                'question': pair['question'].strip(),
                                'answer': pair['answer'].strip()
                            })
                    return valid_pairs
            except json.JSONDecodeError as e:
                self.logger.error(f"JSON 解析失败: {e}")

        return []

    def _append_to_jsonl(self, qa_pairs: List[Dict[str, str]]):
        """
        追加 QA 对到 JSONL 文件

        Args:
            qa_pairs: QA 对列表
        """
        with open(self.output_file, 'a', encoding='utf-8') as f:
            for pair in qa_pairs:
                json_line = json.dumps(pair, ensure_ascii=False)
                f.write(json_line + '\n')

    def _save_checkpoint(self, checkpoint_file: Path, data: dict):
        """保存断点信息"""
        with open(checkpoint_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        self.logger.debug(f"💾 已保存断点: {checkpoint_file}")

    def _load_checkpoint(self, checkpoint_file: Path) -> dict:
        """加载断点信息"""
        with open(checkpoint_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        self.logger.debug(f"📂 已加载断点: {checkpoint_file}")
        return data


# 使用示例
if __name__ == "__main__":
    import asyncio

    async def test_distiller():
        """测试数据蒸馏功能"""
        # 创建蒸馏器（使用 Gemini）
        distiller = DataDistillerSkill(
            api_provider='gemini',
            output_file='data/output/dataset.jsonl',
            chunk_size=2000,
            qa_per_chunk=5
        )

        # 测试文本
        test_content = """
# 财务报销制度

## 差旅费报销

1. 出差申请：员工出差前需填写《出差申请单》，经部门经理审批后方可出差。
2. 报销标准：
   - 交通费：实报实销，需提供发票
   - 住宿费：一线城市不超过500元/天，二线城市不超过300元/天
   - 餐费：100元/天
3. 报销时限：出差结束后15个工作日内完成报销
4. 所需材料：出差申请单、发票原件、行程单

## 办公用品报销

1. 采购流程：由行政部统一采购
2. 报销标准：每人每月不超过200元
3. 审批流程：部门经理审批 → 财务审核 → 总经理批准
        """

        print(f"\n{'='*60}")
        print("测试数据蒸馏")
        print('='*60)

        result = await distiller.run(test_content, source_file='test_policy.md')

        if result['success']:
            data = result['data']
            print(f"✅ 蒸馏成功:")
            print(f"   生成 QA 对: {data['total_qa_pairs']} 个")
            print(f"   输出文件: {data['output_file']}")
            print(f"   处理块数: {data['chunks_processed']}")
            print(f"   API 调用: {data['api_calls']} 次")
        else:
            print(f"❌ 蒸馏失败: {result['error']}")

    # 运行测试
    asyncio.run(test_distiller())
