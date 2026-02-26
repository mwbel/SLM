#!/usr/bin/env python3
"""
测试训练环境
验证模型、数据和依赖是否正确配置
"""

import sys
import json
from pathlib import Path
import yaml


def check_model():
    """检查模型文件"""
    print("\n🔍 检查模型...")

    config_path = Path(__file__).parent / "config.yaml"
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    model_path = Path(config['model']['base_model'])

    # 检查模型路径
    if model_path.exists():
        print(f"✅ 模型路径存在: {model_path}")

        # 检查必要文件
        required_files = [
            "config.json",
            "tokenizer.json",
            "tokenizer_config.json"
        ]

        # 检查模型权重文件
        has_safetensors = False
        for file in model_path.glob("*.safetensors"):
            has_safetensors = True
            size_gb = file.stat().st_size / (1024**3)
            print(f"   ✓ {file.name} ({size_gb:.2f} GB)")

        if not has_safetensors:
            print("   ⚠️  未找到.safetensors文件")

        # 检查配置文件
        for file_name in required_files:
            file_path = model_path / file_name
            if file_path.exists():
                print(f"   ✓ {file_name}")
            else:
                print(f"   ✗ 缺少 {file_name}")

        return True
    else:
        print(f"❌ 模型路径不存在: {model_path}")
        print(f"   请先运行: python3 download_qwen_3b.py")
        return False


def check_data():
    """检查训练数据"""
    print("\n🔍 检查训练数据...")

    data_path = Path(__file__).parent / "data" / "报销细则_distilled_chunked.jsonl"

    if not data_path.exists():
        print(f"❌ 数据文件不存在: {data_path}")
        return False

    print(f"✅ 数据文件存在: {data_path}")

    # 检查数据格式
    try:
        with open(data_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        print(f"   总行数: {len(lines)}")

        # 验证JSON格式
        valid_count = 0
        for i, line in enumerate(lines[:5]):  # 检查前5行
            try:
                data = json.loads(line.strip())
                if 'instruction' in data and 'output' in data:
                    valid_count += 1
            except json.JSONDecodeError:
                print(f"   ⚠️  第{i+1}行格式错误")

        if valid_count > 0:
            print(f"   ✅ 数据格式正确（前5行验证通过）")

            # 显示一个样本
            sample = json.loads(lines[0].strip())
            print(f"\n   示例样本:")
            print(f"   问题: {sample['instruction'][:60]}...")
            print(f"   回答: {sample['output'][:60]}...")

            return True
        else:
            print(f"   ❌ 数据格式错误")
            return False

    except Exception as e:
        print(f"   ❌ 读取数据失败: {e}")
        return False


def check_dependencies():
    """检查依赖包"""
    print("\n🔍 检查依赖包...")

    required_packages = {
        'torch': 'PyTorch',
        'transformers': 'Transformers',
        'peft': 'PEFT (LoRA)',
        'datasets': 'Datasets',
        'yaml': 'PyYAML'
    }

    all_ok = True
    for package, display_name in required_packages.items():
        try:
            __import__(package)
            print(f"   ✅ {display_name}")
        except ImportError:
            print(f"   ❌ {display_name} 未安装")
            all_ok = False

    # 检查GPU/MPS支持
    try:
        import torch
        if torch.cuda.is_available():
            gpu_name = torch.cuda.get_device_name(0)
            print(f"\n   ✅ CUDA GPU: {gpu_name}")
        elif torch.backends.mps.is_available():
            print(f"\n   ✅ Apple MPS (Metal Performance Shaders)")
        else:
            print(f"\n   ⚠️  未检测到GPU加速，将使用CPU（速度较慢）")
    except:
        pass

    return all_ok


def check_config():
    """检查配置文件"""
    print("\n🔍 检查配置文件...")

    config_path = Path(__file__).parent / "config.yaml"

    if not config_path.exists():
        print(f"❌ 配置文件不存在: {config_path}")
        return False

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        print(f"✅ 配置文件格式正确")

        # 检查关键配置
        checks = [
            ('model.base_model', config.get('model', {}).get('base_model')),
            ('model.max_seq_length', config.get('model', {}).get('max_seq_length')),
            ('lora.rank', config.get('lora', {}).get('rank')),
            ('training.num_epochs', config.get('training', {}).get('num_epochs')),
            ('training.learning_rate', config.get('training', {}).get('learning_rate')),
        ]

        all_ok = True
        for key, value in checks:
            if value is not None:
                print(f"   ✓ {key}: {value}")
            else:
                print(f"   ✗ 缺少配置: {key}")
                all_ok = False

        return all_ok

    except Exception as e:
        print(f"❌ 配置文件读取失败: {e}")
        return False


def main():
    """主测试流程"""
    print("=" * 70)
    print("🧪 训练环境测试")
    print("=" * 70)

    results = {
        'config': check_config(),
        'dependencies': check_dependencies(),
        'model': check_model(),
        'data': check_data()
    }

    # 总结
    print("\n" + "=" * 70)
    print("📊 测试总结")
    print("=" * 70)

    all_ok = all(results.values())

    for name, ok in results.items():
        status = "✅ 通过" if ok else "❌ 失败"
        print(f"  {name}: {status}")

    print("\n" + "=" * 70)

    if all_ok:
        print("\n🎉 所有检查通过！")
        print("\n可以开始训练:")
        print("  python3 train_3b_model.py")
        print()
    else:
        print("\n⚠️  部分检查失败，请先解决上述问题")
        print()

    return all_ok


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
