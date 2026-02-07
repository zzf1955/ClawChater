"""CuriousAI 单元测试"""
import pytest
import json
from unittest.mock import MagicMock, patch


class TestCuriousAIToolLoop:
    """测试工具调用循环"""

    @pytest.fixture
    def mock_message_queue(self):
        """Mock 消息队列"""
        mq = MagicMock()
        mq.get_user_message.return_value = None
        return mq

    @pytest.fixture
    def mock_vector_memory(self):
        """Mock 向量记忆"""
        vm = MagicMock()
        vm.search.return_value = [{"text": "测试记忆内容"}]
        return vm

    @pytest.fixture
    def mock_summarizer(self):
        """Mock 活动总结器"""
        s = MagicMock()
        s.get_recent_summaries.return_value = "用户最近在编程"
        return s

    @pytest.fixture
    def curious_ai(self, mock_message_queue, mock_vector_memory, mock_summarizer):
        """创建 CuriousAI 实例"""
        from curious_ai import CuriousAI
        return CuriousAI(
            message_queue=mock_message_queue,
            vector_memory=mock_vector_memory,
            summarizer=mock_summarizer
        )

    def test_text_reply_no_tools(self, curious_ai, mock_message_queue):
        """测试纯文本回复，无工具调用"""
        # Mock LLM 返回纯文本
        with patch.object(curious_ai, '_call_llm') as mock_llm:
            mock_llm.return_value = {
                "content": "这是一个测试回复",
                "tool_calls": []
            }

            msg = {
                "content": "你好",
                "conversation_id": 1,
                "pending_msg_id": 100
            }
            curious_ai._handle_user_message(msg)

            # 验证 LLM 只被调用一次
            assert mock_llm.call_count == 1

            # 验证消息队列更新了 pending 消息
            mock_message_queue.ai_update.assert_called_once_with(100, "这是一个测试回复")

    def test_single_tool_call_loop(self, curious_ai, mock_message_queue, mock_vector_memory):
        """测试单次工具调用后继续 LLM 循环"""
        call_count = [0]

        def mock_llm_response(is_exploration=False):
            call_count[0] += 1
            if call_count[0] == 1:
                # 第一次调用：返回工具调用
                return {
                    "content": "",
                    "tool_calls": [{
                        "id": "call_1",
                        "function": {
                            "name": "search_memory",
                            "arguments": json.dumps({"query": "用户偏好"})
                        }
                    }]
                }
            else:
                # 第二次调用：返回最终回复
                return {
                    "content": "根据记忆，用户喜欢编程",
                    "tool_calls": []
                }

        with patch.object(curious_ai, '_call_llm', side_effect=mock_llm_response):
            msg = {
                "content": "我喜欢什么？",
                "conversation_id": 1,
                "pending_msg_id": 100
            }
            curious_ai._handle_user_message(msg)

            # 验证 LLM 被调用两次
            assert call_count[0] == 2

            # 验证工具被执行
            mock_vector_memory.search.assert_called_once_with("用户偏好", n=5)

            # 验证最终回复被发送
            mock_message_queue.ai_update.assert_called_once_with(100, "根据记忆，用户喜欢编程")

    def test_multiple_tool_calls(self, curious_ai, mock_message_queue, mock_vector_memory, mock_summarizer):
        """测试多次工具调用的迭代"""
        call_count = [0]

        def mock_llm_response(is_exploration=False):
            call_count[0] += 1
            if call_count[0] == 1:
                # 第一次：搜索记忆
                return {
                    "content": "",
                    "tool_calls": [{
                        "id": "call_1",
                        "function": {
                            "name": "search_memory",
                            "arguments": json.dumps({"query": "用户信息"})
                        }
                    }]
                }
            elif call_count[0] == 2:
                # 第二次：获取活动
                return {
                    "content": "",
                    "tool_calls": [{
                        "id": "call_2",
                        "function": {
                            "name": "get_activity",
                            "arguments": json.dumps({"hours": 3})
                        }
                    }]
                }
            else:
                # 第三次：最终回复
                return {
                    "content": "综合分析结果",
                    "tool_calls": []
                }

        with patch.object(curious_ai, '_call_llm', side_effect=mock_llm_response):
            msg = {
                "content": "分析我的情况",
                "conversation_id": 1,
                "pending_msg_id": 100
            }
            curious_ai._handle_user_message(msg)

            # 验证 LLM 被调用三次
            assert call_count[0] == 3

            # 验证两个工具都被执行
            mock_vector_memory.search.assert_called_once()
            mock_summarizer.get_recent_summaries.assert_called_once_with(hours=3)

            # 验证最终回复
            mock_message_queue.ai_update.assert_called_once_with(100, "综合分析结果")

    def test_max_iterations_limit(self, curious_ai, mock_message_queue):
        """测试最大迭代次数限制"""
        call_count = [0]

        def mock_llm_response(is_exploration=False):
            call_count[0] += 1
            # 始终返回工具调用，测试最大迭代限制
            return {
                "content": f"迭代 {call_count[0]}",
                "tool_calls": [{
                    "id": f"call_{call_count[0]}",
                    "function": {
                        "name": "search_memory",
                        "arguments": json.dumps({"query": "测试"})
                    }
                }]
            }

        with patch.object(curious_ai, '_call_llm', side_effect=mock_llm_response):
            msg = {
                "content": "无限循环测试",
                "conversation_id": 1,
                "pending_msg_id": 100
            }
            curious_ai._handle_user_message(msg)

            # 验证最多调用 4 次（1 次初始 + 3 次迭代）
            assert call_count[0] == 4

    def test_send_message_tool(self, curious_ai, mock_message_queue):
        """测试 send_message 工具正确更新前端"""
        call_count = [0]

        def mock_llm_response(is_exploration=False):
            call_count[0] += 1
            if call_count[0] == 1:
                return {
                    "content": "",
                    "tool_calls": [{
                        "id": "call_1",
                        "function": {
                            "name": "send_message",
                            "arguments": json.dumps({"message": "AI 主动消息"})
                        }
                    }]
                }
            else:
                return {
                    "content": "完成",
                    "tool_calls": []
                }

        with patch.object(curious_ai, '_call_llm', side_effect=mock_llm_response):
            msg = {
                "content": "测试",
                "conversation_id": 1,
                "pending_msg_id": 100
            }
            curious_ai._handle_user_message(msg)

            # send_message 工具应该更新 pending 消息
            assert mock_message_queue.ai_update.call_count == 2
            mock_message_queue.ai_update.assert_any_call(100, "AI 主动消息")
            mock_message_queue.ai_update.assert_any_call(100, "完成")

    def test_conversation_history_updated(self, curious_ai, mock_message_queue):
        """测试对话历史正确更新"""
        call_count = [0]

        def mock_llm_response(is_exploration=False):
            call_count[0] += 1
            if call_count[0] == 1:
                return {
                    "content": "思考中...",
                    "tool_calls": [{
                        "id": "call_1",
                        "function": {
                            "name": "search_memory",
                            "arguments": json.dumps({"query": "测试"})
                        }
                    }]
                }
            else:
                return {
                    "content": "最终回复",
                    "tool_calls": []
                }

        with patch.object(curious_ai, '_call_llm', side_effect=mock_llm_response):
            curious_ai.conversation = []
            msg = {
                "content": "用户消息",
                "conversation_id": None,
                "pending_msg_id": 100
            }
            curious_ai._handle_user_message(msg)

            # 验证对话历史包含正确的消息
            assert len(curious_ai.conversation) == 4

            # 1. 用户消息
            assert curious_ai.conversation[0]["role"] == "user"
            assert curious_ai.conversation[0]["content"] == "用户消息"

            # 2. assistant 消息（包含 tool_calls）
            assert curious_ai.conversation[1]["role"] == "assistant"
            assert "tool_calls" in curious_ai.conversation[1]

            # 3. tool 消息
            assert curious_ai.conversation[2]["role"] == "tool"
            assert curious_ai.conversation[2]["tool_call_id"] == "call_1"

            # 4. 最终 assistant 消息
            assert curious_ai.conversation[3]["role"] == "assistant"
            assert curious_ai.conversation[3]["content"] == "最终回复"

    def test_no_pending_msg_sends_directly(self, curious_ai, mock_message_queue):
        """测试没有 pending_msg_id 时直接发送消息"""
        with patch.object(curious_ai, '_call_llm') as mock_llm:
            mock_llm.return_value = {
                "content": "直接发送的消息",
                "tool_calls": []
            }

            msg = {
                "content": "测试",
                "conversation_id": 1,
                "pending_msg_id": None
            }
            curious_ai._handle_user_message(msg)

            # 应该调用 ai_send 而不是 ai_update
            mock_message_queue.ai_send.assert_called_once_with("直接发送的消息", 1)
            mock_message_queue.ai_update.assert_not_called()


