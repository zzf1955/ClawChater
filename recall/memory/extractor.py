"""记忆提取器 - 从对话中提取需要记住的内容

重构说明：
- MemoryExtractor 类：支持依赖注入，可指定 text_memory 和 vector_memory
- 全局实例：向后兼容层
"""
import json
import logging
from typing import List, Dict, Any, TYPE_CHECKING

import httpx

import config

if TYPE_CHECKING:
    from memory.text_memory import TextMemory
    from memory.vector_memory import VectorMemory

log = logging.getLogger(__name__)

EXTRACTION_PROMPT = """分析以下对话，提取需要长期记住的信息。

返回JSON格式：
{
    "text_memory": [
        {"section": "基本信息/偏好/重要事项", "content": "要记住的内容"}
    ],
    "vector_memory": [
        {"text": "详细信息或事件描述", "type": "event/fact/preference"}
    ],
    "skip": true/false
}

规则：
- 只提取重要的、值得长期记住的信息
- 用户偏好、习惯 → text_memory (偏好)
- 用户基本信息 → text_memory (基本信息)
- 重要事件、具体信息 → vector_memory
- 如果对话没有值得记住的内容，设置 skip: true
- 不要记录闲聊、问候等无意义内容

对话内容：
"""


class MemoryExtractor:
    """记忆提取器"""

    def __init__(self, text_memory: "TextMemory" = None,
                 vector_memory: "VectorMemory" = None):
        """
        初始化记忆提取器

        Args:
            text_memory: 文本记忆实例，默认使用全局实例
            vector_memory: 向量记忆实例，默认使用全局实例
        """
        self._text_memory = text_memory
        self._vector_memory = vector_memory
        self.headers = {
            "Authorization": f"Bearer {config.LLM_API_KEY}",
            "Content-Type": "application/json"
        }

    @property
    def text_memory(self):
        """获取文本记忆实例"""
        if self._text_memory is None:
            from memory.text_memory import text_memory
            return text_memory
        return self._text_memory

    @property
    def vector_memory(self):
        """获取向量记忆实例"""
        if self._vector_memory is None:
            from memory.vector_memory import vector_memory
            return vector_memory
        return self._vector_memory

    def _format_conversation(self, messages: List[Dict]) -> str:
        """格式化对话为文本"""
        lines = []
        for msg in messages:
            role = msg.get("role", "")
            content = msg.get("content", "")
            if role == "user":
                lines.append(f"用户: {content}")
            elif role == "assistant":
                lines.append(f"助手: {content}")
        return "\n".join(lines)

    def extract(self, messages: List[Dict]) -> Dict[str, Any]:
        """从对话中提取记忆"""
        if not messages:
            return {"skip": True}

        conversation_text = self._format_conversation(messages)
        prompt = EXTRACTION_PROMPT + conversation_text

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
                result = resp.json()
                content = result["choices"][0]["message"]["content"]

                # 解析JSON
                # 尝试提取JSON部分
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0]
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0]

                return json.loads(content.strip())

        except json.JSONDecodeError as e:
            log.warning(f"记忆提取JSON解析失败: {e}")
            return {"skip": True}
        except Exception as e:
            log.error(f"记忆提取失败: {e}")
            return {"skip": True}

    def extract_and_save(self, messages: List[Dict]):
        """提取记忆并保存"""
        result = self.extract(messages)

        if result.get("skip", False):
            log.info("对话无需记忆")
            return

        # 保存到文本记忆库
        for item in result.get("text_memory", []):
            section = item.get("section", "重要事项")
            content = item.get("content", "")
            if content:
                self.text_memory.append(section, content)

        # 保存到向量记忆库
        for item in result.get("vector_memory", []):
            text = item.get("text", "")
            mem_type = item.get("type", "fact")
            if text:
                try:
                    self.vector_memory.add(text, {"type": mem_type})
                except Exception as e:
                    log.warning(f"向量记忆保存失败: {e}")

        log.info(f"记忆提取完成: text={len(result.get('text_memory', []))}, "
                 f"vector={len(result.get('vector_memory', []))}")


# 全局实例（向后兼容）
extractor = MemoryExtractor()
