"""Thinking Session 单元测试"""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from openclaw_client import OpenClawClient, THINKING_PROMPT_TEMPLATE


def test_format_ocr_summary():
    """验证 OCR 摘要格式化"""
    screenshots = [
        {
            "timestamp": "2026-02-08T12:00:00",
            "window_title": "Chrome",
            "process_name": "chrome.exe",
            "ocr_preview": "Hello World",
        },
        {
            "timestamp": "2026-02-08T12:01:00",
            "window_title": "VS Code",
            "process_name": "code.exe",
            "ocr_preview": "",
        },
    ]
    summary = OpenClawClient._format_ocr_summary(screenshots)
    assert "[2026-02-08T12:00:00] chrome.exe - Chrome" in summary
    assert "内容: Hello World" in summary
    assert "[2026-02-08T12:01:00] code.exe - VS Code" in summary
    # 空 ocr_preview 不应出现 "内容:" 行
    lines = summary.split("\n")
    assert not any("内容:" in l for l in lines if "VS Code" in lines[lines.index(l) - 1] if lines.index(l) > 0)


def test_format_ocr_summary_truncates():
    """验证 OCR 文本截断到 150 字符"""
    long_text = "x" * 200
    screenshots = [{"timestamp": "t", "window_title": "w", "process_name": "p", "ocr_preview": long_text}]
    summary = OpenClawClient._format_ocr_summary(screenshots)
    # 内容行应该只有 150 个 x
    for line in summary.split("\n"):
        if "内容:" in line:
            assert line.count("x") == 150


def test_format_ocr_summary_limits_30():
    """验证最多处理 30 条截图"""
    screenshots = [
        {"timestamp": f"t{i}", "window_title": f"w{i}", "process_name": f"p{i}", "ocr_preview": ""}
        for i in range(50)
    ]
    summary = OpenClawClient._format_ocr_summary(screenshots)
    # 应该只有 30 条
    assert summary.count("[t") == 30


def test_thinking_prompt_template():
    """验证 prompt 模板包含关键指令"""
    assert "facts.json" in THINKING_PROMPT_TEMPLATE
    assert "intents.json" in THINKING_PROMPT_TEMPLATE
    assert "read" in THINKING_PROMPT_TEMPLATE.lower()
    assert "write" in THINKING_PROMPT_TEMPLATE.lower()
    assert "{ocr_summary}" in THINKING_PROMPT_TEMPLATE


def test_thinking_session_dry_run():
    """验证 dry-run 模式下 send_to_thinking_session 返回 True"""
    client = OpenClawClient("http://localhost:18789", "test", dry_run=True)
    screenshots = [
        {"timestamp": "t", "window_title": "w", "process_name": "p", "ocr_preview": "text"}
    ]
    assert client.send_to_thinking_session(screenshots) is True


def test_thinking_session_payload_structure():
    """验证 payload 结构：sessionKey 持久化、deliver=False"""
    client = OpenClawClient("http://localhost:18789", "test", dry_run=True)

    # 捕获 payload（通过检查 dry-run 输出）
    import io
    from contextlib import redirect_stdout

    screenshots = [{"timestamp": "t", "window_title": "w", "process_name": "p", "ocr_preview": "text"}]
    f = io.StringIO()
    with redirect_stdout(f):
        client.send_to_thinking_session(screenshots)

    output = f.getvalue()
    assert "deliver: False" in output
    assert "sessionKey: hook:screen-agent-thinking" in output


if __name__ == "__main__":
    test_format_ocr_summary()
    test_format_ocr_summary_truncates()
    test_format_ocr_summary_limits_30()
    test_thinking_prompt_template()
    test_thinking_session_dry_run()
    test_thinking_session_payload_structure()
    print("All tests passed!")
