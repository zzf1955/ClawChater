"""消息队列单元测试"""
import pytest
from unittest.mock import MagicMock


class TestMessageQueue:
    """消息队列测试"""

    def test_user_send_adds_to_queue(self, initialized_db):
        """测试用户发送消息添加到队列"""
        from message_queue import MessageQueue
        mq = MessageQueue(database=initialized_db)

        user_msg_id, pending_msg_id = mq.user_send("测试消息")
        assert user_msg_id > 0
        assert pending_msg_id > 0

        # 从队列获取消息
        msg = mq.get_user_message(timeout=1.0)
        assert msg is not None
        assert msg['content'] == "测试消息"
        assert msg['role'] == "user"
        assert msg['pending_msg_id'] == pending_msg_id

    def test_get_user_message_timeout(self, initialized_db):
        """测试获取消息超时返回 None"""
        from message_queue import MessageQueue
        mq = MessageQueue(database=initialized_db)

        msg = mq.get_user_message(timeout=0.1)
        assert msg is None

    def test_ai_send_writes_to_db(self, initialized_db):
        """测试 AI 发送消息写入数据库"""
        from message_queue import MessageQueue
        mq = MessageQueue(database=initialized_db)

        msg_id = mq.ai_send("AI 回复")
        assert msg_id > 0

        # 验证数据库
        messages = initialized_db.get_ai_messages_since(0)
        assert any(m['content'] == "AI 回复" for m in messages)
