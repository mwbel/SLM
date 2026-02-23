"""
SmartChunkerSkill - 智能文本切分器

负责将长文本进行逻辑切分：
1. 支持自定义 chunk_size 和 overlap
2. 智能识别段落、句子边界，避免语义截断
3. 保留文档结构信息（如标题层级）
4. 支持多种切分策略（按字符、按句子、按段落）
"""

import asyncio
import re
from typing import Dict, Any, List, Optional
from .base_skill import BaseSkill


class SmartChunkerSkill(BaseSkill):
    """
    智能文本切分 Skill

    将长文本切分为合适大小的块，同时保持语义完整性
    """

    def __init__(self,
                 chunk_size: int = 1000,
                 overlap: int = 200,
                 strategy: str = 'smart',
                 respect_structure: bool = True):
        """
        初始化 SmartChunkerSkill

        Args:
            chunk_size: 每个块的目标字符数（默认 1000）
            overlap: 块之间的重叠字符数（默认 200）
            strategy: 切分策略
                - 'smart': 智能切分（优先在段落/句子边界切分）
                - 'sentence': 按句子切分
                - 'paragraph': 按段落切分
                - 'fixed': 固定长度切分
            respect_structure: 是否尊重文档结构（如标题层级）
        """
        super().__init__(name="SmartChunker")
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.strategy = strategy
        self.respect_structure = respect_structure

        # 验证策略
        valid_strategies = ['smart', 'sentence', 'paragraph', 'fixed']
        if self.strategy not in valid_strategies:
            raise ValueError(
                f"不支持的切分策略: {strategy}\n"
                f"支持的策略: {', '.join(valid_strategies)}"
            )

    async def execute(self, input_data: Any, **kwargs) -> Dict[str, Any]:
        """
        执行文本切分

        Args:
            input_data: 解析结果字典（包含 content 和 structure）
            **kwargs: 额外参数
                - chunk_size: 覆盖默认的块大小
                - overlap: 覆盖默认的重叠大小

        Returns:
            {
                'file_path': str,
                'chunks': List[Dict],     # 切分后的块列表
                'chunk_count': int,       # 块的数量
                'metadata': dict          # 切分元数据
            }

        Raises:
            ValueError: 输入数据格式错误
        """
        # 验证输入
        if not isinstance(input_data, dict):
            raise ValueError("输入必须是解析结果字典")

        if 'content' not in input_data:
            raise ValueError("输入字典必须包含 'content' 字段")

        # 获取参数
        chunk_size = kwargs.get('chunk_size', self.chunk_size)
        overlap = kwargs.get('overlap', self.overlap)

        content = input_data['content']
        structure = input_data.get('structure', [])
        file_path = input_data.get('file_path', 'unknown')

        self.logger.info(
            f"📝 开始切分文本: 长度={len(content)}, "
            f"策略={self.strategy}, chunk_size={chunk_size}"
        )

        # 根据策略选择切分方法
        if self.strategy == 'smart':
            chunks = await self._smart_chunk(content, structure, chunk_size, overlap)
        elif self.strategy == 'sentence':
            chunks = await self._sentence_chunk(content, chunk_size, overlap)
        elif self.strategy == 'paragraph':
            chunks = await self._paragraph_chunk(content, chunk_size, overlap)
        elif self.strategy == 'fixed':
            chunks = await self._fixed_chunk(content, chunk_size, overlap)

        self.logger.info(f"✅ 切分完成: 共 {len(chunks)} 个块")

        return {
            'file_path': file_path,
            'chunks': chunks,
            'chunk_count': len(chunks),
            'metadata': {
                'original_length': len(content),
                'chunk_size': chunk_size,
                'overlap': overlap,
                'strategy': self.strategy,
                'avg_chunk_size': sum(len(c['text']) for c in chunks) / len(chunks) if chunks else 0
            }
        }

    async def _smart_chunk(self,
                          content: str,
                          structure: List[Dict],
                          chunk_size: int,
                          overlap: int) -> List[Dict]:
        """
        智能切分：优先在段落/句子边界切分

        Args:
            content: 文本内容
            structure: 文档结构信息
            chunk_size: 块大小
            overlap: 重叠大小

        Returns:
            切分后的块列表
        """
        chunks = []

        # 如果文本很短，直接返回
        if len(content) <= chunk_size:
            return [{
                'chunk_id': 0,
                'text': content,
                'start_pos': 0,
                'end_pos': len(content),
                'metadata': {}
            }]

        # 先按段落分割
        paragraphs = self._split_paragraphs(content)

        current_chunk = []
        current_size = 0
        chunk_id = 0
        start_pos = 0

        for para in paragraphs:
            para_len = len(para)

            # 如果当前段落加入后超过 chunk_size
            if current_size + para_len > chunk_size and current_chunk:
                # 保存当前块
                chunk_text = '\n\n'.join(current_chunk)
                chunks.append({
                    'chunk_id': chunk_id,
                    'text': chunk_text,
                    'start_pos': start_pos,
                    'end_pos': start_pos + len(chunk_text),
                    'metadata': self._extract_chunk_metadata(chunk_text, structure)
                })

                # 计算重叠部分
                overlap_text = self._get_overlap_text(current_chunk, overlap)
                current_chunk = [overlap_text] if overlap_text else []
                current_size = len(overlap_text) if overlap_text else 0
                start_pos = start_pos + len(chunk_text) - current_size
                chunk_id += 1

            # 如果单个段落就超过 chunk_size，需要按句子切分
            if para_len > chunk_size:
                sentences = self._split_sentences(para)
                for sentence in sentences:
                    if current_size + len(sentence) > chunk_size and current_chunk:
                        # 保存当前块
                        chunk_text = '\n\n'.join(current_chunk)
                        chunks.append({
                            'chunk_id': chunk_id,
                            'text': chunk_text,
                            'start_pos': start_pos,
                            'end_pos': start_pos + len(chunk_text),
                            'metadata': self._extract_chunk_metadata(chunk_text, structure)
                        })

                        overlap_text = self._get_overlap_text(current_chunk, overlap)
                        current_chunk = [overlap_text] if overlap_text else []
                        current_size = len(overlap_text) if overlap_text else 0
                        start_pos = start_pos + len(chunk_text) - current_size
                        chunk_id += 1

                    current_chunk.append(sentence)
                    current_size += len(sentence)
            else:
                current_chunk.append(para)
                current_size += para_len

        # 保存最后一个块
        if current_chunk:
            chunk_text = '\n\n'.join(current_chunk)
            chunks.append({
                'chunk_id': chunk_id,
                'text': chunk_text,
                'start_pos': start_pos,
                'end_pos': start_pos + len(chunk_text),
                'metadata': self._extract_chunk_metadata(chunk_text, structure)
            })

        return chunks

    async def _sentence_chunk(self,
                             content: str,
                             chunk_size: int,
                             overlap: int) -> List[Dict]:
        """
        按句子切分

        Args:
            content: 文本内容
            chunk_size: 块大小
            overlap: 重叠大小

        Returns:
            切分后的块列表
        """
        sentences = self._split_sentences(content)
        chunks = []

        current_chunk = []
        current_size = 0
        chunk_id = 0
        start_pos = 0

        for sentence in sentences:
            sentence_len = len(sentence)

            if current_size + sentence_len > chunk_size and current_chunk:
                # 保存当前块
                chunk_text = ' '.join(current_chunk)
                chunks.append({
                    'chunk_id': chunk_id,
                    'text': chunk_text,
                    'start_pos': start_pos,
                    'end_pos': start_pos + len(chunk_text),
                    'metadata': {}
                })

                # 计算重叠
                overlap_sentences = self._get_overlap_sentences(current_chunk, overlap)
                current_chunk = overlap_sentences
                current_size = sum(len(s) for s in overlap_sentences)
                start_pos = start_pos + len(chunk_text) - current_size
                chunk_id += 1

            current_chunk.append(sentence)
            current_size += sentence_len

        # 保存最后一个块
        if current_chunk:
            chunk_text = ' '.join(current_chunk)
            chunks.append({
                'chunk_id': chunk_id,
                'text': chunk_text,
                'start_pos': start_pos,
                'end_pos': start_pos + len(chunk_text),
                'metadata': {}
            })

        return chunks

    async def _paragraph_chunk(self,
                              content: str,
                              chunk_size: int,
                              overlap: int) -> List[Dict]:
        """
        按段落切分

        Args:
            content: 文本内容
            chunk_size: 块大小
            overlap: 重叠大小

        Returns:
            切分后的块列表
        """
        paragraphs = self._split_paragraphs(content)
        chunks = []

        current_chunk = []
        current_size = 0
        chunk_id = 0
        start_pos = 0

        for para in paragraphs:
            para_len = len(para)

            if current_size + para_len > chunk_size and current_chunk:
                # 保存当前块
                chunk_text = '\n\n'.join(current_chunk)
                chunks.append({
                    'chunk_id': chunk_id,
                    'text': chunk_text,
                    'start_pos': start_pos,
                    'end_pos': start_pos + len(chunk_text),
                    'metadata': {}
                })

                # 重叠处理
                overlap_text = self._get_overlap_text(current_chunk, overlap)
                current_chunk = [overlap_text] if overlap_text else []
                current_size = len(overlap_text) if overlap_text else 0
                start_pos = start_pos + len(chunk_text) - current_size
                chunk_id += 1

            current_chunk.append(para)
            current_size += para_len

        # 保存最后一个块
        if current_chunk:
            chunk_text = '\n\n'.join(current_chunk)
            chunks.append({
                'chunk_id': chunk_id,
                'text': chunk_text,
                'start_pos': start_pos,
                'end_pos': start_pos + len(chunk_text),
                'metadata': {}
            })

        return chunks

    async def _fixed_chunk(self,
                          content: str,
                          chunk_size: int,
                          overlap: int) -> List[Dict]:
        """
        固定长度切分（不考虑语义边界）

        Args:
            content: 文本内容
            chunk_size: 块大小
            overlap: 重叠大小

        Returns:
            切分后的块列表
        """
        chunks = []
        chunk_id = 0
        start = 0

        while start < len(content):
            end = start + chunk_size
            chunk_text = content[start:end]

            chunks.append({
                'chunk_id': chunk_id,
                'text': chunk_text,
                'start_pos': start,
                'end_pos': end,
                'metadata': {}
            })

            start = end - overlap
            chunk_id += 1

        return chunks

    def _split_paragraphs(self, text: str) -> List[str]:
        """
        按段落分割文本

        Args:
            text: 文本内容

        Returns:
            段落列表
        """
        # 按双换行符分割
        paragraphs = re.split(r'\n\s*\n', text)
        return [p.strip() for p in paragraphs if p.strip()]

    def _split_sentences(self, text: str) -> List[str]:
        """
        按句子分割文本

        Args:
            text: 文本内容

        Returns:
            句子列表
        """
        # 中英文句子分割
        sentences = re.split(r'([。！？\.!?]+)', text)

        # 合并标点符号
        result = []
        for i in range(0, len(sentences) - 1, 2):
            sentence = sentences[i] + (sentences[i + 1] if i + 1 < len(sentences) else '')
            sentence = sentence.strip()
            if sentence:
                result.append(sentence)

        # 处理最后一个句子（如果没有标点）
        if len(sentences) % 2 == 1 and sentences[-1].strip():
            result.append(sentences[-1].strip())

        return result

    def _get_overlap_text(self, chunks: List[str], overlap: int) -> str:
        """
        获取重叠文本

        Args:
            chunks: 当前块列表
            overlap: 重叠字符数

        Returns:
            重叠文本
        """
        if not chunks:
            return ''

        # 从最后的块中提取 overlap 长度的文本
        combined = '\n\n'.join(chunks)
        if len(combined) <= overlap:
            return combined

        return combined[-overlap:]

    def _get_overlap_sentences(self, sentences: List[str], overlap: int) -> List[str]:
        """
        获取重叠的句子

        Args:
            sentences: 句子列表
            overlap: 重叠字符数

        Returns:
            重叠的句子列表
        """
        if not sentences:
            return []

        overlap_sentences = []
        current_size = 0

        # 从后往前累加句子，直到达到 overlap 大小
        for sentence in reversed(sentences):
            if current_size >= overlap:
                break
            overlap_sentences.insert(0, sentence)
            current_size += len(sentence)

        return overlap_sentences

    def _extract_chunk_metadata(self,
                                chunk_text: str,
                                structure: List[Dict]) -> Dict[str, Any]:
        """
        提取块的元数据（如所属章节）

        Args:
            chunk_text: 块文本
            structure: 文档结构信息

        Returns:
            元数据字典
        """
        if not self.respect_structure or not structure:
            return {}

        metadata = {}

        # 查找块中的标题
        for item in structure:
            if 'title' in item and item['title'] in chunk_text:
                metadata['section'] = item['title']
                metadata['level'] = item.get('level', 0)
                break

        return metadata


