"""Thinking Session + Chat Session 编排单元测试"""
import sys
import os
import io
from contextlib import redirect_stdout

sys.path.insert(0, os.path.dirname(__file__))

from openclaw_client import (
    OpenClawClient, THINKING_PROMPT_TEMPLATE,
    CHAT_TRIGGER_MESSAGE, THINKING_WAIT_SECONDS,
)


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

    screenshots = [{"timestamp": "t", "window_title": "w", "process_name": "p", "ocr_preview": "text"}]
    f = io.StringIO()
    with redirect_stdout(f):
        client.send_to_thinking_session(screenshots)

    output = f.getvalue()
    assert "deliver: False" in output
    assert "sessionKey: hook:screen-agent-thinking" in output


def test_chat_trigger_dry_run():
    """验证 dry-run 模式下 trigger_chat_session 返回 True"""
    client = OpenClawClient("http://localhost:18789", "test", dry_run=True)
    f = io.StringIO()
    with redirect_stdout(f):
        result = client.trigger_chat_session(channel="telegram", to="123")

    assert result is True
    output = f.getvalue()
    assert "Chat Session" in output
    assert "deliver: True" in output
    assert "sessionKey: hook:screen-agent-chat" in output


def test_chat_trigger_message_content():
    """验证触发消息包含关键内容"""
    assert "intents.json" in CHAT_TRIGGER_MESSAGE
    assert "待处理意图" in CHAT_TRIGGER_MESSAGE


def test_run_heartbeat_success():
    """验证 heartbeat 两步编排成功路径"""
    client = OpenClawClient("http://localhost:18789", "test", dry_run=True)
    screenshots = [{"timestamp": "t", "window_title": "w", "process_name": "p", "ocr_preview": "text"}]

    f = io.StringIO()
    with redirect_stdout(f):
        result = client.run_heartbeat(screenshots, channel="telegram", to="123")

    assert result is True
    output = f.getvalue()
    # 应该同时包含 Thinking 和 Chat 的输出
    assert "Thinking Session" in output
    assert "Chat Session" in output


def test_run_heartbeat_thinking_fails():
    """验证 Thinking 失败时不触发 Chat"""
    client = OpenClawClient("http://localhost:18789", "test", dry_run=False)
    # 非 dry-run 模式下，连接会失败
    screenshots = [{"timestamp": "t", "window_title": "w", "process_name": "p", "ocr_preview": "text"}]

    result = client.run_heartbeat(screenshots)
    assert result is False  # Thinking 失败，整个 heartbeat 失败


def test_thinking_wait_seconds():
    """验证等待时间常量存在且合理"""
    assert isinstance(THINKING_WAIT_SECONDS, int)
    assert 10 <= THINKING_WAIT_SECONDS <= 120


if __name__ == "__main__":
    test_format_ocr_summary()
    test_format_ocr_summary_truncates()
    test_format_ocr_summary_limits_30()
    test_thinking_prompt_template()
    test_thinking_session_dry_run()
    test_thinking_session_payload_structure()
    test_chat_trigger_dry_run()
    test_chat_trigger_message_content()
    test_run_heartbeat_success()
    test_run_heartbeat_thinking_fails()
    test_thinking_wait_seconds()
    print("All tests passed!")
