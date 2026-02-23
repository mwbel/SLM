#!/usr/bin/env python3
"""快速测试 API 配置加载"""

import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

try:
    print("1. 导入 APIManagerSkill...")
    from src.skills import APIManagerSkill
    print("   ✅ 导入成功")

    print("\n2. 加载配置文件...")
    manager = APIManagerSkill(config_file='config/api_config.json')
    print("   ✅ 配置加载成功")

    print("\n3. 获取可用 API...")
    api = manager.get_available_api('gemini')
    if api:
        print(f"   ✅ 获取成功: {api['name']}")
        print(f"   模型: {api['model']}")
    else:
        print("   ❌ 未获取到 API")

    print("\n4. 测试轮询...")
    for i in range(3):
        api = manager.get_available_api('gemini')
        if api:
            print(f"   第 {i+1} 次: {api['name']}")

    print("\n✅ 所有测试通过！")

except Exception as e:
    print(f"\n❌ 错误: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
