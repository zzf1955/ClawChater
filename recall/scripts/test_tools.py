"""统一工具测试脚本 - 测试 LLM 工具调用功能"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, '.')

from datetime import datetime


def test_search_memory():
    """测试 search_memory 工具"""
    print('=== 测试 search_memory 工具 ===')

    try:
        from memory.vector_memory import vector_memory
        print('[OK] 向量记忆库导入成功')
    except ImportError as e:
        print(f'[SKIP] chromadb 未安装: {e}')
        return False
    except Exception as e:
        print(f'[FAIL] 导入失败: {e}')
        return False

    # 测试添加记忆
    try:
        test_text = f"测试记忆 - {datetime.now().isoformat()}"
        mid = vector_memory.add(test_text, {"type": "test"})
        print(f'[OK] 添加记忆成功, ID: {mid}')
    except Exception as e:
        print(f'[FAIL] 添加记忆失败: {e}')
        return False

    # 测试搜索
    try:
        results = vector_memory.search("测试", n=3)
        print(f'[OK] 搜索成功, 找到 {len(results)} 条结果')
        for r in results:
            print(f'  - {r["text"][:50]}...')
    except Exception as e:
        print(f'[FAIL] 搜索失败: {e}')
        return False

    # 测试删除
    try:
        vector_memory.delete(mid)
        print(f'[OK] 删除测试记忆成功')
    except Exception as e:
        print(f'[FAIL] 删除失败: {e}')
        return False

    return True


def test_search_screenshots():
    """测试 search_screenshots 工具"""
    print()
    print('=== 测试 search_screenshots 工具 ===')

    try:
        from llm import llm
        print('[OK] LLM 服务导入成功')
    except Exception as e:
        print(f'[FAIL] 导入失败: {e}')
        return False

    # 测试数据库连接和查询
    try:
        results = llm.search_screenshots("", hours=24, limit=5)
        print(f'[OK] 数据库查询成功, 最近24小时有 {len(results)} 条记录')
        if results:
            for r in results[:3]:
                ts = r.get('timestamp', '')
                title = r.get('window_title', '') or ''
                print(f'  - [{ts}] {title[:40]}')
    except Exception as e:
        print(f'[FAIL] 查询失败: {e}')
        return False

    # 测试关键词搜索
    try:
        results = llm.search_screenshots("Chrome", hours=24, limit=5)
        print(f'[OK] 关键词搜索成功, 找到 {len(results)} 条包含 "Chrome" 的记录')
    except Exception as e:
        print(f'[FAIL] 关键词搜索失败: {e}')
        return False

    return True


def test_get_activity():
    """测试 get_activity 工具"""
    print()
    print('=== 测试 get_activity 工具 ===')

    try:
        from memory.summarizer import summarizer
        print('[OK] 活动总结器导入成功')
    except Exception as e:
        print(f'[FAIL] 导入失败: {e}')
        return False

    # 测试获取最近总结
    try:
        summaries = summarizer.get_recent_summaries(hours=3)
        if summaries == "（暂无活动总结）":
            print('[INFO] 暂无活动总结，尝试生成...')
            summary = summarizer.generate_summary_until_now()
            print(f'[OK] 生成总结成功:')
            print(f'  {summary[:100]}...')
        else:
            print(f'[OK] 获取总结成功:')
            print(f'  {summaries[:100]}...')
    except Exception as e:
        print(f'[FAIL] 获取/生成总结失败: {e}')
        import traceback
        traceback.print_exc()
        return False

    return True


def test_llm_tool_calling():
    """测试 LLM 工具调用集成"""
    print()
    print('=== 测试 LLM 工具调用集成 ===')

    try:
        from llm import LLMService
        test_llm = LLMService()
        print('[OK] LLM 服务实例化成功')
    except Exception as e:
        print(f'[FAIL] 实例化失败: {e}')
        return False

    # 测试一个应该触发工具调用的问题
    print()
    print('测试问题: "我最近在做什么？"')
    print('(这应该触发 get_activity 或 search_screenshots 工具)')
    print()

    try:
        result = test_llm.chat('我最近在做什么？', debug=True)
        reply = result["reply"]
        print(f'回复: {reply[:200]}...' if len(reply) > 200 else f'回复: {reply}')
        print()
        print(f'工具调用次数: {len(result["tool_calls"])}')
        print(f'迭代次数: {result["iterations"]}')

        if result['tool_calls']:
            print()
            print('工具调用详情:')
            for tc in result['tool_calls']:
                func = tc.get('function', {})
                print(f'  - {func.get("name")}: {func.get("arguments")}')
            return True
        else:
            print()
            print('[警告] LLM 没有调用任何工具')
            return False
    except Exception as e:
        print(f'[FAIL] 工具调用测试失败: {e}')
        import traceback
        traceback.print_exc()
        return False


def main():
    """运行所有测试"""
    print('=' * 50)
    print('LLM 工具测试脚本')
    print(f'测试时间: {datetime.now().isoformat()}')
    print('=' * 50)
    print()

    results = {}

    # 运行各项测试
    results['search_memory'] = test_search_memory()
    results['search_screenshots'] = test_search_screenshots()
    results['get_activity'] = test_get_activity()
    results['llm_tool_calling'] = test_llm_tool_calling()

    # 汇总结果
    print()
    print('=' * 50)
    print('测试结果汇总')
    print('=' * 50)
    for name, passed in results.items():
        status = '[PASS]' if passed else '[FAIL]'
        print(f'  {status} {name}')

    all_passed = all(results.values())
    print()
    if all_passed:
        print('所有测试通过!')
    else:
        print('部分测试失败，请检查上方输出')

    return 0 if all_passed else 1


if __name__ == '__main__':
    sys.exit(main())