"""Recall 截图服务 API 客户端"""
import httpx
import logging
from datetime import datetime
from typing import List, Dict, Optional

log = logging.getLogger(__name__)


class RecallClient:
    """Recall 截图服务客户端"""

    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        self.client = httpx.Client(timeout=30.0)

    def get_recent(self, since: Optional[str] = None, limit: int = 50) -> List[Dict]:
        """获取最近截图的 OCR 摘要"""
        params = {'limit': limit}
        if since:
            params['since'] = since
        try:
            resp = self.client.get(f'{self.base_url}/api/recent', params=params)
            resp.raise_for_status()
            return resp.json().get('screenshots', [])
        except Exception as e:
            log.error(f"获取截图失败: {e}")
            return []

    def search(self, query: str, hours: int = 24, limit: int = 20) -> List[Dict]:
        """搜索截图"""
        try:
            resp = self.client.get(
                f'{self.base_url}/api/search',
                params={'q': query, 'hours': hours, 'limit': limit}
            )
            resp.raise_for_status()
            return resp.json().get('results', [])
        except Exception as e:
            log.error(f"搜索截图失败: {e}")
            return []

    def get_detail(self, screenshot_id: int) -> Optional[Dict]:
        """获取截图完整详情"""
        try:
            resp = self.client.get(f'{self.base_url}/api/screenshot/{screenshot_id}/detail')
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            log.error(f"获取截图详情失败: {e}")
            return None
