"""
OCRParserSkill - OCR 文档解析器

负责处理扫描版 PDF 和图片文件：
1. 支持 MinerU 和 PaddleOCR 两种 OCR 引擎
2. 分批处理大文件（防止内存溢出）
3. 将识别结果转换为干净的 Markdown 格式
4. 支持断点续传（记录处理进度）
"""

import asyncio
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from .base_skill import BaseSkill


class OCRParserSkill(BaseSkill):
    """
    OCR 文档解析 Skill

    支持扫描版 PDF 和图片的 OCR 识别
    """

    def __init__(self,
                 ocr_engine: str = 'mineru',
                 batch_size: int = 10,
                 output_format: str = 'markdown',
                 checkpoint_dir: Optional[str] = None):
        """
        初始化 OCRParserSkill

        Args:
            ocr_engine: OCR 引擎 ('mineru' 或 'paddleocr')
            batch_size: 批处理大小（每批处理的页数，默认 10）
            output_format: 输出格式 ('markdown' 或 'text')
            checkpoint_dir: 断点文件保存目录（用于断点续传）
        """
        super().__init__(name="OCRParser")
        self.ocr_engine = ocr_engine.lower()
        self.batch_size = batch_size
        self.output_format = output_format
        self.checkpoint_dir = Path(checkpoint_dir) if checkpoint_dir else Path('.checkpoints')
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

        # 验证 OCR 引擎
        if self.ocr_engine not in ['mineru', 'paddleocr']:
            raise ValueError(f"不支持的 OCR 引擎: {ocr_engine}，仅支持 'mineru' 或 'paddleocr'")

    async def execute(self, input_data: Any, **kwargs) -> Dict[str, Any]:
        """
        执行 OCR 解析

        Args:
            input_data: 文件路径（str 或 Path）或路由结果字典
            **kwargs: 额外参数
                - resume: bool, 是否从断点恢复（默认 True）
                - start_page: int, 起始页码（默认 0）

        Returns:
            {
                'file_path': str,
                'file_type': str,
                'content': str,           # OCR 识别后的文本（Markdown 格式）
                'metadata': dict,         # 文档元数据
                'ocr_info': dict          # OCR 处理信息
            }

        Raises:
            ValueError: 不支持的文件类型
            FileNotFoundError: 文件不存在
        """
        # 处理输入数据
        if isinstance(input_data, dict):
            file_path = Path(input_data['file_path'])
            file_type = input_data.get('file_type')
        else:
            file_path = Path(input_data)
            file_type = None

        # 检查文件
        if not file_path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")

        # 获取参数
        resume = kwargs.get('resume', True)
        start_page = kwargs.get('start_page', 0)

        # 根据文件类型选择处理方法
        file_ext = file_path.suffix.lower()

        if file_ext == '.pdf':
            result = await self._process_pdf(file_path, resume, start_page)
        elif file_ext in ['.png', '.jpg', '.jpeg']:
            result = await self._process_image(file_path)
        else:
            raise ValueError(f"不支持的文件类型: {file_ext}")

        return result

    async def _process_pdf(self,
                          file_path: Path,
                          resume: bool,
                          start_page: int) -> Dict[str, Any]:
        """
        处理扫描版 PDF

        Args:
            file_path: PDF 文件路径
            resume: 是否从断点恢复
            start_page: 起始页码

        Returns:
            解析结果字典
        """
        self.logger.info(f"📄 开始 OCR 处理 PDF: {file_path.name}")

        # 获取 PDF 总页数
        try:
            import fitz
            doc = fitz.open(file_path)
            total_pages = len(doc)
            doc.close()
        except ImportError:
            raise ImportError(
                "需要安装 PyMuPDF 库来读取 PDF 信息\n"
                "安装方法: pip install PyMuPDF"
            )

        self.logger.info(f"📊 PDF 总页数: {total_pages}")

        # 检查断点
        checkpoint_file = self.checkpoint_dir / f"{file_path.stem}_ocr_checkpoint.json"
        if resume and checkpoint_file.exists():
            checkpoint = self._load_checkpoint(checkpoint_file)
            start_page = checkpoint.get('last_processed_page', 0) + 1
            self.logger.info(f"🔄 从断点恢复，起始页: {start_page}")

        # 分批处理
        all_content = []
        processed_pages = 0

        for batch_start in range(start_page, total_pages, self.batch_size):
            batch_end = min(batch_start + self.batch_size, total_pages)

            self.logger.info(
                f"🔄 处理第 {batch_start + 1}-{batch_end} 页 "
                f"({batch_end}/{total_pages})"
            )

            try:
                # 执行 OCR
                batch_content = await self._ocr_pdf_batch(
                    file_path,
                    batch_start,
                    batch_end
                )
                all_content.append(batch_content)
                processed_pages = batch_end

                # 保存断点
                self._save_checkpoint(checkpoint_file, {
                    'file_path': str(file_path),
                    'total_pages': total_pages,
                    'last_processed_page': batch_end - 1,
                    'processed_batches': (batch_end - start_page) // self.batch_size + 1
                })

            except Exception as e:
                self.logger.error(f"❌ 处理第 {batch_start + 1}-{batch_end} 页失败: {e}")
                # 保存当前进度
                self._save_checkpoint(checkpoint_file, {
                    'file_path': str(file_path),
                    'total_pages': total_pages,
                    'last_processed_page': batch_start - 1,
                    'error': str(e)
                })
                raise

        # 合并内容
        content = '\n\n'.join(all_content)

        # 清理断点文件（处理完成）
        if checkpoint_file.exists():
            checkpoint_file.unlink()
            self.logger.info("✅ 处理完成，已清理断点文件")

        return {
            'file_path': str(file_path),
            'file_type': 'pdf',
            'content': content,
            'metadata': {
                'file_name': file_path.name,
                'file_size': file_path.stat().st_size,
                'total_pages': total_pages,
                'char_count': len(content)
            },
            'ocr_info': {
                'engine': self.ocr_engine,
                'processed_pages': processed_pages,
                'batch_size': self.batch_size,
                'output_format': self.output_format
            }
        }

    async def _ocr_pdf_batch(self,
                            file_path: Path,
                            start_page: int,
                            end_page: int) -> str:
        """
        对 PDF 的一批页面执行 OCR

        Args:
            file_path: PDF 文件路径
            start_page: 起始页码（从 0 开始）
            end_page: 结束页码（不包含）

        Returns:
            识别后的文本内容
        """
        if self.ocr_engine == 'mineru':
            return await self._ocr_with_mineru(file_path, start_page, end_page)
        elif self.ocr_engine == 'paddleocr':
            return await self._ocr_with_paddleocr(file_path, start_page, end_page)

    async def _ocr_with_mineru(self,
                               file_path: Path,
                               start_page: int,
                               end_page: int) -> str:
        """
        使用 MinerU 进行 OCR

        Args:
            file_path: PDF 文件路径
            start_page: 起始页码
            end_page: 结束页码

        Returns:
            Markdown 格式的文本
        """
        try:
            # 注意：这里需要根据 MinerU 的实际 API 进行调整
            # 以下是示例代码
            from magic_pdf.pipe.UNIPipe import UNIPipe
            from magic_pdf.rw.DiskReaderWriter import DiskReaderWriter

            self.logger.debug(f"使用 MinerU 处理页面 {start_page}-{end_page}")

            # 创建临时输出目录
            temp_dir = self.checkpoint_dir / f"temp_{file_path.stem}"
            temp_dir.mkdir(exist_ok=True)

            # 初始化 MinerU
            reader = DiskReaderWriter(str(file_path.parent))
            pipe = UNIPipe(str(file_path), reader)

            # 处理指定页面
            # 注意：实际 API 可能不同，需要根据 MinerU 文档调整
            result = pipe.pipe_parse()

            # 提取 Markdown 内容
            markdown_content = result.get('markdown', '')

            return markdown_content

        except ImportError:
            raise ImportError(
                "需要安装 MinerU 库\n"
                "安装方法: pip install magic-pdf"
            )
        except Exception as e:
            self.logger.error(f"MinerU OCR 失败: {e}")
            raise

    async def _ocr_with_paddleocr(self,
                                  file_path: Path,
                                  start_page: int,
                                  end_page: int) -> str:
        """
        使用 PaddleOCR 进行 OCR

        Args:
            file_path: PDF 文件路径
            start_page: 起始页码
            end_page: 结束页码

        Returns:
            文本内容
        """
        try:
            from paddleocr import PaddleOCR
            import fitz
            from PIL import Image
            import io

            self.logger.debug(f"使用 PaddleOCR 处理页面 {start_page}-{end_page}")

            # 初始化 PaddleOCR
            ocr = PaddleOCR(use_angle_cls=True, lang='ch')

            # 打开 PDF
            doc = fitz.open(file_path)

            all_text = []

            # 逐页处理
            for page_num in range(start_page, end_page):
                page = doc[page_num]

                # 将页面转换为图片
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2倍缩放提高质量
                img_data = pix.tobytes("png")
                img = Image.open(io.BytesIO(img_data))

                # 执行 OCR
                result = ocr.ocr(img_data, cls=True)

                # 提取文本
                page_text = []
                if result and result[0]:
                    for line in result[0]:
                        text = line[1][0]  # 提取识别的文本
                        page_text.append(text)

                # 添加页面标记（Markdown 格式）
                if self.output_format == 'markdown':
                    all_text.append(f"## 第 {page_num + 1} 页\n")
                    all_text.append('\n'.join(page_text))
                else:
                    all_text.extend(page_text)

            doc.close()

            return '\n\n'.join(all_text)

        except ImportError:
            raise ImportError(
                "需要安装 PaddleOCR 库\n"
                "安装方法: pip install paddleocr"
            )
        except Exception as e:
            self.logger.error(f"PaddleOCR 失败: {e}")
            raise

    async def _process_image(self, file_path: Path) -> Dict[str, Any]:
        """
        处理单张图片

        Args:
            file_path: 图片文件路径

        Returns:
            解析结果字典
        """
        self.logger.info(f"🖼️ 开始 OCR 处理图片: {file_path.name}")

        try:
            from paddleocr import PaddleOCR

            # 初始化 PaddleOCR
            ocr = PaddleOCR(use_angle_cls=True, lang='ch')

            # 执行 OCR
            result = ocr.ocr(str(file_path), cls=True)

            # 提取文本
            text_lines = []
            if result and result[0]:
                for line in result[0]:
                    text = line[1][0]
                    text_lines.append(text)

            content = '\n'.join(text_lines)

            return {
                'file_path': str(file_path),
                'file_type': 'image',
                'content': content,
                'metadata': {
                    'file_name': file_path.name,
                    'file_size': file_path.stat().st_size,
                    'char_count': len(content)
                },
                'ocr_info': {
                    'engine': self.ocr_engine,
                    'output_format': self.output_format
                }
            }

        except ImportError:
            raise ImportError(
                "需要安装 PaddleOCR 库\n"
                "安装方法: pip install paddleocr"
            )

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

    async def test_ocr():
        """测试 OCR 解析功能"""
        # 使用 PaddleOCR
        parser = OCRParserSkill(
            ocr_engine='paddleocr',
            batch_size=5,
            output_format='markdown'
        )

        # 测试 PDF
        test_file = "data/scanned_document.pdf"

        print(f"\n{'='*60}")
        print(f"测试文件: {test_file}")
        print('='*60)

        result = await parser.run(test_file, resume=True)

        if result['success']:
            data = result['data']
            print(f"✅ OCR 成功:")
            print(f"   引擎: {data['ocr_info']['engine']}")
            print(f"   处理页数: {data['ocr_info']['processed_pages']}")
            print(f"   字符数: {data['metadata']['char_count']}")
            print(f"   内容预览: {data['content'][:200]}...")
        else:
            print(f"❌ OCR 失败: {result['error']}")

        # 查看统计信息
        print(f"\n{'='*60}")
        print("统计信息:")
        print('='*60)
        stats = parser.get_stats()
        for key, value in stats.items():
            print(f"   {key}: {value}")

    # 运行测试
    asyncio.run(test_ocr())
