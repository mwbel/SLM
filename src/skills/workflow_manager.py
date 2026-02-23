"""
WorkflowManager - 流程控制器

负责：
1. 串联多个 Skill 形成完整的处理流程
2. 支持断点续传（保存和恢复处理进度）
3. 错误处理和重试机制
4. 生成处理报告
"""

import asyncio
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

from .base_skill import BaseSkill
from .router_file import FileRouterSkill
from .parser_native import NativeParserSkill
from .parser_pdf_ocr import OCRParserSkill
from .chunk_smart import SmartChunkerSkill


class WorkflowManager:
    """
    工作流管理器

    串联多个 Skill，实现完整的文档处理流程
    """

    def __init__(self,
                 checkpoint_dir: str = '.workflow_checkpoints',
                 enable_checkpoint: bool = True,
                 max_retries: int = 3):
        """
        初始化 WorkflowManager

        Args:
            checkpoint_dir: 断点文件保存目录
            enable_checkpoint: 是否启用断点续传
            max_retries: 最大重试次数
        """
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        self.enable_checkpoint = enable_checkpoint
        self.max_retries = max_retries

        # 初始化 Skills
        self.router = FileRouterSkill()
        self.native_parser = NativeParserSkill()
        self.ocr_parser = OCRParserSkill(checkpoint_dir=str(self.checkpoint_dir))
        self.chunker = SmartChunkerSkill()

        # 工作流状态
        self.workflow_id = None
        self.current_step = None
        self.results = {}

    async def process_file(self,
                          file_path: str,
                          chunk_size: int = 1000,
                          overlap: int = 200,
                          chunking_strategy: str = 'smart',
                          resume: bool = True) -> Dict[str, Any]:
        """
        处理单个文件的完整流程

        流程：
        1. 文件路由（识别类型）
        2. 文档解析（原生或 OCR）
        3. 智能切分
        4. 返回结果

        Args:
            file_path: 文件路径
            chunk_size: 切分块大小
            overlap: 切分重叠大小
            chunking_strategy: 切分策略
            resume: 是否从断点恢复

        Returns:
            {
                'success': bool,
                'file_path': str,
                'chunks': List[Dict],
                'metadata': dict,
                'workflow_report': dict
            }
        """
        file_path = Path(file_path)
        self.workflow_id = f"{file_path.stem}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        print(f"\n{'='*60}")
        print(f"🚀 开始处理文件: {file_path.name}")
        print(f"   工作流 ID: {self.workflow_id}")
        print('='*60)

        # 检查断点
        checkpoint_file = self.checkpoint_dir / f"{file_path.stem}_workflow.json"
        if resume and self.enable_checkpoint and checkpoint_file.exists():
            print(f"📂 发现断点文件，尝试恢复...")
            checkpoint = self._load_checkpoint(checkpoint_file)
            return await self._resume_workflow(checkpoint, file_path, chunk_size, overlap, chunking_strategy)

        # 开始新的工作流
        workflow_start = datetime.now()

        try:
            # Step 1: 文件路由
            print(f"\n📍 Step 1: 文件路由")
            self.current_step = 'routing'
            self._save_workflow_checkpoint(checkpoint_file, {
                'workflow_id': self.workflow_id,
                'file_path': str(file_path),
                'current_step': 'routing',
                'timestamp': datetime.now().isoformat()
            })

            route_result = await self.router.run(str(file_path))
            if not route_result['success']:
                raise Exception(f"文件路由失败: {route_result['error']}")

            route_data = route_result['data']
            print(f"   ✅ 文件类型: {route_data['file_type']}")
            print(f"   ✅ 推荐解析器: {route_data['recommended_parser']}")

            # Step 2: 文档解析
            print(f"\n📄 Step 2: 文档解析")
            self.current_step = 'parsing'
            self._save_workflow_checkpoint(checkpoint_file, {
                'workflow_id': self.workflow_id,
                'file_path': str(file_path),
                'current_step': 'parsing',
                'route_data': route_data,
                'timestamp': datetime.now().isoformat()
            })

            if route_data['recommended_parser'] == 'ocr':
                print(f"   使用 OCR 解析器")
                parse_result = await self.ocr_parser.run(route_data, resume=resume)
            else:
                print(f"   使用原生解析器")
                parse_result = await self.native_parser.run(route_data)

            if not parse_result['success']:
                raise Exception(f"文档解析失败: {parse_result['error']}")

            parse_data = parse_result['data']
            print(f"   ✅ 解析完成: {parse_data['metadata']['char_count']} 字符")

            # Step 3: 智能切分
            print(f"\n✂️  Step 3: 智能切分")
            self.current_step = 'chunking'
            self._save_workflow_checkpoint(checkpoint_file, {
                'workflow_id': self.workflow_id,
                'file_path': str(file_path),
                'current_step': 'chunking',
                'route_data': route_data,
                'parse_data': parse_data,
                'timestamp': datetime.now().isoformat()
            })

            chunk_result = await self.chunker.run(
                parse_data,
                chunk_size=chunk_size,
                overlap=overlap
            )

            if not chunk_result['success']:
                raise Exception(f"文本切分失败: {chunk_result['error']}")

            chunk_data = chunk_result['data']
            print(f"   ✅ 切分完成: {chunk_data['chunk_count']} 个块")

            # 计算总耗时
            workflow_end = datetime.now()
            total_time = (workflow_end - workflow_start).total_seconds()

            # 生成工作流报告
            workflow_report = {
                'workflow_id': self.workflow_id,
                'file_path': str(file_path),
                'total_time': round(total_time, 2),
                'steps': {
                    'routing': {
                        'success': True,
                        'time': route_result['execution_time'],
                        'result': route_data
                    },
                    'parsing': {
                        'success': True,
                        'time': parse_result['execution_time'],
                        'parser': route_data['recommended_parser']
                    },
                    'chunking': {
                        'success': True,
                        'time': chunk_result['execution_time'],
                        'chunk_count': chunk_data['chunk_count']
                    }
                }
            }

            # 清理断点文件
            if checkpoint_file.exists():
                checkpoint_file.unlink()
                print(f"\n🗑️  已清理断点文件")

            print(f"\n{'='*60}")
            print(f"✅ 工作流完成!")
            print(f"   总耗时: {total_time:.2f} 秒")
            print(f"   生成块数: {chunk_data['chunk_count']}")
            print('='*60)

            return {
                'success': True,
                'file_path': str(file_path),
                'chunks': chunk_data['chunks'],
                'metadata': {
                    'file_type': route_data['file_type'],
                    'is_scanned': route_data.get('is_scanned', False),
                    'original_length': parse_data['metadata']['char_count'],
                    'chunk_count': chunk_data['chunk_count'],
                    'chunk_size': chunk_size,
                    'overlap': overlap,
                    'strategy': chunking_strategy
                },
                'workflow_report': workflow_report
            }

        except Exception as e:
            print(f"\n❌ 工作流失败: {e}")

            # 保存错误状态
            self._save_workflow_checkpoint(checkpoint_file, {
                'workflow_id': self.workflow_id,
                'file_path': str(file_path),
                'current_step': self.current_step,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            })

            return {
                'success': False,
                'file_path': str(file_path),
                'error': str(e),
                'current_step': self.current_step
            }

    async def _resume_workflow(self,
                               checkpoint: Dict,
                               file_path: Path,
                               chunk_size: int,
                               overlap: int,
                               chunking_strategy: str) -> Dict[str, Any]:
        """
        从断点恢复工作流

        Args:
            checkpoint: 断点数据
            file_path: 文件路径
            chunk_size: 切分块大小
            overlap: 切分重叠大小
            chunking_strategy: 切分策略

        Returns:
            处理结果
        """
        print(f"🔄 从断点恢复工作流")
        print(f"   上次步骤: {checkpoint.get('current_step')}")
        print(f"   时间: {checkpoint.get('timestamp')}")

        current_step = checkpoint.get('current_step')

        # 根据断点步骤决定从哪里继续
        if current_step == 'routing':
            # 从头开始
            print(f"   从文件路由步骤重新开始")
            return await self.process_file(file_path, chunk_size, overlap, chunking_strategy, resume=False)

        elif current_step == 'parsing':
            # 从解析步骤继续
            print(f"   从文档解析步骤继续")
            route_data = checkpoint.get('route_data')

            if route_data['recommended_parser'] == 'ocr':
                # OCR 解析器自带断点续传
                parse_result = await self.ocr_parser.run(route_data, resume=True)
            else:
                parse_result = await self.native_parser.run(route_data)

            if not parse_result['success']:
                raise Exception(f"文档解析失败: {parse_result['error']}")

            parse_data = parse_result['data']

            # 继续切分
            chunk_result = await self.chunker.run(parse_data, chunk_size=chunk_size, overlap=overlap)

            if not chunk_result['success']:
                raise Exception(f"文本切分失败: {chunk_result['error']}")

            chunk_data = chunk_result['data']

            return {
                'success': True,
                'file_path': str(file_path),
                'chunks': chunk_data['chunks'],
                'metadata': {
                    'file_type': route_data['file_type'],
                    'chunk_count': chunk_data['chunk_count']
                }
            }

        elif current_step == 'chunking':
            # 从切分步骤继续
            print(f"   从文本切分步骤继续")
            parse_data = checkpoint.get('parse_data')

            chunk_result = await self.chunker.run(parse_data, chunk_size=chunk_size, overlap=overlap)

            if not chunk_result['success']:
                raise Exception(f"文本切分失败: {chunk_result['error']}")

            chunk_data = chunk_result['data']

            return {
                'success': True,
                'file_path': str(file_path),
                'chunks': chunk_data['chunks'],
                'metadata': {
                    'chunk_count': chunk_data['chunk_count']
                }
            }

        else:
            print(f"   未知的断点步骤，从头开始")
            return await self.process_file(file_path, chunk_size, overlap, chunking_strategy, resume=False)

    async def process_directory(self,
                                input_dir: str,
                                output_dir: str,
                                chunk_size: int = 1000,
                                overlap: int = 200,
                                chunking_strategy: str = 'smart') -> Dict[str, Any]:
        """
        批量处理目录中的所有文件

        Args:
            input_dir: 输入目录
            output_dir: 输出目录
            chunk_size: 切分块大小
            overlap: 切分重叠大小
            chunking_strategy: 切分策略

        Returns:
            批量处理结果
        """
        input_path = Path(input_dir)
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        print(f"\n{'='*60}")
        print(f"📁 批量处理目录: {input_dir}")
        print('='*60)

        # 支持的文件类型
        supported_extensions = ['.txt', '.md', '.docx', '.pdf', '.png', '.jpg', '.jpeg']

        # 收集所有文件
        files = [
            f for f in input_path.iterdir()
            if f.is_file() and f.suffix.lower() in supported_extensions
        ]

        print(f"找到 {len(files)} 个文件")

        results = []
        success_count = 0
        error_count = 0

        for i, file_path in enumerate(files, 1):
            print(f"\n{'='*60}")
            print(f"处理文件 {i}/{len(files)}: {file_path.name}")
            print('='*60)

            try:
                result = await self.process_file(
                    str(file_path),
                    chunk_size=chunk_size,
                    overlap=overlap,
                    chunking_strategy=chunking_strategy
                )

                if result['success']:
                    # 保存结果
                    output_file = output_path / f"{file_path.stem}_chunks.json"
                    self._save_chunks(output_file, result['chunks'])
                    print(f"✅ 已保存到: {output_file}")
                    success_count += 1
                else:
                    print(f"❌ 处理失败: {result.get('error')}")
                    error_count += 1

                results.append(result)

            except Exception as e:
                print(f"❌ 处理文件 {file_path.name} 时出错: {e}")
                error_count += 1
                results.append({
                    'success': False,
                    'file_path': str(file_path),
                    'error': str(e)
                })

        print(f"\n{'='*60}")
        print(f"📊 批量处理完成")
        print(f"   总文件数: {len(files)}")
        print(f"   成功: {success_count}")
        print(f"   失败: {error_count}")
        print('='*60)

        return {
            'total_files': len(files),
            'success_count': success_count,
            'error_count': error_count,
            'results': results
        }

    def _save_workflow_checkpoint(self, checkpoint_file: Path, data: dict):
        """保存工作流断点"""
        if not self.enable_checkpoint:
            return

        with open(checkpoint_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _load_checkpoint(self, checkpoint_file: Path) -> dict:
        """加载工作流断点"""
        with open(checkpoint_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _save_chunks(self, output_file: Path, chunks: List[Dict]):
        """保存切分结果"""
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(chunks, f, ensure_ascii=False, indent=2)


# 使用示例
if __name__ == "__main__":
    import asyncio

    async def test_workflow():
        """测试工作流管理器"""
        manager = WorkflowManager(
            checkpoint_dir='.workflow_checkpoints',
            enable_checkpoint=True
        )

        # 测试单个文件
        print("\n=== 测试单个文件处理 ===")
        result = await manager.process_file(
            file_path="data/example.pdf",
            chunk_size=1000,
            overlap=200,
            chunking_strategy='smart',
            resume=True
        )

        if result['success']:
            print(f"\n✅ 处理成功:")
            print(f"   文件: {result['file_path']}")
            print(f"   块数: {result['metadata']['chunk_count']}")
            print(f"   总耗时: {result['workflow_report']['total_time']} 秒")
        else:
            print(f"\n❌ 处理失败: {result['error']}")

        # 测试批量处理
        print("\n\n=== 测试批量处理 ===")
        batch_result = await manager.process_directory(
            input_dir="data/documents",
            output_dir="data/output",
            chunk_size=1000,
            overlap=200
        )

        print(f"\n批量处理结果:")
        print(f"   成功: {batch_result['success_count']}")
        print(f"   失败: {batch_result['error_count']}")

    # 运行测试
    asyncio.run(test_workflow())
