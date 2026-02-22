"""测试数据蒸馏功能"""

import sys
from pathlib import Path

# 添加src到路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

from data_prep import DataDistiller

def test_distiller():
    """测试数据蒸馏器"""

    print("=== 测试数据蒸馏功能 ===\n")

    # 初始化蒸馏器（使用默认密钥池）
    print("初始化数据蒸馏器...")
    distiller = DataDistiller()
    print(f"✓ 已加载 {len(distiller.rotator.api_keys)} 个API密钥\n")

    # 测试文件路径
    test_file = "/Users/Min369/Documents/同步空间/Manju/Projects/垂直小模型/domain_knowledge/报销细则_21页.pdf"

    if not Path(test_file).exists():
        print(f"✗ 测试文件不存在: {test_file}")
        return

    print(f"测试文件: {test_file}")
    print("开始处理...\n")

    try:
        # 处理文件
        output_path = distiller.process_file(
            file_path=test_file,
            output_dir="data",
            num_pairs=10
        )

        print(f"\n✓ 处理成功！")
        print(f"输出文件: {output_path}")

        # 读取并显示前3条
        print("\n=== 生成数据预览 ===")
        with open(output_path, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f.readlines()[:3], 1):
                print(f"\n[{i}] {line.strip()}")

        # 显示API密钥状态
        print("\n" + distiller.get_status_report())

    except Exception as e:
        print(f"\n✗ 处理失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_distiller()
