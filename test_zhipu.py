#!/usr/bin/env python3
"""测试智谱AI API"""

import os
import sys
from pathlib import Path

# 添加src到路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_zhipuai():
    """测试智谱AI"""
    print("=" * 70)
    print("测试智谱AI API")
    print("=" * 70)

    # 加载API密钥
    api_key = os.environ.get('ZHIPU_API_KEY')
    if not api_key:
        print("\n⚠️ 未找到智谱AI API密钥")
        print("请设置环境变量：export ZHIPU_API_KEY='your-key'")
        return False

    print(f"\n✓ API密钥已加载: {api_key[:20]}...{api_key[-10:]}")

    try:
        # 导入zhipuai
        import zhipuai
        print("✓ zhipuai包导入成功")

        # 创建客户端
        client = zhipuai.ZhipuAI(api_key=api_key)
        print("✓ 客户端创建成功")

        # 测试API调用
        print("\n测试API调用...")
        response = client.chat.completions.create(
            model="glm-4-flash",
            messages=[
                {"role": "user", "content": "你好，请用一句话介绍你自己。"}
            ],
            max_tokens=100
        )

        answer = response.choices[0].message.content
        print(f"✓ API调用成功")
        print(f"  回答: {answer}")
        return True

    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_zhipuai()

    print("\n" + "=" * 70)
    if success:
        print("✅ 智谱AI API测试通过！")
        print("   你可以使用智谱AI进行数据蒸馏和推理，无需下载本地模型。")
    else:
        print("❌ 智谱AI API测试失败")
        print("   请检查API密钥是否正确")
    print("=" * 70)

    sys.exit(0 if success else 1)
