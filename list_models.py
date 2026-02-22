"""列出可用的Gemini模型"""

from google import genai

# 使用第一个API密钥
api_key = "AIzaSyBxsxg8_9gUOrtcJ-4lmxsOo9EeKznFzJs"
client = genai.Client(api_key=api_key)

print("可用的Gemini模型：\n")
try:
    models = client.models.list()
    for model in models:
        if 'gemini' in model.name.lower():
            print(f"- {model.name}")
            print(f"  显示名称: {model.display_name if hasattr(model, 'display_name') else 'N/A'}")
            print()
except Exception as e:
    print(f"错误: {e}")
    import traceback
    traceback.print_exc()
