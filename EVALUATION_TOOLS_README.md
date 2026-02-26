# 模型评估工具快速参考

## 🚀 三大评估工具

### 1. 自动化批量评估
```bash
python3 evaluate_model.py
```
**用途**: 全面评估 → 生成报告
**时间**: 约30-40分钟
**输出**: JSON报告 + 控制台详情

### 2. 对比测试
```bash
python3 compare_models.py
```
**用途**: 基座模型 vs 训练后模型
**时间**: 约20-30分钟
**输出**: 对比分析

### 3. 交互式评估
```bash
python3 interactive_eval.py
```
**用途**: 手动测试探索
**时间**: 按需
**输出**: 实时对话

---

## 📊 当前模型评分: **65/100** (⭐⭐⭐ 合格)

| 指标 | 得分 |
|------|------|
| 精确度 | 80.0% |
| 一致性 | 0.500 |
| 多样性 | 0.200 |

---

## 💡 快速命令

```bash
# 快速测试（5分钟）
python3 test_trained_model.py

# 完整评估（30分钟）
python3 evaluate_model.py

# 对比分析（20分钟）
python3 compare_models.py

# 交互测试（按需）
python3 interactive_eval.py
```

---

## 🎯 评估建议

### 日常开发
→ 用 `test_trained_model.py` 快速验证

### 训练完成后
→ 用 `evaluate_model.py` 全面评估

### 优化调参时
→ 用 `compare_models.py` 对比效果

### 上线前
→ 用 `interactive_eval.py` 人工测试

---

## 📈 改进方向

1. **增加数据密度** - 当前7.5样本/页，可提高到15+
2. **调整训练参数** - 降低学习率，增加轮数
3. **针对性优化** - 为数字类问题增加专项训练

---

详细文档: `MODEL_EVALUATION_GUIDE.md`
