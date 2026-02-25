#!/usr/bin/env python3
"""测试训练器初始化"""

import sys
from pathlib import Path

# 添加src到路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_trainer_init():
    """测试训练器初始化"""
    print("=" * 70)
    print("测试训练器初始化")
    print("=" * 70)

    try:
        from training import Trainer
        import yaml

        # 加载配置
        print("\n1. 加载配置...")
        config_path = Path("config.yaml")
        with open(config_path) as f:
            config = yaml.safe_load(f)

        model_name = config['model']['base_model']
        print(f"   模型路径: {model_name}")
        print(f"   配置加载成功")

        print("\n2. 初始化训练器...")
        trainer = Trainer(model_name, config)
        print("   ✓ 训练器初始化成功")

        print("\n3. 检查模型...")
        print(f"   模型类型: {type(trainer.model).__name__}")
        print(f"   设备: {trainer.model.device}")

        print("\n" + "=" * 70)
        print("✅ 训练器初始化测试通过！")
        print("=" * 70)
        print("\n训练功能已就绪！")

        return True

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_trainer_init()
    sys.exit(0 if success else 1)
