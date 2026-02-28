"""
重新蒸馏数据 - 使用温度0.1重新生成训练数据
"""

import sys
from pathlib import Path

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from src.data_prep.distiller import DataDistiller


def main():
    print("=" * 60)
    print("重新蒸馏数据 - 使用温度0.1")
    print("=" * 60)

    # 初始化蒸馏器
    print("\n📋 初始化蒸馏器...")
    distiller = DataDistiller()
    print(f"✅ 蒸馏器初始化完成")

    # 查看API密钥状态
    print(f"\n🔑 API密钥状态:")
    print(distiller.get_status_report())

    # 处理文档
    input_file = "docs/报销细则.pdf"
    output_dir = "data"

    print(f"\n📄 开始处理文档: {input_file}")
    print(f"   输出目录: {output_dir}")
    print(f"   温度设置: 0.1（已降低以提高数字准确性）")

    try:
        # 使用分块处理（适用于长文档）
        print(f"\n✂️  使用分块处理模式...")
        output_file = distiller.process_file_chunked(
            file_path=input_file,
            output_dir=output_dir,
            num_pairs_per_chunk=30,  # 每个块生成30组对话对
            chunk_size=15000,  # 每块15000字符
            overlap=500,  # 块之间重叠500字符
        )

        print(f"\n{'='*60}")
        print(f"✅ 重新蒸馏完成！")
        print(f"   输出文件: {output_file}")
        print(f"{'='*60}")

        # 统计生成的数据
        import json

        with open(output_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
            total_pairs = len(lines)

            # 统计数字类问题
            import re

            numeric_count = 0
            for line in lines:
                data = json.loads(line)
                instruction = data.get("instruction", "")
                output = data.get("output", "")
                if re.search(r"\d+", instruction) or re.search(r"\d+", output):
                    numeric_count += 1

            numeric_ratio = (
                (numeric_count / total_pairs * 100) if total_pairs > 0 else 0
            )

        print(f"\n📊 数据统计:")
        print(f"   总对话对数: {total_pairs}")
        print(f"   数字类问题: {numeric_count} ({numeric_ratio:.1f}%)")

        if numeric_ratio >= 30:
            print(f"   ✅ 数字类问题占比达标（≥30%）")
        else:
            print(f"   ⚠️ 数字类问题占比偏低（目标≥30%）")

        print(f"\n🔑 最终API密钥状态:")
        print(distiller.get_status_report())

    except Exception as e:
        print(f"\n❌ 处理失败: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
