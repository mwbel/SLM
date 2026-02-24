# API密钥配置说明

## 配置方法

### 方法1：使用配置文件（推荐）

1. 复制示例文件：
```bash
cp config/api_keys.json.example config/api_keys.json
```

2. 编辑 `config/api_keys.json`，填入你的API密钥：
```json
{
  "gemini_keys": [
    "your-gemini-api-key-1",
    "your-gemini-api-key-2"
  ],
  "zhipu_key": "your-zhipu-api-key"
}
```

3. **重要**：`api_keys.json` 已被加入 `.gitignore`，不会被提交到Git

### 方法2：使用环境变量

```bash
# 设置Gemini API密钥（多个密钥用逗号分隔）
export GEMINI_API_KEYS="key1,key2,key3"

# 运行应用
python src/ui/app.py
```

## 默认行为

如果没有配置Gemini API密钥，系统会自动使用智谱AI（GLM-4-Flash）进行数据蒸馏。

## 安全提示

⚠️ **永远不要将API密钥提交到Git仓库！**

- ❌ 不要硬编码在代码中
- ❌ 不要提交到GitHub等公开仓库
- ✅ 使用配置文件或环境变量
- ✅ 确保配置文件在 `.gitignore` 中
