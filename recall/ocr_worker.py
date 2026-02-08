"""OCR后台处理模块"""
import os
import sys
import time
import logging
import threading
from pathlib import Path
from typing import Optional, Callable

import config
import db
from utils.gpu import is_gpu_idle

log = logging.getLogger(__name__)

# 添加cuDNN路径
_nvidia_path = os.path.join(sys.prefix, 'Lib', 'site-packages', 'nvidia')
_cudnn_bin = os.path.join(_nvidia_path, 'cudnn', 'bin')
_cublas_bin = os.path.join(_nvidia_path, 'cublas', 'bin')
if os.path.exists(_cudnn_bin):
    os.environ['PATH'] = _cudnn_bin + os.pathsep + _cublas_bin + os.pathsep + os.environ.get('PATH', '')


class OCRWorker:
    """OCR后台处理器"""

    def __init__(self):
        self.ocr_engine = None
        self.has_gpu = False
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._init_ocr()

    def _init_ocr(self):
        """初始化OCR引擎"""
        try:
            import onnxruntime as ort
            providers = ort.get_available_providers()
            log.info(f"ONNX可用Providers: {providers}")

            if 'CUDAExecutionProvider' in providers:
                self.has_gpu = True
                from rapidocr_onnxruntime import RapidOCR
                self.ocr_engine = RapidOCR(
                    det_use_cuda=True,
                    cls_use_cuda=True,
                    rec_use_cuda=True
                )
                log.info("OCR Worker: GPU模式")
            else:
                self.has_gpu = False
                log.warning("OCR Worker: 无GPU，OCR将在GPU空闲时处理")
        except Exception as e:
            self.has_gpu = False
            log.error(f"OCR初始化失败: {e}")

    def process_one(self, screenshot_id: int, image_path: str) -> bool:
        """处理单张图片的OCR"""
        if not self.ocr_engine:
            return False

        try:
            from PIL import Image
            import numpy as np

            img = np.array(Image.open(image_path))
            start_time = time.time()
            result, _ = self.ocr_engine(img)
            ocr_time = time.time() - start_time

            if result:
                text_lines = [line[1] for line in result]
                ocr_text = '\n'.join(text_lines)
                # 同时保存txt文件
                txt_path = Path(image_path).with_suffix('.txt')
                txt_path.write_text(ocr_text, encoding='utf-8')
                log.info(f"OCR完成: {Path(image_path).name} - {len(text_lines)}行 ({ocr_time:.2f}s)")
            else:
                ocr_text = ''
                Path(image_path).with_suffix('.txt').write_text('', encoding='utf-8')
                log.info(f"OCR完成: {Path(image_path).name} - 无文本 ({ocr_time:.2f}s)")

            db.update_ocr_result(screenshot_id, ocr_text, 'done')
            return True

        except Exception as e:
            log.error(f"OCR处理失败 {image_path}: {e}")
            db.update_ocr_result(screenshot_id, '', 'error')
            return False

    def _worker_loop(self):
        """后台处理循环"""
        log.info("OCR Worker 启动")
        while self._running:
            try:
                # 检查GPU是否空闲
                if not is_gpu_idle(config.get('GPU_USAGE_THRESHOLD')):
                    time.sleep(5)
                    continue

                # 获取待处理任务
                pending = db.get_pending_ocr(config.get('OCR_BATCH_SIZE'))
                if not pending:
                    time.sleep(10)
                    continue

                # 处理OCR
                for item in pending:
                    if not self._running:
                        break
                    self.process_one(item['id'], item['path'])

            except Exception as e:
                log.error(f"OCR Worker错误: {e}")
                time.sleep(5)

        log.info("OCR Worker 停止")

    def start(self):
        """启动后台处理"""
        if self._running:
            return
        if not self.ocr_engine:
            log.warning("OCR引擎未初始化，Worker不启动")
            return

        self._running = True
        self._thread = threading.Thread(target=self._worker_loop, daemon=True)
        self._thread.start()

    def stop(self):
        """停止后台处理"""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)


# 全局实例
_worker: Optional[OCRWorker] = None


def get_worker() -> OCRWorker:
    """获取全局OCR Worker"""
    global _worker
    if _worker is None:
        _worker = OCRWorker()
    return _worker
