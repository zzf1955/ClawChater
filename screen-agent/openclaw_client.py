"""OpenClaw Hooks API 客户端（支持 dry-run 模式）"""
import httpx
import logging

log = logging.getLogger(__name__)


class OpenClawClient:
    """OpenClaw Hooks API 客户端"""

    def __init__(self, base_url: str, token: str, dry_run: bool = True):
        self.base_url = base_url.rstrip('/')
        self.token = token
        self.dry_run = dry_run
        self.client = httpx.Client(timeout=30.0)

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
