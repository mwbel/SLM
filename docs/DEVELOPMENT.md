# 开发指南

## 环境配置

### 1. 创建虚拟环境
```bash
conda create -n slm python=3.10
conda activate slm
```

### 2. 安装依赖
```bash
pip install -r requirements.txt
```

### 3. 配置文件
编辑 `config.yaml` 设置模型和训练参数

## 开发规范

### 代码风格
- 遵循 PEP 8 规范
- 使用类型注解
- 添加文档字符串

### 测试
```bash
# 运行所有测试
python -m pytest tests/

# 运行特定测试
python -m pytest tests/test_data_prep.py
```

### 提交规范
- feat: 新功能
- fix: 修复bug
- docs: 文档更新
- test: 测试相关
- refactor: 重构代码

## 模块开发

### 添加新功能
1. 在对应模块创建新文件
2. 实现功能类/函数
3. 添加单元测试
4. 更新文档

### 调试技巧
- 使用日志记录关键信息
- 设置断点调试
- 检查配置文件

## 常见问题

### CUDA内存不足
- 减小batch_size
- 使用更小的模型
- 启用梯度检查点

### 训练速度慢
- 检查GPU利用率
- 优化数据加载
- 调整num_workers
