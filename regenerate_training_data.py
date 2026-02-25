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
    """重新生成训练数据，增加数量"""

    print("=" * 70)
    print("重新生成训练数据 - 增加数据量")
    print("=" * 70)

    # 原始PDF文档
    pdf_path = "docs/报销细则.pdf"

    # 输出路径
    output_path = "data/报销细则_distilled_expanded.jsonl"

    # 数据蒸馏器
    distiller = DataDistiller()

    print(f"\n正在处理文档: {pdf_path}")
    print(f"输出文件: {output_path}")
    print(f"生成策略: 增加每个chunk的问答对数量\n")

    # 智能分块处理
    # 目标：生成 500-1000 条数据
    # 策略：减小chunk_size，增加num_pairs_per_chunk

    target_pairs = 800  # 目标生成800条
    pairs_per_chunk = 20  # 每个chunk生成20条（之前是15条）
    chunk_size = 1500  # chunk大小设为1500字符（比之前更小，产生更多chunk）
    overlap = 200  # 重叠200字符

    print(f"参数配置:")
    print(f"  目标生成数量: {target_pairs}")
    print(f"  每块生成问答: {pairs_per_chunk}")
    print(f"  分块大小: {chunk_size} 字符")
    print(f"  重叠大小: {overlap} 字符")

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
        print(f"\n原始数据量: 217 条")
        print(f"新生成数据量: {data_count} 条")
        print(f"增加: {data_count - 217} 条 ({(data_count - 217) / 217 * 100:.1f}%)")
        print(f"\n数据文件: {result_path}")

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
