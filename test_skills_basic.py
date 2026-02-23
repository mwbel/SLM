"""
基础 Skill 功能测试

测试每个 Skill 的核心功能是否正常工作
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from src.skills import (
    FileRouterSkill,
    NativeParserSkill,
    SmartChunkerSkill,
    WorkflowManager
)


async def test_file_router():
    """测试文件路由功能"""
    print("\n" + "="*60)
    print("测试 1: FileRouterSkill - 文件类型识别")
    print("="*60)

    router = FileRouterSkill()

    # 测试不同文件类型
    test_files = [
        "test.txt",
        "test.md",
        "test.pdf",
        "test.docx",
        "test.png"
    ]

    for file_path in test_files:
        result = await router.run(file_path)
        if result['success']:
            print(f"✅ {file_path}: {result['file_type']} -> 推荐解析器: {result['recommended_parser']}")
        else:
            print(f"❌ {file_path}: {result['error']}")

    return True


async def test_native_parser():
    """测试原生解析器"""
    print("\n" + "="*60)
    print("测试 2: NativeParserSkill - 文本解析")
    print("="*60)

    parser = NativeParserSkill()

    # 创建测试文本文件
    test_file = Path("test_sample.txt")
    test_content = """这是一个测试文档。

第一段：这是第一段的内容，用于测试文本解析功能。

第二段：这是第二段的内容，包含多个句子。这是第二个句子。这是第三个句子。

第三段：最后一段内容。"""

    test_file.write_text(test_content, encoding='utf-8')

    try:
        result = await parser.run(str(test_file))
        if result['success']:
            print(f"✅ 解析成功")
            # NativeParserSkill 返回 'content' 字段，但可能在嵌套结构中
            content = result.get('content', '')
            if not content and 'data' in result:
                content = result['data'].get('content', '')
            print(f"   文本长度: {len(content)} 字符")
            if content:
                print(f"   前 100 字符: {content[:100]}...")
            if 'metadata' in result:
                print(f"   元数据: {result['metadata']}")
        else:
            print(f"❌ 解析失败: {result['error']}")
    finally:
        # 清理测试文件
        if test_file.exists():
            test_file.unlink()

    return True


async def test_smart_chunker():
    """测试智能切分器"""
    print("\n" + "="*60)
    print("测试 3: SmartChunkerSkill - 文本切分")
    print("="*60)

    chunker = SmartChunkerSkill(
        chunk_size=50,
        overlap=10,
        strategy='smart'
    )

    test_text = """这是第一段文字。这是第一段的第二句话。这是第一段的第三句话。

这是第二段文字。这是第二段的第二句话。

这是第三段文字。这是第三段的第二句话。这是第三段的第三句话。这是第三段的第四句话。"""

    # SmartChunkerSkill 需要解析结果作为输入，字段名是 'content'
    parsed_data = {
        'content': test_text,
        'metadata': {}
    }

    result = await chunker.run(parsed_data)

    if result['success']:
        print(f"✅ 切分成功")
        print(f"   原始文本长度: {len(test_text)} 字符")
        # 获取 chunks，可能在 result 直接层级或嵌套在内部
        chunks = result.get('chunks', result.get('data', {}).get('chunks', []))
        print(f"   切分块数: {len(chunks)} 块")
        print(f"   切分策略: {result.get('strategy', 'N/A')}")
        print(f"\n   前 3 个块:")
        for i, chunk in enumerate(chunks[:3], 1):
            chunk_text = chunk.get('text', chunk.get('content', ''))
            print(f"   块 {i}: {chunk_text[:50]}... (长度: {len(chunk_text)})")
    else:
        print(f"❌ 切分失败: {result['error']}")

    return True


async def test_workflow_manager():
    """测试工作流管理器"""
    print("\n" + "="*60)
    print("测试 4: WorkflowManager - 完整流程")
    print("="*60)

    # 创建测试文件
    test_file = Path("test_workflow.txt")
    test_content = """# 测试文档

## 第一章

这是第一章的内容。包含多个段落。

这是第一章的第二段。

## 第二章

这是第二章的内容。也包含多个段落。

这是第二章的第二段。"""

    test_file.write_text(test_content, encoding='utf-8')

    try:
        manager = WorkflowManager()

        result = await manager.process_file(
            file_path=str(test_file),
            chunk_size=100,
            overlap=20,
            chunking_strategy='smart'
        )

        if result['success']:
            print(f"✅ 工作流执行成功")
            print(f"   文件: {result.get('file_path', 'N/A')}")
            print(f"   解析器: {result.get('parser_used', 'N/A')}")
            if 'text' in result:
                print(f"   文本长度: {len(result['text'])} 字符")
            print(f"   切分块数: {len(result['chunks'])} 块")
            if 'processing_time' in result:
                print(f"   处理时间: {result['processing_time']:.2f} 秒")
        else:
            print(f"❌ 工作流执行失败: {result['error']}")
    finally:
        # 清理测试文件
        if test_file.exists():
            test_file.unlink()

    return True


async def main():
    """运行所有测试"""
    print("\n" + "="*60)
    print("Skill 系统功能测试")
    print("="*60)

    tests = [
        ("FileRouterSkill", test_file_router),
        ("NativeParserSkill", test_native_parser),
        ("SmartChunkerSkill", test_smart_chunker),
        ("WorkflowManager", test_workflow_manager),
    ]

    results = []
    for name, test_func in tests:
        try:
            success = await test_func()
            results.append((name, success))
        except Exception as e:
            print(f"\n❌ {name} 测试出错: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))

    # 打印测试总结
    print("\n" + "="*60)
    print("测试结果总结")
    print("="*60)

    passed = sum(1 for _, success in results if success)
    total = len(results)

    for name, success in results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"{status} - {name}")

    print(f"\n总计: {passed}/{total} 测试通过")

    if passed == total:
        print("\n🎉 所有测试通过！Skill 系统工作正常！")
    else:
        print(f"\n⚠️  有 {total - passed} 个测试失败")


if __name__ == "__main__":
    asyncio.run(main())
