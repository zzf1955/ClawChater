"""截图服务单元测试"""
import pytest
import numpy as np
from pathlib import Path


class TestCaptureService:
    """截图服务测试"""

    def test_calculate_diff_same_image(self):
        """测试相同图片差异为 0"""
        from core.capture import CaptureService
        service = CaptureService()

        img = np.zeros((100, 100, 3), dtype=np.uint8)
        diff = service.calculate_diff(img, img)
        assert diff == 0.0

    def test_calculate_diff_different_image(self):
        """测试完全不同图片差异接近 1"""
        from core.capture import CaptureService
        service = CaptureService()

        img1 = np.zeros((100, 100, 3), dtype=np.uint8)
        img2 = np.full((100, 100, 3), 255, dtype=np.uint8)

        diff = service.calculate_diff(img1, img2)
        assert diff > 0.9

    def test_calculate_diff_different_shape(self):
        """测试不同尺寸图片返回 1"""
        from core.capture import CaptureService
        service = CaptureService()

        img1 = np.zeros((100, 100, 3), dtype=np.uint8)
        img2 = np.zeros((200, 200, 3), dtype=np.uint8)

        diff = service.calculate_diff(img1, img2)
        assert diff == 1.0

    def test_get_screenshot_path(self, temp_screenshot_dir):
        """测试生成截图路径"""
        from core.capture import CaptureService
        service = CaptureService(screenshot_dir=temp_screenshot_dir)

        path = service.get_screenshot_path()
        assert path.suffix == ".jpg"
        assert temp_screenshot_dir in path.parents