# 使用示例
if __name__ == "__main__":
    import asyncio

    async def test_chunker():
        """测试文本切分功能"""
        chunker = SmartChunkerSkill(
            chunk_size=500,
            overlap=100,
            strategy='smart'
        )

        # 测试文本
        test_content = """
        # 第一章 引言

        这是第一章的内容。人工智能是计算机科学的一个分支。它企图了解智能的实质。

        ## 1.1 背景

        人工智能的研究始于20世纪50年代。早期的研究者们对人工智能充满了乐观。

        # 第二章 机器学习

        机器学习是人工智能的一个重要分支。它使计算机能够从数据中学习。
        """ * 5  # 重复以产生更长的文本

        input_data = {
            'file_path': 'test.md',
            'content': test_content,
            'structure': [
                {'level': 1, 'title': '第一章 引言'},
                {'level': 2, 'title': '1.1 背景'},
                {'level': 1, 'title': '第二章 机器学习'}
            ]
        }

        print(f"\n{'='*60}")
        print(f"测试智能切分")
        print('='*60)

        result = await chunker.run(input_data)

        if result['success']:
            data = result['data']
            print(f"✅ 切分成功:")
            print(f"   原始长度: {data['metadata']['original_length']}")
            print(f"   块数量: {data['chunk_count']}")
            print(f"   平均块大小: {data['metadata']['avg_chunk_size']:.0f}")

            print(f"\n前 3 个块:")
            for chunk in data['chunks'][:3]:
                print(f"\n   --- Chunk {chunk['chunk_id']} ---")
                print(f"   长度: {len(chunk['text'])}")
                print(f"   预览: {chunk['text'][:100]}...")
                if chunk['metadata']:
                    print(f"   元数据: {chunk['metadata']}")
        else:
            print(f"❌ 切分失败: {result['error']}")

        # 查看统计信息
        print(f"\n{'='*60}")
        print("统计信息:")
        print('='*60)
        stats = chunker.get_stats()
        for key, value in stats.items():
            print(f"   {key}: {value}")

    # 运行测试
    asyncio.run(test_chunker())
