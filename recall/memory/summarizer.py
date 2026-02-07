"""活动总结生成器 - 定时生成用户活动总结

重构说明：
- ActivitySummarizer 类：支持依赖注入，可指定总结目录和数据库
- 全局实例：向后兼容层
"""
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, List, TYPE_CHECKING

import httpx

import config

if TYPE_CHECKING:
    from db import Database

log = logging.getLogger(__name__)

# 默认总结目录（向后兼容）
SUMMARIES_DIR = Path(__file__).parent.parent / "data" / "summaries" / "hourly"


class ActivitySummarizer:
    """活动总结生成器"""

    def __init__(self, summaries_dir: Path = None, database: "Database" = None):
        """
        初始化活动总结器

        Args:
            summaries_dir: 总结文件存储目录，默认为 data/summaries/hourly
            database: 数据库实例，默认使用全局实例
        """
        self.summaries_dir = summaries_dir or SUMMARIES_DIR
        self._database = database
        self.headers = {
            "Authorization": f"Bearer {config.LLM_API_KEY}",
            "Content-Type": "application/json"
        }
        self.summaries_dir.mkdir(parents=True, exist_ok=True)
        self._last_summary_time: Optional[datetime] = None

    @property
    def database(self):
        """获取数据库实例"""
        if self._database is None:
            import db
            return db  # 使用模块级函数（向后兼容）
        return self._database

    def _get_screenshots_in_range(self, start: datetime, end: datetime) -> List[dict]:
        """获取指定时间范围内的截图"""
        if self._database is not None:
            # 使用注入的数据库实例
            with self._database.get_connection() as conn:
                rows = conn.execute("""
                    SELECT timestamp, window_title, process_name, ocr_text
                    FROM screenshots
                    WHERE timestamp BETWEEN ? AND ?
                    ORDER BY timestamp
                """, (start.isoformat(), end.isoformat())).fetchall()
                return [dict(row) for row in rows]
        else:
            # 使用全局数据库（向后兼容）
            import db
            with db.get_connection() as conn:
                rows = conn.execute("""
                    SELECT timestamp, window_title, process_name, ocr_text
                    FROM screenshots
                    WHERE timestamp BETWEEN ? AND ?
                    ORDER BY timestamp
                """, (start.isoformat(), end.isoformat())).fetchall()
                return [dict(row) for row in rows]

    def _format_screenshots_for_llm(self, screenshots: List[dict]) -> str:
        """格式化截图数据供LLM分析"""
        if not screenshots:
            return "（该时间段没有截图记录）"

        lines = []
        for s in screenshots:
            ts = s.get("timestamp", "")
            title = s.get("window_title", "") or ""
            process = s.get("process_name", "") or ""
            ocr = s.get("ocr_text", "") or ""
            # 截断OCR文本
            if len(ocr) > 150:
                ocr = ocr[:150] + "..."

            line = f"[{ts}] {process}"
            if title:
                line += f" - {title}"
            lines.append(line)
            if ocr:
                lines.append(f"  内容片段: {ocr}")

        return "\n".join(lines)

    def _call_llm(self, prompt: str) -> str:
        """调用LLM生成总结"""
        data = {
            "model": config.LLM_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 500
        }
        try:
            with httpx.Client(timeout=60) as client:
                resp = client.post(
                    f"{config.LLM_BASE_URL}/chat/completions",
                    headers=self.headers,
                    json=data
                )
                resp.raise_for_status()
                return resp.json()["choices"][0]["message"]["content"]
        except Exception as e:
            log.error(f"LLM调用失败: {e}")
            return f"（总结生成失败: {e}）"

    def generate_summary(self, start: datetime, end: datetime) -> str:
        """生成指定时间段的活动总结"""
        screenshots = self._get_screenshots_in_range(start, end)

        if not screenshots:
            return f"# {start.strftime('%Y-%m-%d %H:%M')} - {end.strftime('%H:%M')}\n\n无活动记录"

        formatted = self._format_screenshots_for_llm(screenshots)

        prompt = f"""以下是用户在 {start.strftime('%Y-%m-%d %H:%M')} 到 {end.strftime('%H:%M')} 的屏幕活动记录。
请生成一段简洁的活动总结（100字以内），描述用户主要在做什么。

活动记录：
{formatted}

要求：
- 简洁概括，不要逐条列举
- 用中文回答
- 直接输出总结内容，不要加标题"""

        summary_text = self._call_llm(prompt)

        # 格式化为markdown
        result = f"# {start.strftime('%Y-%m-%d %H:%M')} - {end.strftime('%H:%M')}\n\n{summary_text}"
        return result

    def generate_hourly_summary(self, hour: datetime = None) -> str:
        """生成某小时的总结并保存"""
        if hour is None:
            hour = datetime.now().replace(minute=0, second=0, microsecond=0)

        start = hour
        end = hour + timedelta(hours=1)

        summary = self.generate_summary(start, end)

        # 保存到文件
        filename = f"{hour.strftime('%Y-%m-%d_%H')}.md"
        filepath = self.summaries_dir / filename
        filepath.write_text(summary, encoding="utf-8")

        self._last_summary_time = datetime.now()
        log.info(f"生成活动总结: {filepath}")

        return summary

    def get_recent_summaries(self, hours: int = 3) -> str:
        """获取最近N小时的总结"""
        now = datetime.now()
        summaries = []

        for i in range(hours):
            hour = (now - timedelta(hours=i)).replace(minute=0, second=0, microsecond=0)
            filename = f"{hour.strftime('%Y-%m-%d_%H')}.md"
            filepath = self.summaries_dir / filename

            if filepath.exists():
                content = filepath.read_text(encoding="utf-8")
                summaries.append(content)

        if not summaries:
            return "（暂无活动总结）"

        return "\n\n---\n\n".join(summaries)

    def ensure_fresh(self, max_age_minutes: int = 10) -> bool:
        """确保总结是新鲜的，如果过期则重新生成当前时段的总结"""
        now = datetime.now()
        current_hour = now.replace(minute=0, second=0, microsecond=0)

        # 检查当前小时的总结文件
        filename = f"{current_hour.strftime('%Y-%m-%d_%H')}.md"
        filepath = self.summaries_dir / filename

        need_refresh = False

        if not filepath.exists():
            need_refresh = True
        else:
            # 检查文件修改时间
            mtime = datetime.fromtimestamp(filepath.stat().st_mtime)
            if (now - mtime).total_seconds() > max_age_minutes * 60:
                need_refresh = True

        if need_refresh:
            # 生成从当前小时开始到现在的总结
            self.generate_summary_until_now()
            return True

        return False

    def generate_summary_until_now(self) -> str:
        """生成从当前小时开始到现在的总结"""
        now = datetime.now()
        current_hour = now.replace(minute=0, second=0, microsecond=0)

        summary = self.generate_summary(current_hour, now)

        # 保存
        filename = f"{current_hour.strftime('%Y-%m-%d_%H')}.md"
        filepath = self.summaries_dir / filename
        filepath.write_text(summary, encoding="utf-8")

        self._last_summary_time = now
        log.info(f"更新活动总结: {filepath}")

        return summary


# 全局实例（向后兼容）
summarizer = ActivitySummarizer()
