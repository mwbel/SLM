#!/usr/bin/env python3
"""调试导入问题"""

import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

print("Python 路径:", sys.path[0])
print("\n开始测试导入...\n")

try:
    print("1. 测试 BaseSkill 导入...")
    from src.skills.base_skill import BaseSkill
    print("   ✅ BaseSkill 导入成功")
except Exception as e:
    print(f"   ❌ BaseSkill 导入失败: {e}")
    import traceback
    traceback.print_exc()

try:
    print("\n2. 测试 parser_pdf_ocr 直接导入...")
    from src.skills.parser_pdf_ocr import OCRParserSkill
    print("   ✅ parser_pdf_ocr 直接导入成功")
except Exception as e:
    print(f"   ❌ parser_pdf_ocr 直接导入失败: {e}")
    import traceback
    traceback.print_exc()

try:
    print("\n3. 测试通过 __init__ 导入...")
    from src.skills import OCRParserSkill
    print("   ✅ 通过 __init__ 导入成功")
except Exception as e:
    print(f"   ❌ 通过 __init__ 导入失败: {e}")
    import traceback
    traceback.print_exc()

print("\n测试完成")
