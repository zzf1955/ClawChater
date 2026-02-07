"""
处理待OCR的图片
在有GPU的机器上运行此脚本
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from rapidocr_onnxruntime import RapidOCR

ROOT_DIR = Path(__file__).parent.parent
LOG_DIR = ROOT_DIR / "logs"
PENDING_FILE = LOG_DIR / "pending_ocr.txt"


def process_pending():
    """处理所有待OCR的图片"""
    if not PENDING_FILE.exists():
        print("无待处理图片")
        return

    # 读取待处理列表
    pending = PENDING_FILE.read_text(encoding='utf-8').strip().split('\n')
    pending = [p for p in pending if p]

    if not pending:
        print("无待处理图片")
        return

    print(f"待处理: {len(pending)} 张图片")

    # 初始化OCR
    print("初始化OCR引擎...")
    ocr = RapidOCR()

    processed = []
    failed = []

    for i, img_path in enumerate(pending):
        img_path = Path(img_path)
        txt_path = img_path.with_suffix('.txt')

        # 跳过已处理的
        if txt_path.exists():
            processed.append(img_path)
            continue

        if not img_path.exists():
            print(f"[{i+1}/{len(pending)}] 跳过: {img_path} (文件不存在)")
            processed.append(img_path)
            continue

        print(f"[{i+1}/{len(pending)}] 处理: {img_path}")

        try:
            img = np.array(Image.open(img_path))
            result, _ = ocr(img)
            if result:
                text_lines = [line[1] for line in result]
                txt_path.write_text('\n'.join(text_lines), encoding='utf-8')
                print(f"  完成: {len(text_lines)}行文本")
            else:
                txt_path.write_text('', encoding='utf-8')
                print(f"  完成: 无文本")
            processed.append(img_path)
        except Exception as e:
            print(f"  失败: {e}")
            failed.append(img_path)

    # 更新待处理列表
    if failed:
        PENDING_FILE.write_text('\n'.join(str(p) for p in failed), encoding='utf-8')
    else:
        PENDING_FILE.unlink()

    print(f"\n处理完成: {len(processed)} 成功, {len(failed)} 失败")


if __name__ == "__main__":
    process_pending()
