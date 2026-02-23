"""
FileRouterSkill - 文件类型识别与路由

负责：
1. 根据文件后缀识别文件类型
2. 对于 PDF 文件，检测是否为扫描版（通过读取前 2 页判断字符数）
3. 返回文件类型和推荐的处理路径
"""

import asyncio
from pathlib import Path
from typing import Dict, Any
from .base_skill import BaseSkill


class FileRouterSkill(BaseSkill):
    """
    文件路由 Skill

    识别文件类型并决定后续处理路径
    """

    # 支持的文件类型
    SUPPORTED_TYPES = {
        '.txt': 'text',
        '.md': 'markdown',
        '.docx': 'word',
        '.pdf': 'pdf',
        '.png': 'image',
        '.jpg': 'image',
        '.jpeg': 'image',
    }

    def __init__(self,
                 scanned_pdf_threshold: int = 100,
                 check_pages: int = 2):
        """
        初始化 FileRouterSkill

        Args:
            scanned_pdf_threshold: 判定为扫描版的字符数阈值（默认 100）
            check_pages: 检测 PDF 时读取的页数（默认前 2 页）
        """
        super().__init__(name="FileRouter")
        self.scanned_pdf_threshold = scanned_pdf_threshold
        self.check_pages = check_pages

    async def execute(self, input_data: Any, **kwargs) -> Dict[str, Any]:
        """
        执行文件路由逻辑

        Args:
            input_data: 文件路径（str 或 Path）
            **kwargs: 额外参数

        Returns:
            {
                'file_path': str,           # 文件路径
                'file_type': str,           # 文件类型
                'is_scanned': bool,         # 是否为扫描版（仅 PDF）
                'recommended_parser': str,  # 推荐的解析器
                'metadata': dict            # 额外的元数据
            }

        Raises:
            FileNotFoundError: 文件不存在
            ValueError: 不支持的文件类型
        """
        file_path = Path(input_data)

        # 检查文件是否存在
        if not file_path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")

        if not file_path.is_file():
            raise ValueError(f"路径不是文件: {file_path}")

        # 获取文件后缀
        file_ext = file_path.suffix.lower()

        # 检查是否支持
        if file_ext not in self.SUPPORTED_TYPES:
            raise ValueError(
                f"不支持的文件类型: {file_ext}\n"
                f"支持的类型: {', '.join(self.SUPPORTED_TYPES.keys())}"
            )

        file_type = self.SUPPORTED_TYPES[file_ext]
        is_scanned = False
        recommended_parser = 'native'

        # 特殊处理：PDF 需要检测是否为扫描版
        if file_type == 'pdf':
            is_scanned = await self._detect_scanned_pdf(file_path)
            recommended_parser = 'ocr' if is_scanned else 'native'
            self.logger.info(
                f"📄 PDF 检测结果: "
                f"{'扫描版' if is_scanned else '原生版'}"
            )

        # 图片文件直接使用 OCR
        elif file_type == 'image':
            is_scanned = True
            recommended_parser = 'ocr'

        return {
            'file_path': str(file_path),
            'file_type': file_type,
            'is_scanned': is_scanned,
            'recommended_parser': recommended_parser,
            'metadata': {
                'file_name': file_path.name,
                'file_size': file_path.stat().st_size,
                'file_ext': file_ext
            }
        }

    async def _detect_scanned_pdf(self, file_path: Path) -> bool:
        """
        检测 PDF 是否为扫描版

        通过读取前 N 页，统计文本字符数来判断：
        - 字符数很少（< threshold）：判定为扫描版
        - 字符数较多：判定为原生 PDF

        Args:
            file_path: PDF 文件路径

        Returns:
            True 表示扫描版，False 表示原生版
        """
        try:
            # 使用 PyMuPDF (fitz) 读取 PDF
            import fitz

            doc = fitz.open(file_path)
            total_chars = 0
            pages_to_check = min(self.check_pages, len(doc))

            self.logger.debug(
                f"检测 PDF: {file_path.name}, "
                f"总页数: {len(doc)}, 检测页数: {pages_to_check}"
            )

            # 读取前 N 页的文本
            for page_num in range(pages_to_check):
                page = doc[page_num]
                text = page.get_text()
                total_chars += len(text.strip())

            doc.close()

            # 计算平均每页字符数
            avg_chars_per_page = total_chars / pages_to_check if pages_to_check > 0 else 0

            self.logger.debug(
                f"前 {pages_to_check} 页平均字符数: {avg_chars_per_page:.0f}, "
                f"阈值: {self.scanned_pdf_threshold}"
            )

            # 判断是否为扫描版
            return avg_chars_per_page < self.scanned_pdf_threshold

        except ImportError:
            self.logger.warning(
                "⚠️ PyMuPDF 未安装，无法检测扫描版 PDF，默认当作原生 PDF 处理\n"
                "安装方法: pip install PyMuPDF"
            )
            return False

        except Exception as e:
            self.logger.error(f"检测 PDF 时出错: {e}，默认当作原生 PDF 处理")
            return False

    async def batch_route(self, file_paths: list) -> list:
        """
        批量路由多个文件

        Args:
            file_paths: 文件路径列表

        Returns:
            路由结果列表
        """
        tasks = [self.run(file_path) for file_path in file_paths]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 过滤掉异常结果
        valid_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                self.logger.error(f"路由文件 {file_paths[i]} 失败: {result}")
            elif result['success']:
                valid_results.append(result['data'])

        return valid_results


# 使用示例
if __name__ == "__main__":
    import asyncio

    async def test_router():
        """测试文件路由功能"""
        router = FileRouterSkill(
            scanned_pdf_threshold=100,
            check_pages=2
        )

        # 测试单个文件
        test_files = [
            "data/example.pdf",
            "data/example.txt",
            "data/example.docx",
        ]

        for file_path in test_files:
            print(f"\n{'='*60}")
            print(f"测试文件: {file_path}")
            print('='*60)

            result = await router.run(file_path)

            if result['success']:
                data = result['data']
                print(f"✅ 路由成功:")
                print(f"   文件类型: {data['file_type']}")
                print(f"   是否扫描版: {data['is_scanned']}")
                print(f"   推荐解析器: {data['recommended_parser']}")
                print(f"   文件大小: {data['metadata']['file_size']} 字节")
            else:
                print(f"❌ 路由失败: {result['error']}")

        # 查看统计信息
        print(f"\n{'='*60}")
        print("统计信息:")
        print('='*60)
        stats = router.get_stats()
        for key, value in stats.items():
            print(f"   {key}: {value}")

    # 运行测试
    asyncio.run(test_router())
