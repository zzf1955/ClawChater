"""截图分析器 — 两阶段 LLM 分析（OCR 摘要 → 按需取图）"""
import httpx
import json
import logging
from typing import List, Dict, Optional

log = logging.getLogger(__name__)

SYSTEM_PROMPT = """你是一个好奇的 AI 屏幕观察者。你通过截图的 OCR 文本和窗口信息来了解用户在做什么。

你的任务：
1. 观察用户最近的屏幕活动
2. 识别有趣的、值得讨论的内容
3. 决定是否需要主动向用户提问或分享发现

行为准则：
- 每次只问一个问题，保持简洁友好
- 不要问太琐碎的问题
- 关注用户可能需要帮助的场景
- 如果没有值得问的，回复 NO_QUESTION
"""


class Analyzer:
    """截图分析器"""

    def __init__(self, api_key: str, base_url: str, model: str):
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.model = model
        self.client = httpx.Client(timeout=60.0)

    def analyze(self, screenshots: List[Dict]) -> Optional[str]:
        """分析截图摘要，返回要问的问题或 None"""
        if not screenshots:
            return None

        # 格式化截图摘要
        lines = []
        for s in screenshots[:30]:  # 限制数量
            ts = s.get('timestamp', '')
            title = s.get('window_title', '')
            process = s.get('process_name', '')
            ocr = s.get('ocr_preview', '')
            lines.append(f"[{ts}] {process} - {title}")
            if ocr:
                lines.append(f"  内容: {ocr[:150]}")

        activity_text = '\n'.join(lines)

        user_prompt = f"""以下是用户最近的屏幕活动（{len(screenshots)} 条截图摘要）：

{activity_text}

请判断是否需要主动向用户提问或分享发现。
- 如果有值得问的，直接输出你的问题（一句话）
- 如果没有，输出 NO_QUESTION"""

        response = self._call_llm(user_prompt)
        if not response:
            return None

        response = response.strip()
        if response == "NO_QUESTION" or not response:
            log.info("LLM 决定不提问")
            return None

        log.info(f"LLM 生成问题: {response[:100]}")
        return response

    def _call_llm(self, user_prompt: str) -> Optional[str]:
        """调用 LLM API"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            "max_tokens": 500
        }

        try:
            resp = self.client.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload
            )
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]
        except Exception as e:
            log.error(f"LLM 调用失败: {e}")
            return None
