# Skill 系统依赖安装指南

## 基础依赖

```bash
# 文档解析
pip install PyMuPDF        # PDF 解析
pip install python-docx    # Word 文档解析
```

## OCR 依赖（根据需要选择）

### 方案 1: PaddleOCR（推荐，开源免费）

```bash
pip install paddleocr
pip install paddlepaddle    # CPU 版本
# 或
pip install paddlepaddle-gpu  # GPU 版本（需要 CUDA）
```

### 方案 2: MinerU（高质量 PDF OCR）

```bash
pip install magic-pdf
```

## 可选依赖

```bash
# 图片处理
pip install Pillow

# 异步支持（Python 3.7+ 已内置）
# asyncio 已包含在标准库中
```

## 验证安装

运行以下脚本验证依赖是否正确安装：

```python
import sys

def check_dependencies():
    """检查依赖是否安装"""
    dependencies = {
        'fitz': 'PyMuPDF',
        'docx': 'python-docx',
        'paddleocr': 'paddleocr (可选)',
        'magic_pdf': 'magic-pdf (可选)',
        'PIL': 'Pillow (可选)'
    }

    print("检查依赖安装状态:\n")

    for module, name in dependencies.items():
        try:
            __import__(module)
            print(f"✅ {name} - 已安装")
        except ImportError:
            if '可选' in name:
                print(f"⚠️  {name} - 未安装（可选）")
            else:
                print(f"❌ {name} - 未安装（必需）")

    print(f"\nPython 版本: {sys.version}")

if __name__ == "__main__":
    check_dependencies()
```

保存为 `check_deps.py` 并运行：
```bash
python check_deps.py
```
