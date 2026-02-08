"""OpenClaw Hooks API 客户端（支持 dry-run 模式）"""
import time
import httpx
import logging
from typing import List, Dict

log = logging.getLogger(__name__)

THINKING_PROMPT_TEMPLATE = """你是一个屏幕活动分析助手。你的任务是分析用户的屏幕活动，生成观察和问题。

## 你的工作流程
1. 用 read 工具读取 facts.json，了解已知事实（避免重复提问）
2. 分析下面的 OCR 数据
3. 如果发现值得聊的内容，用 read 工具读取 intents.json，然后用 write 工具更新它
4. 只添加新意图（status: "pending"），保留未处理的旧意图
5. 如果没有值得聊的内容，不需要更新 intents.json

## 意图格式
每条意图包含：id（i-NNN）、created_at、type（observation/curiosity/question）、content、context、status

## 当前 OCR 数据
{ocr_summary}"""

CHAT_TRIGGER_MESSAGE = "有新的屏幕观察，请查看 intents.json 中的待处理意图，选择合适的话题和用户聊天。"

# Thinking Session 完成等待时间（秒）
THINKING_WAIT_SECONDS = 30


class OpenClawClient:
    """OpenClaw Hooks API 客户端"""

    def __init__(self, base_url: str, token: str, dry_run: bool = True):
        self.base_url = base_url.rstrip('/')
        self.token = token
        self.dry_run = dry_run
        self.client = httpx.Client(timeout=30.0)

    def send_to_thinking_session(self, screenshots: List[Dict]) -> bool:
        """发送 OCR 数据到 Thinking Session

        使用持久化 sessionKey，deliver=False（不投递到 Telegram）。
        Agent 会分析 OCR 数据并写入 intents.json。
        """
        ocr_summary = self._format_ocr_summary(screenshots)
        message = THINKING_PROMPT_TEMPLATE.format(ocr_summary=ocr_summary)

        payload = {
            "message": message,
            "name": "Screen Agent",
            "sessionKey": "hook:screen-agent-thinking",
            "deliver": False,
            "wakeMode": "now",
        }

        if self.dry_run:
            log.info(f"[DRY-RUN] Thinking Session: {len(screenshots)} 条截图")
            print(f"\n{'='*60}")
            print("[Screen Agent -> Thinking Session]")
            print(f"Screenshots: {len(screenshots)}")
            print(f"OCR summary length: {len(ocr_summary)} chars")
            print(f"deliver: {payload['deliver']}")
            print(f"sessionKey: {payload['sessionKey']}")
            print(f"{'='*60}\n")
            return True

        try:
            resp = self.client.post(
                f"{self.base_url}/hooks/agent",
                headers={
                    "Authorization": f"Bearer {self.token}",
                    "Content-Type": "application/json"
                },
                json=payload
            )
            resp.raise_for_status()
            log.info(f"Thinking Session 已处理 {len(screenshots)} 条截图")
            return True
        except Exception as e:
            log.error(f"Thinking Session 调用失败: {e}")
            return False

    def trigger_chat_session(self, channel: str = "telegram", to: str = "") -> bool:
        """触发 Chat Agent 检查意图并主动聊天

        发送触发消息到 Chat Session，deliver=True 投递到 Telegram。
        """
        payload = {
            "message": CHAT_TRIGGER_MESSAGE,
            "name": "Screen Agent",
            "channel": channel,
            "deliver": True,
            "wakeMode": "now",
            "sessionKey": "hook:screen-agent-chat",
        }
        if to:
            payload["to"] = to

        if self.dry_run:
            log.info(f"[DRY-RUN] Chat Session trigger -> {channel}")
            print(f"\n{'='*60}")
            print(f"[Screen Agent -> Chat Session ({channel})]")
            print(f"Message: {CHAT_TRIGGER_MESSAGE}")
            print(f"deliver: True")
            print(f"sessionKey: {payload['sessionKey']}")
            print(f"{'='*60}\n")
            return True

        try:
            resp = self.client.post(
                f"{self.base_url}/hooks/agent",
                headers={
                    "Authorization": f"Bearer {self.token}",
                    "Content-Type": "application/json"
                },
                json=payload
            )
            resp.raise_for_status()
            log.info(f"Chat Session 已触发 -> {channel}")
            return True
        except Exception as e:
            log.error(f"Chat Session 触发失败: {e}")
            return False

    def run_heartbeat(self, screenshots: List[Dict],
                      channel: str = "telegram", to: str = "") -> bool:
        """完整的 heartbeat 流程：Thinking → 等待 → Chat

        Step 1: 发送 OCR 到 Thinking Session（分析 + 写 intents.json）
        Step 2: 等待 Thinking 完成
        Step 3: 触发 Chat Session（读 intents → 和用户聊天）
        """
        # Step 1: Thinking
        log.info("Heartbeat Step 1: Thinking Session...")
        if not self.send_to_thinking_session(screenshots):
            log.warning("Thinking Session 失败，跳过 Chat 触发")
            return False

        # Step 2: 等待 Thinking 完成
        if not self.dry_run:
            log.info(f"等待 Thinking 完成 ({THINKING_WAIT_SECONDS}s)...")
            time.sleep(THINKING_WAIT_SECONDS)
        else:
            log.info(f"[DRY-RUN] 跳过等待 {THINKING_WAIT_SECONDS}s")

        # Step 3: 触发 Chat
        log.info("Heartbeat Step 2: Chat Session...")
        return self.trigger_chat_session(channel=channel, to=to)

    def send_message(self, message: str, channel: str = "telegram", to: str = "") -> bool:
        """发送主动消息

        dry_run=True 时只打印到控制台，不实际发送。
        """
        payload = {
            "message": message,
            "name": "Screen Agent",
            "channel": channel,
            "deliver": True,
            "wakeMode": "now",
            "sessionKey": "hook:screen-agent",
        }
        if to:
            payload["to"] = to

        if self.dry_run:
            log.info(f"[DRY-RUN] 将发送到 {channel}: {message}")
            print(f"\n{'='*60}")
            print(f"[Screen Agent -> {channel}]")
            print(f"Payload: {payload}")
            print(f"{'='*60}\n")
            return True

        try:
            resp = self.client.post(
                f"{self.base_url}/hooks/agent",
                headers={
                    "Authorization": f"Bearer {self.token}",
                    "Content-Type": "application/json"
                },
                json=payload
            )
            resp.raise_for_status()
            log.info(f"消息已发送到 {channel}: {message[:50]}...")
            return True
        except Exception as e:
            log.error(f"发送消息失败: {e}")
            return False

    @staticmethod
    def _format_ocr_summary(screenshots: List[Dict]) -> str:
        """将截图列表格式化为 OCR 摘要文本"""
        lines = []
        for s in screenshots[:30]:
            ts = s.get('timestamp', '')
            title = s.get('window_title', '')
            process = s.get('process_name', '')
            ocr = s.get('ocr_preview', '')
            lines.append(f"[{ts}] {process} - {title}")
            if ocr:
                lines.append(f"  内容: {ocr[:150]}")
        return '\n'.join(lines)
