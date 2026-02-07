"""LLM测试脚本 - 交互式测试LLM功能"""
import sys
import json
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from llm import LLMService


def print_separator():
    print("-" * 60)


def print_tool_calls(tool_calls):
    """打印工具调用详情"""
    if not tool_calls:
        print("  (无工具调用)")
        return
    for i, tc in enumerate(tool_calls, 1):
        func = tc.get("function", {})
        name = func.get("name", "unknown")
        try:
            args = json.loads(func.get("arguments", "{}"))
        except:
            args = {}
        print(f"  [{i}] {name}({json.dumps(args, ensure_ascii=False)})")


def print_conversation(conversation):
    """打印对话历史"""
    if not conversation:
        print("  (对话历史为空)")
        return
    for i, msg in enumerate(conversation):
        role = msg.get("role", "unknown")
        content = msg.get("content", "")
        if role == "tool":
            tool_id = msg.get("tool_call_id", "")
            print(f"  [{i}] tool({tool_id}): {content[:100]}...")
        elif role == "assistant" and msg.get("tool_calls"):
            print(f"  [{i}] assistant: [tool_calls]")
        else:
            preview = content[:80] + "..." if len(content) > 80 else content
            print(f"  [{i}] {role}: {preview}")


def main():
    print("=" * 60)
    print("LLM 测试工具")
    print("=" * 60)
    print("命令:")
    print("  /clear   - 清空对话历史")
    print("  /history - 查看对话历史")
    print("  /system  - 查看系统提示词")
    print("  /quit    - 退出")
    print_separator()

    # 创建独立的LLM实例
    llm = LLMService()
    print("已创建独立LLM实例")
    print_separator()

    while True:
        try:
            user_input = input("\n> ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n退出")
            break

        if not user_input:
            continue

        # 处理命令
        if user_input == "/quit":
            print("退出")
            break

        elif user_input == "/clear":
            llm.clear_conversation()
            print("对话历史已清空")
            continue

        elif user_input == "/history":
            print("\n对话历史:")
            print_conversation(llm.conversation)
            continue

        elif user_input == "/system":
            print("\n系统提示词:")
            print_separator()
            print(llm._build_system_prompt())
            print_separator()
            continue

        elif user_input.startswith("/"):
            print(f"未知命令: {user_input}")
            continue

        # 发送消息
        print("\n发送中...")
        result = llm.chat(user_input, debug=True)

        print_separator()
        print(f"回复: {result['reply']}")
        print_separator()
        print(f"工具调用 (迭代{result['iterations']}次):")
        print_tool_calls(result['tool_calls'])
        print_separator()


if __name__ == "__main__":
    main()
