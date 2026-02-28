#!/usr/bin/env python3
"""
重新生成更多训练数据
通过增加 num_pairs 参数来生成更多问答对
"""

import sys
from pathlib import Path

# 添加src到路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

from data_prep import DataDistiller


def regenerate_data():
    """重新生成训练数据 - 使用优化后的配置"""

    print("=" * 70)
    print("🔄 重新生成训练数据 - 优化版本")
    print("=" * 70)
    print("   ✅ 强调数字类信息提取")
    print("   ✅ 增加样本密度 (15对/块)")
    print("   ✅ 优化提示词")

    # 原始PDF文档
    pdf_path = "docs/报销细则.pdf"

    # 输出路径
    output_path = "data/报销细则_distilled_optimized.jsonl"

    # 数据蒸馏器
    distiller = DataDistiller()

    print(f"\n正在处理文档: {pdf_path}")
    print(f"输出文件: {output_path}")
    print(f"生成策略: 使用优化后的蒸馏提示词\n")

    # 智能分块处理（优化版）
    # 目标：生成高质量、强调数字的训练数据
    # 策略：减小chunk_size以产生更多块，使用智谱AI（优化后提示词）

    target_pairs = 180  # 目标生成180条（使用智谱AI）
    pairs_per_chunk = 15  # 每个chunk生成15条（优化后的推荐值）
    chunk_size = 5000  # chunk大小5000字符（减小以产生更多块，约11-12块）
    overlap = 300  # 重叠300字符

    print(f"参数配置:")
    print(f"  目标生成数量: {target_pairs}")
    print(f"  每块生成问答: {pairs_per_chunk} (优化后)")
    print(f"  分块大小: {chunk_size} 字符 (减小以增加块数)")
    print(f"  重叠大小: {overlap} 字符")
    print(f"  使用API: 智谱AI GLM-4-Flash (优化提示词)")

    try:
        # 执行分块处理
        result_path = distiller.process_file_chunked(
            file_path=pdf_path,
            output_dir=str(Path(output_path).parent),
            num_pairs_per_chunk=pairs_per_chunk,
            chunk_size=chunk_size,
            overlap=overlap,
        )

        # 统计生成的数据量
        import json
        data_count = 0
        with open(result_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    data_count += 1

        print("\n" + "=" * 70)
        print("✅ 数据生成完成！")
        print("=" * 70)
        print(f"\n原始数据量: 863 条")
        print(f"新生成数据量: {data_count} 条")
        if data_count > 863:
            print(f"增加: {data_count - 863} 条 ({(data_count - 863) / 863 * 100:.1f}%)")
        print(f"\n数据文件: {result_path}")
        print(f"\n💡 优化内容:")
        print(f"   - 强调数字类信息提取（30%+数字问题）")
        print(f"   - 增加样本密度（15对/块）")
        print(f"   - 优化蒸馏提示词")

        # 显示前3条预览
        print("\n" + "=" * 70)
        print("数据预览（前3条）:")
        print("=" * 70)
        with open(result_path, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f):
                if i >= 3:
                    break
                data = json.loads(line)
                print(f"\n【第{i+1}条】")
                print(f"问题: {data['instruction'][:80]}...")
                print(f"回答: {data['output'][:100]}...")

        print("\n" + "=" * 70)
        print("下一步：使用新数据重新训练模型")
        print("=" * 70)
        print("\n命令：")
        print("  python3 train_with_new_data.py")

        return result_path

    except Exception as e:
        print(f"\n❌ 生成失败: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    regenerate_data()
