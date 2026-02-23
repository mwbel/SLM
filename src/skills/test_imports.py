"""
测试 Skill 系统重构后的导入

验证所有 Skill 是否可以正常导入和使用
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
# 文件位置: slm-trainer/src/skills/test_imports.py
# 项目根目录: slm-trainer/
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


def test_basic_imports():
    """测试基础导入"""
    print("\n" + "="*60)
    print("测试基础导入")
    print("="*60)

    try:
        from src.skills import BaseSkill
        print("✅ BaseSkill 导入成功")
    except ImportError as e:
        print(f"❌ BaseSkill 导入失败: {e}")
        return False

    try:
        from src.skills import BaseSkillEnhanced
        print("✅ BaseSkillEnhanced 导入成功")
    except ImportError as e:
        print(f"❌ BaseSkillEnhanced 导入失败: {e}")
        return False

    try:
        from src.skills import SkillRegistry
        print("✅ SkillRegistry 导入成功")
    except ImportError as e:
        print(f"❌ SkillRegistry 导入失败: {e}")
        return False

    try:
        from src.skills import SkillTemplate
        print("✅ SkillTemplate 导入成功")
    except ImportError as e:
        print(f"❌ SkillTemplate 导入失败: {e}")
        return False

    return True


def test_classifier_imports():
    """测试 Classifier 导入"""
    print("\n" + "="*60)
    print("测试 Classifier 导入")
    print("="*60)

    try:
        from src.skills import FileRouterSkill
        print("✅ FileRouterSkill 导入成功")

        # 测试实例化
        router = FileRouterSkill()
        print(f"   实例化成功: {router}")
    except Exception as e:
        print(f"❌ FileRouterSkill 失败: {e}")
        return False

    return True


def test_parser_imports():
    """测试 Parser 导入"""
    print("\n" + "="*60)
    print("测试 Parser 导入")
    print("="*60)

    try:
        from src.skills import NativeParserSkill
        print("✅ NativeParserSkill 导入成功")

        parser = NativeParserSkill()
        print(f"   实例化成功: {parser}")
    except Exception as e:
        print(f"❌ NativeParserSkill 失败: {e}")
        return False

    try:
        from src.skills import OCRParserSkill
        print("✅ OCRParserSkill 导入成功")

        parser = OCRParserSkill()
        print(f"   实例化成功: {parser}")
    except Exception as e:
        print(f"❌ OCRParserSkill 失败: {e}")
        return False

    return True


def test_transformer_imports():
    """测试 Transformer 导入"""
    print("\n" + "="*60)
    print("测试 Transformer 导入")
    print("="*60)

    try:
        from src.skills import SmartChunkerSkill
        print("✅ SmartChunkerSkill 导入成功")

        chunker = SmartChunkerSkill()
        print(f"   实例化成功: {chunker}")
    except Exception as e:
        print(f"❌ SmartChunkerSkill 失败: {e}")
        return False

    return True


def test_workflow_imports():
    """测试 Workflow 导入"""
    print("\n" + "="*60)
    print("测试 Workflow 导入")
    print("="*60)

    try:
        from src.skills import WorkflowManager
        print("✅ WorkflowManager 导入成功")

        manager = WorkflowManager()
        print(f"   实例化成功: {manager}")
    except Exception as e:
        print(f"❌ WorkflowManager 失败: {e}")
        return False

    return True


def test_direct_imports():
    """测试直接从子模块导入（扁平化后，直接从 skills 导入）"""
    print("\n" + "="*60)
    print("测试直接从子模块导入")
    print("="*60)

    try:
        from src.skills.router_file import FileRouterSkill
        print("✅ 从 router_file 导入成功")
    except ImportError as e:
        print(f"❌ 从 router_file 导入失败: {e}")
        return False

    try:
        from src.skills.parser_native import NativeParserSkill
        from src.skills.parser_pdf_ocr import OCRParserSkill
        print("✅ 从 parser 模块导入成功")
    except ImportError as e:
        print(f"❌ 从 parser 模块导入失败: {e}")
        return False

    try:
        from src.skills.chunk_smart import SmartChunkerSkill
        print("✅ 从 chunk_smart 导入成功")
    except ImportError as e:
        print(f"❌ 从 chunk_smart 导入失败: {e}")
        return False

    try:
        from src.skills.workflow_manager import WorkflowManager
        print("✅ 从 workflow 导入成功")
    except ImportError as e:
        print(f"❌ 从 workflow 导入失败: {e}")
        return False

    return True


def test_skill_registry():
    """测试 Skill 注册功能"""
    print("\n" + "="*60)
    print("测试 Skill 注册功能")
    print("="*60)

    try:
        from src.skills import SkillRegistry, FileRouterSkill

        # 创建 Skill（应该自动注册）
        router = FileRouterSkill()

        # 列出所有注册的 Skills
        registered_skills = SkillRegistry.list_skills()
        print(f"✅ 已注册的 Skills: {registered_skills}")

        # 获取特定 Skill
        skill = SkillRegistry.get_skill("FileRouterSkill")
        if skill:
            print(f"✅ 成功获取 FileRouterSkill: {skill}")
        else:
            print("⚠️  FileRouterSkill 未注册")

    except Exception as e:
        print(f"❌ Skill 注册测试失败: {e}")
        return False

    return True


def test_backward_compatibility():
    """测试向后兼容性"""
    print("\n" + "="*60)
    print("测试向后兼容性（旧代码是否仍能工作）")
    print("="*60)

    # 模拟旧代码的导入方式
    try:
        from src.skills import (
            FileRouterSkill,
            NativeParserSkill,
            OCRParserSkill,
            SmartChunkerSkill,
            WorkflowManager
        )
        print("✅ 旧的导入方式仍然有效")
        print("✅ 向后兼容性测试通过")
    except ImportError as e:
        print(f"❌ 向后兼容性测试失败: {e}")
        return False

    return True


def main():
    """运行所有测试"""
    print("\n" + "="*60)
    print("Skill 系统重构 - 导入测试")
    print("="*60)

    results = []

    # 运行所有测试
    results.append(("基础导入", test_basic_imports()))
    results.append(("Classifier 导入", test_classifier_imports()))
    results.append(("Parser 导入", test_parser_imports()))
    results.append(("Transformer 导入", test_transformer_imports()))
    results.append(("Workflow 导入", test_workflow_imports()))
    results.append(("直接子模块导入", test_direct_imports()))
    results.append(("Skill 注册", test_skill_registry()))
    results.append(("向后兼容性", test_backward_compatibility()))

    # 汇总结果
    print("\n" + "="*60)
    print("测试结果汇总")
    print("="*60)

    passed = 0
    failed = 0

    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
        else:
            failed += 1

    print("\n" + "="*60)
    print(f"总计: {passed + failed} 个测试")
    print(f"通过: {passed}")
    print(f"失败: {failed}")
    print("="*60)

    if failed == 0:
        print("\n🎉 所有测试通过！Skill 系统重构成功！")
        return True
    else:
        print(f"\n⚠️  有 {failed} 个测试失败，请检查错误信息")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
