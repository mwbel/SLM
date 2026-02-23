"""
Skill 系统使用示例

演示如何使用模块化的 Skill 系统处理文档
"""

import asyncio
from pathlib import Path
import sys

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.skills import (
    WorkflowManager,
    FileRouterSkill,
    NativeParserSkill,
    OCRParserSkill,
    SmartChunkerSkill
)


async def example_1_single_file():
    """
    示例 1: 处理单个文件（完整流程）

    使用 WorkflowManager 自动完成：
    1. 文件路由
    2. 文档解析
    3. 智能切分
    """
    print("\n" + "="*60)
    print("示例 1: 处理单个文件")
    print("="*60)

    # 创建工作流管理器
    manager = WorkflowManager(
        checkpoint_dir='.workflow_checkpoints',
        enable_checkpoint=True  # 启用断点续传
    )

    # 处理文件
    result = await manager.process_file(
        file_path="data/example.pdf",
        chunk_size=1000,      # 每块 1000 字符
        overlap=200,          # 重叠 200 字符
        chunking_strategy='smart',  # 智能切分策略
        resume=True           # 支持断点续传
    )

    if result['success']:
        print(f"\n✅ 处理成功!")
        print(f"   文件: {result['file_path']}")
        print(f"   块数: {result['metadata']['chunk_count']}")
        print(f"   原始长度: {result['metadata']['original_length']} 字符")

        # 查看前 3 个块
        print(f"\n前 3 个块预览:")
        for chunk in result['chunks'][:3]:
            print(f"\n   Chunk {chunk['chunk_id']}:")
            print(f"   长度: {len(chunk['text'])} 字符")
            print(f"   预览: {chunk['text'][:100]}...")
    else:
        print(f"\n❌ 处理失败: {result['error']}")


async def example_2_batch_processing():
    """
    示例 2: 批量处理目录中的所有文件
    """
    print("\n" + "="*60)
    print("示例 2: 批量处理目录")
    print("="*60)

    manager = WorkflowManager()

    # 批量处理
    result = await manager.process_directory(
        input_dir="data/documents",
        output_dir="data/output",
        chunk_size=1000,
        overlap=200,
        chunking_strategy='smart'
    )

    print(f"\n批量处理结果:")
    print(f"   总文件数: {result['total_files']}")
    print(f"   成功: {result['success_count']}")
    print(f"   失败: {result['error_count']}")


async def example_3_custom_workflow():
    """
    示例 3: 自定义工作流（手动串联 Skills）

    适用于需要更细粒度控制的场景
    """
    print("\n" + "="*60)
    print("示例 3: 自定义工作流")
    print("="*60)

    file_path = "data/example.docx"

    # Step 1: 文件路由
    router = FileRouterSkill()
    route_result = await router.run(file_path)

    if not route_result['success']:
        print(f"❌ 路由失败: {route_result['error']}")
        return

    route_data = route_result['data']
    print(f"\n✅ Step 1 - 文件路由:")
    print(f"   文件类型: {route_data['file_type']}")
    print(f"   推荐解析器: {route_data['recommended_parser']}")

    # Step 2: 文档解析
    if route_data['recommended_parser'] == 'ocr':
        parser = OCRParserSkill(ocr_engine='paddleocr')
    else:
        parser = NativeParserSkill(preserve_formatting=True)

    parse_result = await parser.run(route_data)

    if not parse_result['success']:
        print(f"❌ 解析失败: {parse_result['error']}")
        return

    parse_data = parse_result['data']
    print(f"\n✅ Step 2 - 文档解析:")
    print(f"   字符数: {parse_data['metadata']['char_count']}")
    print(f"   结构元素: {len(parse_data.get('structure', []))}")

    # Step 3: 智能切分
    chunker = SmartChunkerSkill(
        chunk_size=800,
        overlap=150,
        strategy='smart',
        respect_structure=True
    )

    chunk_result = await chunker.run(parse_data)

    if not chunk_result['success']:
        print(f"❌ 切分失败: {chunk_result['error']}")
        return

    chunk_data = chunk_result['data']
    print(f"\n✅ Step 3 - 智能切分:")
    print(f"   块数: {chunk_data['chunk_count']}")
    print(f"   平均块大小: {chunk_data['metadata']['avg_chunk_size']:.0f} 字符")


async def example_4_ocr_with_checkpoint():
    """
    示例 4: OCR 处理大文件（支持断点续传）

    适用于处理 100+ 页的扫描版 PDF
    """
    print("\n" + "="*60)
    print("示例 4: OCR 处理大文件（断点续传）")
    print("="*60)

    # 创建 OCR 解析器
    ocr_parser = OCRParserSkill(
        ocr_engine='paddleocr',  # 或 'mineru'
        batch_size=10,           # 每批处理 10 页
        output_format='markdown',
        checkpoint_dir='.ocr_checkpoints'
    )

    # 处理大文件
    result = await ocr_parser.run(
        "data/large_scanned_document.pdf",
        resume=True  # 如果中断，下次会从断点继续
    )

    if result['success']:
        data = result['data']
        print(f"\n✅ OCR 处理成功:")
        print(f"   引擎: {data['ocr_info']['engine']}")
        print(f"   处理页数: {data['ocr_info']['processed_pages']}")
        print(f"   字符数: {data['metadata']['char_count']}")
    else:
        print(f"\n❌ OCR 处理失败: {result['error']}")
        print(f"   当前进度已保存，可以使用 resume=True 继续")


async def example_5_different_chunking_strategies():
    """
    示例 5: 不同的切分策略对比
    """
    print("\n" + "="*60)
    print("示例 5: 不同切分策略对比")
    print("="*60)

    # 准备测试文本
    test_content = """
    # 人工智能简介

    人工智能（Artificial Intelligence，AI）是计算机科学的一个分支。
    它企图了解智能的实质，并生产出一种新的能以人类智能相似的方式做出反应的智能机器。

    ## 发展历史

    人工智能的研究始于20世纪50年代。早期的研究者们对人工智能充满了乐观。
    """ * 10  # 重复以产生更长的文本

    input_data = {
        'file_path': 'test.md',
        'content': test_content,
        'structure': []
    }

    strategies = ['smart', 'sentence', 'paragraph', 'fixed']

    for strategy in strategies:
        chunker = SmartChunkerSkill(
            chunk_size=500,
            overlap=100,
            strategy=strategy
        )

        result = await chunker.run(input_data)

        if result['success']:
            data = result['data']
            print(f"\n策略: {strategy}")
            print(f"   块数: {data['chunk_count']}")
            print(f"   平均块大小: {data['metadata']['avg_chunk_size']:.0f} 字符")


async def main():
    """运行所有示例"""
    print("\n" + "="*60)
    print("Skill 系统使用示例")
    print("="*60)

    # 运行示例（根据需要注释/取消注释）

    # await example_1_single_file()
    # await example_2_batch_processing()
    await example_3_custom_workflow()
    # await example_4_ocr_with_checkpoint()
    # await example_5_different_chunking_strategies()


if __name__ == "__main__":
    asyncio.run(main())
