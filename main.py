"""SLM Trainer 主入口"""

import sys
from pathlib import Path

# 添加src到路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

from ui import create_ui

def main():
    """启动应用"""
    app = create_ui()
    # 允许访问项目根目录下的文件（包括 domain_knowledge）
    project_root = Path(__file__).parent.parent
    app.launch(
        server_name="0.0.0.0", 
        server_port=7860,
        allowed_paths=[str(project_root)]
    )

if __name__ == "__main__":
    main()
