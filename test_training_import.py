#!/usr/bin/env python3
"""测试训练模块导入和基本功能"""

import sys
from pathlib import Path

# 添加src到路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_training_module():
    """测试训练模块"""
    print("=" * 70)
    print("测试训练模块")
    print("=" * 70)

    try:
        # 测试导入
        print("\n1. 导入训练模块...")
        from training import Trainer
        print("   ✓ Trainer 导入成功")

        # 测试依赖
        print("\n2. 检查依赖包...")
        import torch
        print(f"   ✓ PyTorch 版本: {torch.__version__}")
        print(f"   ✓ CUDA 可用: {torch.cuda.is_available()}")

        import transformers
        print(f"   ✓ Transformers 版本: {transformers.__version__}")

        from peft import LoraConfig, get_peft_model
        print("   ✓ PEFT 导入成功")

        import bitsandbytes
        print(f"   ✓ BitsAndBytes 版本: {bitsandbytes.__version__}")

        # 测试配置
        print("\n3. 测试配置对象...")
        from data_prep import DataDistiller
        print("   ✓ DataDistiller 导入成功")

        print("\n" + "=" * 70)
        print("✅ 所有测试通过！训练模块已就绪。")
        print("=" * 70)

        return True

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_training_module()
    sys.exit(0 if success else 1)
