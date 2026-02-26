#!/usr/bin/env python3
"""
交互式人工评估工具
提供友好的命令行界面用于手动测试模型
"""

import sys
from pathlib import Path

# 添加src到路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

from inference import ModelInferencer


class InteractiveEvaluator:
    """交互式评估器"""

    def __init__(self, model_path: str, base_model: str):
        self.model_path = model_path
        self.base_model = base_model
        self.inferencer = None
        self.history = []  # 对话历史

    def load_model(self):
        """加载模型"""
        print("=" * 70)
        print("🚀 初始化交互式评估系统")
        print("=" * 70)
        print(f"\n模型路径: {self.model_path}")
        print(f"基座模型: {self.base_model}\n")

        self.inferencer = ModelInferencer(self.model_path, self.base_model)
        self.inferencer.load_model()
        print("✅ 模型加载完成！\n")

    def show_help(self):
        """显示帮助信息"""
        print("\n" + "=" * 70)
        print("📖 命令帮助")
        print("=" * 70)
        print("  <直接输入问题>     - 向模型提问")
        print("  /q 或 /quit       - 退出程序")
        print("  /h 或 /help       - 显示此帮助")
        print("  /c 或 /clear      - 清空对话历史")
        print("  /s 或 /save       - 保存对话历史到文件")
        print("  /t <temp>         - 设置温度参数 (0.0-1.0)")
        print("  /p                - 切换提示格式（问题：回答： vs 原始）")
        print("  /stats            - 显示统计信息")
        print("=" * 70 + "\n")

    def show_stats(self):
        """显示统计信息"""
        print("\n" + "=" * 70)
        print("📊 对话统计")
        print("=" * 70)
        print(f"总对话轮数: {len(self.history) // 2}")
        print(f"用户问题数: {sum(1 for h in self.history if h['role'] == 'user')}")
        print(f"模型回答数: {sum(1 for h in self.history if h['role'] == 'assistant')}")

        if self.history:
            total_chars = sum(len(h['content']) for h in self.history if h['role'] == 'assistant')
            avg_chars = total_chars / sum(1 for h in self.history if h['role'] == 'assistant')
            print(f"平均回答长度: {avg_chars:.0f} 字符")

        print("=" * 70 + "\n")

    def save_history(self, filename: str = None):
        """保存对话历史"""
        if filename is None:
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"chat_history_{timestamp}.txt"

        filepath = Path(filename)

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("=" * 70 + "\n")
            f.write("对话历史记录\n")
            f.write("=" * 70 + "\n\n")

            for i, msg in enumerate(self.history, 1):
                role = "用户" if msg['role'] == 'user' else "模型"
                f.write(f"[{i}] {role}:\n")
                f.write(f"{msg['content']}\n")
                f.write("-" * 70 + "\n")

        print(f"✅ 对话历史已保存到: {filepath}\n")

    def run(self):
        """运行交互式评估"""
        self.show_help()

        temperature = 0.3
        use_prompt_format = True
        use_chat = False  # 是否使用多轮对话模式

        print("💡 提示: 输入 /h 查看帮助信息\n")

        while True:
            try:
                # 获取用户输入
                user_input = input("🔵 您的问题> ").strip()

                # 处理命令
                if user_input.startswith('/'):
                    command = user_input.lower().split()[0]

                    if command in ['/q', '/quit']:
                        print("\n👋 再见！")
                        break

                    elif command in ['/h', '/help']:
                        self.show_help()
                        continue

                    elif command in ['/c', '/clear']:
                        self.history = []
                        print("✅ 对话历史已清空\n")
                        continue

                    elif command in ['/s', '/save']:
                        args = user_input.split()
                        filename = args[1] if len(args) > 1 else None
                        self.save_history(filename)
                        continue

                    elif command in ['/t']:
                        args = user_input.split()
                        if len(args) > 1:
                            try:
                                new_temp = float(args[1])
                                if 0.0 <= new_temp <= 1.0:
                                    temperature = new_temp
                                    print(f"✅ 温度已设置为: {temperature}")
                                else:
                                    print("⚠️  温度必须在 0.0-1.0 之间")
                                print()
                            except ValueError:
                                print("⚠️  无效的温度值")
                            continue
                        else:
                            print("⚠️  请指定温度值，例如: /t 0.5")
                            print()
                            continue

                    elif command in ['/p']:
                        use_prompt_format = not use_prompt_format
                        status = "开启" if use_prompt_format else "关闭"
                        print(f"✅ 提示格式已{status}")
                        print()
                        continue

                    elif command in ['/chat']:
                        use_chat = not use_chat
                        status = "开启" if use_chat else "关闭"
                        print(f"✅ 多轮对话模式已{status}")
                        print()
                        continue

                    elif command == '/stats':
                        self.show_stats()
                        continue

                    else:
                        print(f"⚠️  未知命令: {command}")
                        print("  输入 /h 查看可用命令\n")
                        continue

                # 如果不是命令，则作为问题处理
                if not user_input:
                    continue

                print("\n🟢 模型回答:")
                print("-" * 70)

                if use_chat and self.history:
                    # 使用多轮对话模式
                    response = self.inferencer.generate(
                        user_input,
                        max_new_tokens=500,
                        temperature=temperature,
                        top_p=0.95,
                        top_k=50,
                        repetition_penalty=1.1,
                        add_prompt_format=False,
                    )
                    # 手动添加历史（因为generate不支持历史）
                    # 这里简化处理，实际可以扩展
                else:
                    # 单轮对话
                    response = self.inferencer.generate(
                        user_input,
                        max_new_tokens=500,
                        temperature=temperature,
                        top_p=0.95,
                        top_k=50,
                        repetition_penalty=1.1,
                        add_prompt_format=use_prompt_format,
                    )

                print(response)
                print("-" * 70)
                print(f"\n📝 参数: 温度={temperature}, 格式={'问题：回答：' if use_prompt_format else '原始'}")
                print()

                # 保存到历史
                self.history.append({"role": "user", "content": user_input})
                self.history.append({"role": "assistant", "content": response})

            except KeyboardInterrupt:
                print("\n\n👋 程序已中断")
                break

            except Exception as e:
                print(f"\n❌ 错误: {e}\n")


def main():
    """主流程"""
    try:
        # 模型配置
        model_path = "outputs/qwen2_5-3b-trained"
        base_model = "models/Qwen/Qwen2.5-3B"

        # 初始化并运行
        evaluator = InteractiveEvaluator(model_path, base_model)
        evaluator.load_model()
        evaluator.run()

        return True

    except Exception as e:
        print(f"\n❌ 启动失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
