"""文本记忆库 - Markdown格式存储用户偏好和重要事实

重构说明：
- TextMemory 类：支持依赖注入，可指定文件路径
- 全局实例：向后兼容层
"""
import re
import logging
from pathlib import Path
from typing import Optional

log = logging.getLogger(__name__)

MEMORY_FILE = Path(__file__).parent.parent / "data" / "memory.md"


class TextMemory:
    """文本记忆库管理"""

    def __init__(self, filepath: Path = MEMORY_FILE):
        self.filepath = filepath
        self._ensure_file()

    def _ensure_file(self):
        """确保文件存在"""
        if not self.filepath.exists():
            self.filepath.parent.mkdir(parents=True, exist_ok=True)
            self.filepath.write_text(
                "# 用户记忆\n\n## 基本信息\n\n## 偏好\n\n## 重要事项\n",
                encoding="utf-8"
            )

    def load(self) -> str:
        """加载全部内容"""
        self._ensure_file()
        return self.filepath.read_text(encoding="utf-8")

    def get_section(self, section_name: str) -> str:
        """获取指定section的内容"""
        content = self.load()
        pattern = rf"## {re.escape(section_name)}\n(.*?)(?=\n## |\Z)"
        match = re.search(pattern, content, re.DOTALL)
        if match:
            return match.group(1).strip()
        return ""

    def append(self, section_name: str, content: str):
        """追加内容到指定section"""
        full_content = self.load()

        # 查找section位置
        pattern = rf"(## {re.escape(section_name)}\n)"
        match = re.search(pattern, full_content)

        if match:
            # 在section标题后插入内容
            insert_pos = match.end()
            # 找到下一个section或文件末尾
            next_section = re.search(r"\n## ", full_content[insert_pos:])
            if next_section:
                section_end = insert_pos + next_section.start()
            else:
                section_end = len(full_content)

            # 获取现有内容
            existing = full_content[insert_pos:section_end].strip()

            # 构建新内容
            if existing:
                new_section_content = f"{existing}\n- {content}"
            else:
                new_section_content = f"- {content}"

            # 重建文件内容
            new_full = (
                full_content[:insert_pos] +
                new_section_content + "\n\n" +
                full_content[section_end:].lstrip()
            )
        else:
            # section不存在，添加新section
            new_full = full_content.rstrip() + f"\n\n## {section_name}\n- {content}\n"

        self.filepath.write_text(new_full, encoding="utf-8")
        log.info(f"追加记忆到 [{section_name}]: {content[:50]}...")

    def update_section(self, section_name: str, new_content: str):
        """替换指定section的全部内容"""
        full_content = self.load()

        pattern = rf"(## {re.escape(section_name)}\n).*?(?=\n## |\Z)"
        replacement = rf"\g<1>{new_content}\n"

        if re.search(pattern, full_content, re.DOTALL):
            new_full = re.sub(pattern, replacement, full_content, flags=re.DOTALL)
        else:
            new_full = full_content.rstrip() + f"\n\n## {section_name}\n{new_content}\n"

        self.filepath.write_text(new_full, encoding="utf-8")
        log.info(f"更新记忆section [{section_name}]")


# 全局实例（向后兼容）
text_memory = TextMemory()
