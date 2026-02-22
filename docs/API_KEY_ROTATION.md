# API密钥轮换使用指南

## 功能说明

API密钥轮换器可以自动管理多个Gemini API密钥，当一个密钥配额用完时自动切换到下一个可用密钥。

## 特性

- 自动检测配额错误并切换密钥
- 支持密钥冷却时间（默认60分钟）
- 记录每个密钥的使用情况和错误次数
- 提供详细的状态报告
- 错误次数过多自动禁用密钥

## 使用方法

### 1. 使用默认密钥池（推荐）

```python
from src.data_prep import DataDistiller

# 自动使用预配置的9个API密钥
distiller = DataDistiller()

# 处理文件
output = distiller.process_file("data/document.pdf", num_pairs=15)

# 查看密钥使用状态
print(distiller.get_status_report())
```

### 2. 使用自定义密钥列表

```python
custom_keys = [
    "YOUR_API_KEY_1",
    "YOUR_API_KEY_2",
    "YOUR_API_KEY_3"
]

distiller = DataDistiller(api_keys=custom_keys, use_rotation=True)
```

### 3. 单密钥模式（不使用轮换）

```python
distiller = DataDistiller(
    api_key="YOUR_SINGLE_API_KEY",
    use_rotation=False
)
```

### 4. 直接使用轮换器

```python
from src.utils import APIKeyRotator

# 创建轮换器
rotator = APIKeyRotator(
    api_keys=["KEY1", "KEY2", "KEY3"],
    cooldown_minutes=60
)

# 获取当前密钥
current_key = rotator.get_current_key()

# 标记成功
rotator.mark_success()

# 标记配额用完（自动切换）
new_key = rotator.mark_quota_exceeded()

# 查看状态
print(rotator.get_status_report())
```

## 配额管理

### 免费层级限制
- Gemini 1.5 Flash 免费层：15 RPM (每分钟请求数)
- 每个密钥独立计算配额

### 轮换策略
1. 当检测到配额错误（429、quota、resource_exhausted）时自动切换
2. 被切换的密钥进入冷却期（默认60分钟）
3. 冷却期结束后自动恢复可用
4. 错误次数超过3次的密钥会被暂时禁用

## 状态报告示例

```
=== API密钥状态报告 ===

密钥 #1: AIzaSyBxsxg8_9gUOrtc...
  状态: ✓ 可用
  总调用次数: 15
  错误次数: 0
  最后使用: 2026-02-22 12:30:45

密钥 #2: AIzaSyDGG3Q5i38wBQN9...
  状态: ✗ 不可用
  总调用次数: 20
  错误次数: 0
  最后使用: 2026-02-22 12:25:30
  冷却剩余: 45 分钟

当前使用: 密钥 #1
==============================
```

## 最佳实践

1. **批量处理**：使用默认密钥池可以连续处理多个文档
2. **监控状态**：定期查看状态报告了解密钥使用情况
3. **合理配置**：根据实际需求调整冷却时间
4. **错误处理**：捕获所有密钥用完的异常

```python
try:
    distiller = DataDistiller()
    output = distiller.process_file("data/large_doc.pdf")
except RuntimeError as e:
    print(f"所有密钥配额已用完: {e}")
    # 等待冷却或添加更多密钥
```

## 预配置密钥列表

项目已预配置9个免费API密钥，位于 `src/utils/api_key_rotator.py` 的 `DEFAULT_API_KEYS` 变量中。

如需更新密钥列表，直接修改该变量即可。
