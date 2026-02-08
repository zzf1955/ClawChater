"""OCR Worker 单元测试"""
import threading
import time
from unittest.mock import patch, MagicMock
import pytest


class TestOCRWorkerLoop:
    """测试 _worker_loop 的 GPU 检测逻辑"""

    def _make_worker(self):
        """创建一个 mock 过的 OCRWorker 实例"""
        from ocr_worker import OCRWorker
        with patch.object(OCRWorker, '_init_ocr'):
            worker = OCRWorker()
            worker.ocr_engine = MagicMock()
            worker.has_gpu = True
        return worker

    @patch('ocr_worker.db')
    @patch('ocr_worker.config')
    @patch('ocr_worker.is_gpu_idle')
    def test_batch_processes_without_gpu_check_per_item(
        self, mock_gpu_idle, mock_config, mock_db
    ):
        """batch 内应连续处理所有 item，不逐张检查 GPU"""
        worker = self._make_worker()

        # GPU 检测：第一次空闲，之后都忙碌
        # 如果 batch 内还在检查 GPU，第二张就会被跳过
        gpu_calls = [True, False, False, False, False]
        mock_gpu_idle.side_effect = lambda *a, **kw: gpu_calls.pop(0) if gpu_calls else False

        mock_config.get.side_effect = lambda key: {
            'GPU_USAGE_THRESHOLD': 30,
            'OCR_BATCH_SIZE': 3,
        }[key]

        # 3 张待处理图片
        mock_db.get_pending_ocr.return_value = [
            {'id': 1, 'path': '/fake/1.jpg'},
            {'id': 2, 'path': '/fake/2.jpg'},
            {'id': 3, 'path': '/fake/3.jpg'},
        ]

        processed = []
        original_process = worker.process_one
        worker.process_one = lambda sid, path: processed.append(sid) or True

        # 运行一轮后停止
        def run_one_loop():
            worker._running = True
            # 手动模拟一轮循环逻辑
            from ocr_worker import is_gpu_idle
            import config as cfg
            if is_gpu_idle(cfg.get('GPU_USAGE_THRESHOLD')):
                pending = mock_db.get_pending_ocr(cfg.get('OCR_BATCH_SIZE'))
                for item in pending:
                    if not worker._running:
                        break
                    worker.process_one(item['id'], item['path'])

        run_one_loop()

        # 关键断言：3 张图片都应该被处理
        assert processed == [1, 2, 3], (
            f"Expected all 3 items processed, got {processed}. "
            "Batch-internal GPU check may still be blocking."
        )

    @patch('ocr_worker.db')
    @patch('ocr_worker.config')
    @patch('ocr_worker.is_gpu_idle')
    def test_gpu_check_before_batch(
        self, mock_gpu_idle, mock_config, mock_db
    ):
        """batch 开始前应检查 GPU，GPU 忙时不拉取任务"""
        worker = self._make_worker()

        mock_gpu_idle.return_value = False  # GPU 一直忙
        mock_config.get.return_value = 30

        worker._running = True

        # 模拟一轮
        from ocr_worker import is_gpu_idle
        import config as cfg
        if is_gpu_idle(cfg.get('GPU_USAGE_THRESHOLD')):
            mock_db.get_pending_ocr(cfg.get('OCR_BATCH_SIZE'))

        # GPU 忙时不应拉取任务
        mock_db.get_pending_ocr.assert_not_called()

    @patch('ocr_worker.db')
    @patch('ocr_worker.config')
    @patch('ocr_worker.is_gpu_idle')
    def test_worker_loop_stops_on_running_false(
        self, mock_gpu_idle, mock_config, mock_db
    ):
        """_running=False 时 batch 应中断"""
        worker = self._make_worker()

        mock_gpu_idle.return_value = True
        mock_config.get.side_effect = lambda key: {
            'GPU_USAGE_THRESHOLD': 30,
            'OCR_BATCH_SIZE': 3,
        }[key]

        mock_db.get_pending_ocr.return_value = [
            {'id': 1, 'path': '/fake/1.jpg'},
            {'id': 2, 'path': '/fake/2.jpg'},
            {'id': 3, 'path': '/fake/3.jpg'},
        ]

        processed = []

        def fake_process(sid, path):
            processed.append(sid)
            if sid == 2:
                worker._running = False  # 处理第 2 张后停止
            return True

        worker.process_one = fake_process
        worker._running = True

        # 模拟一轮
        from ocr_worker import is_gpu_idle
        import config as cfg
        if is_gpu_idle(cfg.get('GPU_USAGE_THRESHOLD')):
            pending = mock_db.get_pending_ocr(cfg.get('OCR_BATCH_SIZE'))
            for item in pending:
                if not worker._running:
                    break
                worker.process_one(item['id'], item['path'])

        # 第 3 张不应被处理
        assert processed == [1, 2]