class TestCuriousAIExplore:
    """测试主动探索功能"""

    @pytest.fixture
    def mock_message_queue(self):
        mq = MagicMock()
        return mq

    @pytest.fixture
    def mock_vector_memory(self):
        vm = MagicMock()
        vm.search.return_value = []
        return vm

    @pytest.fixture
    def mock_summarizer(self):
        s = MagicMock()
        s.get_recent_summaries.return_value = "用户在使用 VS Code 编程"
        return s

    @pytest.fixture
    def curious_ai(self, mock_message_queue, mock_vector_memory, mock_summarizer):
        from curious_ai import CuriousAI
        ai = CuriousAI(
            message_queue=mock_message_queue,
            vector_memory=mock_vector_memory,
            summarizer=mock_summarizer
        )
        ai.last_question_time = 0  # 允许探索
        return ai

    def test_explore_with_tool_loop(self, curious_ai, mock_message_queue):
        """测试探索模式下的工具调用循环"""
        call_count = [0]

        def mock_llm_response(is_exploration=False):
            call_count[0] += 1
            if call_count[0] == 1:
                return {
                    "content": "",
                    "tool_calls": [{
                        "id": "call_1",
                        "function": {
                            "name": "search_memory",
                            "arguments": json.dumps({"query": "编程偏好"})
                        }
                    }]
                }
            else:
                return {
                    "content": "发现你在编程，有什么问题吗？",
                    "tool_calls": []
                }

        with patch.object(curious_ai, '_call_llm', side_effect=mock_llm_response):
            with patch('db.get_active_conversation', return_value={"id": 1}):
                curious_ai._explore()

                # 验证 LLM 被调用两次
                assert call_count[0] == 2

                # 验证最终消息被发送
                mock_message_queue.ai_send.assert_called_once()
