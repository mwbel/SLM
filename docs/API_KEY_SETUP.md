# API Keys 配置指南

## 🔒 安全变更

为了防止 API keys 泄露，项目已从配置文件方式改为**环境变量方式**。

## ✅ 已完成的更改

### 1. 代码修改
- ✅ `src/utils/api_key_rotator.py` - 修改为从环境变量读取 API keys
- ✅ `src/skills/api_manager.py` - 已支持环境变量
- ✅ `src/data_prep/distiller.py` - 使用环境变量

### 2. 配置文件清理
- ✅ `config/api_config.json` - 清除硬编码的 API keys
- ✅ `.gitignore` - 添加 `.env` 和敏感配置文件

### 3. 新增文件
- ✅ `.env.example` - 环境变量配置示例
- ✅ `test_env_config.py` - 环境变量测试脚本

---

## 🚀 快速开始

### 方式 1: 使用 .env 文件（推荐）

1. **复制示例文件**
```bash
cp .env.example .env
```

2. **编辑 .env 文件，添加你的 API keys**
```bash
# Gemini API Keys (支持多个)
GEMINI_API_KEY_1=your_first_gemini_key_here
GEMINI_API_KEY_2=your_second_gemini_key_here
GEMINI_API_KEY_3=your_third_gemini_key_here

# 或者使用单个 key
GEMINI_API_KEY=your_gemini_key_here

# 或者使用逗号分隔
GEMINI_API_KEYS=key1,key2,key3
```

3. **加载环境变量**
```bash
# Linux/Mac
source .env

# 或者使用 export
export GEMINI_API_KEY_1='your-key-here'
```

### 方式 2: 直接使用 export 命令

```bash
# 单个 key
export GEMINI_API_KEY='your-key-here'

# 多个 keys (编号)
export GEMINI_API_KEY_1='your-first-key'
export GEMINI_API_KEY_2='your-second-key'
export GEMINI_API_KEY_3='your-third-key'

# 多个 keys (逗号分隔)
export GEMINI_API_KEYS='key1,key2,key3'
```

### 方式 3: 在 Python 代码中设置

```python
import os
os.environ['GEMINI_API_KEY_1'] = 'your-key-here'
```

---

## 🧪 测试配置

运行测试脚本验证配置是否正确：

```bash
python3 test_env_config.py
```

**预期输出：**
```
======================================================================
环境变量配置测试
======================================================================

📝 检查 Gemini API Keys...
  ✓ 找到 GEMINI_API_KEY_1: AIzaSyBxsxg8...zJs
✅ 总共找到 1 个 Gemini API key(s)

📦 测试导入 APIKeyRotator...
  ✓ DEFAULT_API_KEYS 已加载: 1 个 keys
  ✓ APIKeyRotator 创建成功

📦 测试导入 DataDistiller...
  ✓ DataDistiller 创建成功
  ✓ API key 轮换器已启用

✅ 环境变量配置测试通过！
🎉 所有测试通过！可以开始使用了。
```

---

## 🔑 获取 API Keys

### Gemini API
1. 访问 [Google AI Studio](https://makersuite.google.com/app/apikey)
2. 登录 Google 账号
3. 点击 "Create API key"
4. 复制 API key

### DeepSeek API
1. 访问 [DeepSeek Platform](https://platform.deepseek.com/)
2. 注册/登录账号
3. 在 API Keys 页面创建新密钥

### 智谱 AI
1. 访问 [智谱 AI 开放平台](https://open.bigmodel.cn/)
2. 注册/登录账号
3. 在 API 密钥页面创建新密钥

---

## 📋 环境变量格式说明

项目支持以下三种格式：

### 格式 1: 编号分隔（推荐用于多个 keys）
```bash
GEMINI_API_KEY_1=key1
GEMINI_API_KEY_2=key2
GEMINI_API_KEY_3=key3
```

### 格式 2: 逗号分隔
```bash
GEMINI_API_KEYS=key1,key2,key3
```

### 格式 3: 单个 key
```bash
GEMINI_API_KEY=key1
```

**优先级：** 格式 1 > 格式 2 > 格式 3

---

## ⚠️ 安全注意事项

1. **永远不要提交 .env 文件到 Git**
   - `.env` 已在 `.gitignore` 中排除
   - 提交前检查：`git status`

2. **定期轮换 API keys**
   - 建议每月更换一次
   - 如果怀疑泄露，立即更换

3. **限制 API key 权限**
   - 只启用必要的 API
   - 设置配额限制

4. **使用不同的 keys**
   - 开发/测试/生产使用不同的 keys
   - 便于追踪和隔离问题

---

## 🔄 从旧配置迁移

如果你之前使用 `config/api_config.json`：

1. **导出现有的 keys**
```bash
cat config/api_config.json
```

2. **创建 .env 文件**
```bash
cp .env.example .env
```

3. **将 keys 填入 .env**
```bash
GEMINI_API_KEY_1=你的第一个key
GEMINI_API_KEY_2=你的第二个key
# ...
```

4. **测试新配置**
```bash
python3 test_env_config.py
```

5. **删除旧配置（可选）**
```bash
rm config/api_config.json
```

---

## 🐛 故障排查

### 问题 1: 未找到 API keys
```
⚠️  未找到任何 Gemini API keys！
```
**解决方案：**
- 检查环境变量是否正确设置：`echo $GEMINI_API_KEY_1`
- 确保已运行 `source .env`
- 检查变量名拼写

### 问题 2: API key 无效
```
✗ API key 无效
```
**解决方案：**
- 验证 key 是否正确复制
- 检查 key 是否已过期
- 确认 key 已启用 Gemini API

### 问题 3: 导入错误
```
ImportError: cannot import name 'genai' from 'google'
```
**解决方案：**
```bash
pip install google-genai
```

---

## 📚 相关文件

- `.env.example` - 环境变量配置示例
- `test_env_config.py` - 环境变量测试脚本
- `src/utils/api_key_rotator.py` - API key 轮换器
- `config/api_config.json` - 配置文件（已清理）

---

## 📞 获取帮助

如有问题，请：
1. 查看项目 README.md
2. 运行 `python3 test_env_config.py` 诊断
3. 检查 GitHub Issues

---

**最后更新：** 2026-02-25
**版本：** 1.0.0
