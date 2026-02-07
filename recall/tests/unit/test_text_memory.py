"""文本记忆库单元测试"""
import pytest


class TestTextMemory:
    """文本记忆库测试"""

    def test_load_returns_content(self, temp_memory_file):
        """测试加载返回文件内容"""
        from memory.text_memory import TextMemory
        tm = TextMemory(filepath=temp_memory_file)

        content = tm.load()
        assert "# 用户记忆" in content

    def test_get_section(self, temp_memory_file):
        """测试获取指定 section"""
        from memory.text_memory import TextMemory
        tm = TextMemory(filepath=temp_memory_file)

        # 先添加内容
        tm.append("偏好", "喜欢深色主题")

        section = tm.get_section("偏好")
        assert "喜欢深色主题" in section

    def test_append_to_section(self, temp_memory_file):
        """测试追加内容到 section"""
        from memory.text_memory import TextMemory
        tm = TextMemory(filepath=temp_memory_file)

        tm.append("基本信息", "用户名: 测试用户")

        content = tm.load()
        assert "用户名: 测试用户" in content

    def test_append_creates_section_if_not_exists(self, temp_memory_file):
        """测试追加到不存在的 section 会创建它"""
        from memory.text_memory import TextMemory
        tm = TextMemory(filepath=temp_memory_file)

        tm.append("新分类", "新内容")

        content = tm.load()
        assert "## 新分类" in content
        assert "新内容" in content

    def test_update_section(self, temp_memory_file):
        """测试替换 section 内容"""
        from memory.text_memory import TextMemory
        tm = TextMemory(filepath=temp_memory_file)

        tm.append("偏好", "旧内容")
        tm.update_section("偏好", "新内容")

        section = tm.get_section("偏好")
        assert "新内容" in section
        assert "旧内容" not in section
