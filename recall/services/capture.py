from __future__ import annotations

from datetime import datetime
from pathlib import Path

from recall.config import SCREENSHOTS_DIR


def capture_screen() -> Path:
    now = datetime.utcnow()
    target_dir = SCREENSHOTS_DIR / now.strftime("%Y-%m-%d") / now.strftime("%H")
    target_dir.mkdir(parents=True, exist_ok=True)
    fake_image_path = target_dir / f"{now.strftime('%Y%m%d%H%M%S')}.jpg"
    if not fake_image_path.exists():
        fake_image_path.write_bytes(b"")
    return fake_image_path
