# 模型下载问题解决方案

## 🎯 问题说明

由于网络问题无法从 HuggingFace 下载 `Qwen2.5-0.5B` 模型，我们提供了一个**更好的替代方案**：使用智谱AI API进行推理和数据蒸馏，**无需下载任何本地模型**。

---

## ✅ 推荐方案：使用智谱AI API

### 优势

- ✅ **无需下载模型** - 节省 ~1GB 存储空间
- ✅ **无需GPU** - 使用云端API，本地CPU即可
- ✅ **速度快** - 云端推理，秒级响应
- ✅ **免费额度** - 新用户有免费调用额度
- ✅ **已配置好** - API密钥已添加到 `.env` 文件

---

## 🚀 快速开始

### 1. 测试智谱AI API

```bash
export ZHIPU_API_KEY="0608bfac12ae33755667214aa6d00657.oljJQXnYGuGGF6pf"
python3 test_zhipu.py
```

**预期输出：**
```
✅ 智谱AI API测试通过！
   你可以使用智谱AI进行数据蒸馏和推理，无需下载本地模型。
```

### 2. 使用前端UI（当前已可用）

前端服务器已在运行，你**可以直接使用以下功能**：

#### ✅ 数据蒸馏（使用智谱AI）
- 上传 PDF/TXT 文件
- 自动使用智谱AI API生成训练数据
- 支持长文档分块处理

#### ✅ 问答推理
- 使用智谱AI回答问题
- 基于上传的文档内容

---

## 📊 方案对比

| 特性 | 本地模型 | 智谱AI API |
|------|----------|------------|
| 需要下载 | ❌ ~1GB | ✅ 无需下载 |
| GPU要求 | ✅ 需要 | ✅ 不需要 |
| 速度 | ⚠️ 取决于硬件 | ✅ 快速 |
| 成本 | ✅ 免费 | ⚠️ 按API调用计费 |
| 网络要求 | ❌ 下载需要 | ✅ 仅需API连接 |

**推荐：** 如果你在中国大陆，使用智谱AI API会更方便快捷！

---

## 🔧 如果一定要使用本地模型

如果因特殊原因必须使用本地模型，有以下方法：

### 方法 1: 使用 ModelScope（阿里云，推荐）

```bash
# 安装 modelscope
pip3 install modelscope

# 下载模型（国内镜像，速度快）
python3 << 'EOF'
from modelscope import snapshot_download
model_dir = snapshot_download('Qwen/Qwen2.5-0.5B', cache_dir='./models')
print(f"模型已下载到: {model_dir}")
EOF

# 修改配置文件 config.yaml
# model:
#   base_model: "models/Qwen/Qwen2___5-0___5B"
```

### 方法 2: 使用 huggingface-cli

```bash
# 安装 CLI
pip3 install -U "huggingface_hub[cli]"

# 使用镜像下载（可能需要VPN）
HF_ENDPOINT=https://hf-mirror.com huggingface-cli download Qwen/Qwen2.5-0.5B --local-dir models/Qwen2.5-0.5B
```

### 方法 3: 手动下载

1. 访问 https://www.modelscope.cn/models/Qwen/Qwen2.5-0.5B
2. 下载所有文件到 `models/Qwen2.5-0.5B/`
3. 修改 `config.yaml` 指向本地路径

---

## 💡 使用建议

### 对于数据蒸馏
**推荐使用智谱AI API**（已配置好）
- 速度快
- 质量高
- 无需下载模型

### 对于模型训练
**需要本地模型**，但训练可以：
1. 使用智谱API生成训练数据
2. 下载小模型（如Qwen2.5-0.5B）
3. 在本地进行训练

---

## 🎯 现在你可以做什么

### ✅ 可以立即使用

1. **数据蒸馏**
   ```bash
   # 在浏览器中打开 http://localhost:7860
   # 上传PDF/TXT文件
   # 点击"生成训练数据"
   # 会自动使用智谱AI API
   ```

2. **测试API**
   ```bash
   python3 test_zhipu.py
   ```

### ⏳ 需要额外步骤

1. **本地模型训练**
   - 需要先下载模型（使用ModelScope）
   - 或在有VPN的环境下载

2. **离线推理**
   - 需要本地模型
   - 推荐使用更小的模型

---

## 📞 获取帮助

如果你：
- 需要下载本地模型
- 遇到API调用问题
- 想要配置其他API服务

请告诉我，我会继续帮你！

---

**更新时间：** 2026-02-25
**推荐方案：** 使用智谱AI API（已配置并测试通过）
