"""导入历史截图数据到数据库"""
import os
import sys
from pathlib import Path
from datetime import datetime

# 添加项目根目录到路径
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

import db
from utils.similarity import compute_phash
import config


def parse_timestamp_from_path(path: Path) -> datetime:
    """从路径解析时间戳: screenshots/2026-01-25/10/103943.jpg"""
    try:
        date_str = path.parent.parent.name  # 2026-01-25
        hour_str = path.parent.name          # 10
        time_str = path.stem                  # 103943

        # 处理时间字符串
        h = time_str[:2]
        m = time_str[2:4]
        s = time_str[4:6] if len(time_str) >= 6 else "00"

        return datetime.strptime(
            f"{date_str} {hour_str}:{m}:{s}",
            "%Y-%m-%d %H:%M:%S"
        )
    except Exception as e:
        print(f"  解析时间戳失败 {path}: {e}")
        return datetime.now()


def scan_and_import(screenshot_dir: str = None):
    """扫描截图目录并导入数据库"""
    if screenshot_dir is None:
        screenshot_dir = ROOT_DIR / config.SCREENSHOT_DIR

    root = Path(screenshot_dir)
    if not root.exists():
        print(f"目录不存在: {root}")
        return 0, 0

    print(f"扫描目录: {root}")
    imported = 0
    skipped = 0
    errors = 0

    # 遍历 YYYY-MM-DD/HH/HHMMSS.jpg 结构
    for date_dir in sorted(root.iterdir()):
        if not date_dir.is_dir():
            continue

        print(f"\n处理日期: {date_dir.name}")

        for hour_dir in sorted(date_dir.iterdir()):
            if not hour_dir.is_dir():
                continue

            # 获取所有图片文件
            img_files = list(hour_dir.glob("*.jpg")) + list(hour_dir.glob("*.png"))

            for img_file in sorted(img_files):
                path_str = str(img_file)

                # 检查是否已存在
                if db.screenshot_exists(path_str):
                    skipped += 1
                    continue

                try:
                    # 解析时间戳
                    timestamp = parse_timestamp_from_path(img_file)

                    # 计算 phash
                    try:
                        phash = compute_phash(img_file)
                    except Exception:
                        phash = None

                    # 读取 OCR 文本 (如果存在)
                    txt_file = img_file.with_suffix('.txt')
                    if txt_file.exists():
                        ocr_text = txt_file.read_text(encoding='utf-8')
                        ocr_status = 'done'
                    else:
                        ocr_text = None
                        ocr_status = 'pending'

                    # 插入数据库
                    db.add_screenshot_with_ocr(
                        path=path_str,
                        timestamp=timestamp,
                        phash=phash,
                        ocr_text=ocr_text,
                        ocr_status=ocr_status
                    )
                    imported += 1

                    if imported % 100 == 0:
                        print(f"  已导入 {imported} 张...")

                except Exception as e:
                    print(f"  导入失败 {img_file.name}: {e}")
                    errors += 1

    return imported, skipped, errors


def main():
    """主函数"""
    print("=" * 50)
    print("Recall 历史数据导入工具")
    print("=" * 50)

    # 初始化数据库
    db.init_db()

    # 扫描并导入
    imported, skipped, errors = scan_and_import()

    print("\n" + "=" * 50)
    print(f"导入完成!")
    print(f"  新导入: {imported} 张")
    print(f"  已跳过: {skipped} 张 (已存在)")
    print(f"  失败: {errors} 张")
    print("=" * 50)


if __name__ == "__main__":
    main()