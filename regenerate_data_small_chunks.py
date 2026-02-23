"""重新生成训练数据 - 使用更小的分块尺寸"""

import sys
from pathlib import Path

# 添加src目录到路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

from data_prep.distiller import DataDistiller

if __name__ == "__main__":
    print("="*60)
    print("重新生成训练数据 - 使用更小的分块尺寸")
    print("="*60)

    # 初始化蒸馏器（使用默认API密钥池）
    distiller = DataDistiller()

    # 文档路径（使用绝对路径）
    pdf_path = "/Users/Min369/Documents/同步空间/Manju/Projects/垂直小模型/domain_knowledge/高校财务报销/报销细则.pdf"

    # 使用更小的分块尺寸重新处理
    print(f"\n📄 处理文档: {pdf_path}")
    print(f"📊 新参数:")
    print(f"   - chunk_size: 4500 字符 (原15000)")
    print(f"   - overlap: 500 字符")
    print(f"   - num_pairs_per_chunk: 30")
    print(f"\n预期效果: 生成更多训练样本 (目标 300+ 组)\n")

    output_file = distiller.process_file_chunked(
        file_path=pdf_path,
        output_dir="data",
        num_pairs_per_chunk=30,
        chunk_size=4500,  # 从15000降到4500
        overlap=500
    )

    print(f"\n✅ 处理完成！")
    print(f"📁 输出文件: {output_file}")

    # 显示API使用状态
    print(f"\n{distiller.get_status_report()}")
