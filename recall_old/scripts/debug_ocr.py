"""
OCR GPU/CPU Diagnosis Script
Detect CPU and GPU usage during OCR
"""
import os
import sys
import time
import threading

# Add cuDNN to PATH before importing onnxruntime
_nvidia_path = os.path.join(sys.prefix, 'Lib', 'site-packages', 'nvidia')
_cudnn_bin = os.path.join(_nvidia_path, 'cudnn', 'bin')
_cublas_bin = os.path.join(_nvidia_path, 'cublas', 'bin')
if os.path.exists(_cudnn_bin):
    os.environ['PATH'] = _cudnn_bin + os.pathsep + _cublas_bin + os.pathsep + os.environ.get('PATH', '')

import psutil
from pathlib import Path

# GPU监控
try:
    import pynvml
    pynvml.nvmlInit()
    gpu_handle = pynvml.nvmlDeviceGetHandleByIndex(0)
    HAS_PYNVML = True
except:
    HAS_PYNVML = False
    print("警告: pynvml不可用，无法监控GPU")

# 监控数据
monitor_data = {
    "cpu": [],
    "gpu": [],
    "running": False
}

def monitor_thread():
    """后台监控线程"""
    while monitor_data["running"]:
        # CPU使用率
        cpu = psutil.cpu_percent(interval=0.1)
        monitor_data["cpu"].append(cpu)

        # GPU使用率
        if HAS_PYNVML:
            util = pynvml.nvmlDeviceGetUtilizationRates(gpu_handle)
            monitor_data["gpu"].append(util.gpu)

        time.sleep(0.1)

def start_monitor():
    """启动监控"""
    monitor_data["cpu"] = []
    monitor_data["gpu"] = []
    monitor_data["running"] = True
    t = threading.Thread(target=monitor_thread, daemon=True)
    t.start()
    return t

def stop_monitor():
    """停止监控"""
    monitor_data["running"] = False
    time.sleep(0.2)

def print_stats(label):
    """打印统计"""
    print(f"\n=== {label} ===")
    if monitor_data["cpu"]:
        print(f"CPU: 平均 {sum(monitor_data['cpu'])/len(monitor_data['cpu']):.1f}%, "
              f"最大 {max(monitor_data['cpu']):.1f}%")
    if monitor_data["gpu"]:
        print(f"GPU: 平均 {sum(monitor_data['gpu'])/len(monitor_data['gpu']):.1f}%, "
              f"最大 {max(monitor_data['gpu']):.1f}%")


def main():
    import numpy as np
    from PIL import ImageGrab

    print("=" * 60)
    print("OCR GPU/CPU Diagnosis")
    print("=" * 60)

    # 1. 检查ONNX providers
    print("\n[1] ONNX Runtime Config")
    import onnxruntime as ort
    providers = ort.get_available_providers()
    print(f"Available Providers: {providers}")
    print(f"get_device(): {ort.get_device()}")

    # 2. 初始化OCR并监控
    print("\n[2] Init OCR Engine (monitoring...)")
    start_monitor()

    from rapidocr_onnxruntime import RapidOCR
    ocr = RapidOCR(
        det_use_cuda=True,
        cls_use_cuda=True,
        rec_use_cuda=True
    )

    stop_monitor()
    print_stats("OCR Init")

    # 2.5 检查实际使用的provider
    print("\n[2.5] Check actual providers used")
    print(f"Det session providers: {ocr.text_det.infer.session.get_providers()}")
    print(f"Cls session providers: {ocr.text_cls.infer.session.get_providers()}")

    # 3. 截图
    print("\n[3] Capture screen")
    img = np.array(ImageGrab.grab())
    print(f"Image size: {img.shape}")

    # 4. 运行OCR并监控
    print("\n[4] Run OCR (monitoring...)")
    start_monitor()

    start_time = time.time()
    result, _ = ocr(img)
    ocr_time = time.time() - start_time

    stop_monitor()
    print(f"OCR time: {ocr_time:.2f}s")
    print(f"Lines detected: {len(result) if result else 0}")
    print_stats("OCR Run")

    # 5. 诊断结论
    print("\n" + "=" * 60)
    print("Diagnosis")
    print("=" * 60)

    if monitor_data["gpu"] and max(monitor_data["gpu"]) > 30:
        print("[OK] GPU usage increased significantly, OCR likely running on GPU")
    elif monitor_data["cpu"] and max(monitor_data["cpu"]) > 50:
        print("[WARN] High CPU but low GPU usage, OCR likely running on CPU!")
    else:
        print("[?] Cannot determine, please check data")

    if HAS_PYNVML:
        pynvml.nvmlShutdown()


if __name__ == "__main__":
    main()
