"""Slave client: capture screenshots and write to syncthing sync directory.

Usage:
    python -m recall.slave

Environment variables:
    RECALL_DEVICE_ID        — device identifier (default: hostname)
    RECALL_SYNC_DIR         — syncthing sync directory (required)
    RECALL_CAPTURE_INTERVAL — capture interval in seconds (default: 5)
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import platform
import signal
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from recall.services.capture import CaptureService

_logger = logging.getLogger(__name__)

_DEFAULT_INTERVAL = 5


def _get_device_id() -> str:
    return os.getenv("RECALL_DEVICE_ID", platform.node())


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Recall slave — screenshot collector")
    parser.add_argument(
        "--sync-dir",
        default=os.getenv("RECALL_SYNC_DIR"),
        help="Syncthing sync directory (or set RECALL_SYNC_DIR)",
    )
    parser.add_argument(
        "--device-id",
        default=_get_device_id(),
        help="Device identifier (default: hostname)",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=float(os.getenv("RECALL_CAPTURE_INTERVAL", str(_DEFAULT_INTERVAL))),
        help=f"Capture interval in seconds (default: {_DEFAULT_INTERVAL})",
    )
    parser.add_argument(
        "--no-change-only",
        action="store_false",
        dest="change_only",
        help="Capture every interval even if screen is unchanged",
    )
    return parser.parse_args()


def _write_screenshot(
    sync_dir: Path,
    device_id: str,
    image_bytes: bytes,
    phash: str,
    window_title: str | None = None,
    process_name: str | None = None,
) -> Path:
    captured_at_dt = datetime.now(timezone.utc)
    captured_at = captured_at_dt.isoformat()
    timestamp = captured_at_dt.strftime("%Y%m%d%H%M%S%f")

    stem = f"{device_id}_{timestamp}"
    jpg_path = sync_dir / f"{stem}.jpg"
    json_path = sync_dir / f"{stem}.json"

    sync_dir.mkdir(parents=True, exist_ok=True)

    metadata = {
        "device_id": device_id,
        "captured_at": captured_at,
        "window_title": window_title,
        "process_name": process_name,
        "platform": platform.system(),
        "phash": phash,
    }

    # Write jpg first, then json sidecar — IncomingWatcher only processes
    # files when both exist, so json acts as the "ready" signal.
    jpg_path.write_bytes(image_bytes)
    json_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")

    _logger.info("saved %s (%d bytes)", jpg_path.name, len(image_bytes))
    return jpg_path


def run(sync_dir: Path, device_id: str, interval: float, change_only: bool) -> None:
    _logger.info(
        "slave starting device_id=%s sync_dir=%s interval=%.1fs change_only=%s",
        device_id, sync_dir, interval, change_only,
    )

    capture_svc = CaptureService()
    last_phash: str | None = None
    running = True

    def _stop(signum, frame):
        nonlocal running
        _logger.info("received signal %s, stopping", signum)
        running = False

    signal.signal(signal.SIGINT, _stop)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, _stop)

    while running:
        try:
            image_bytes = capture_svc._screenshot_provider()
            if not image_bytes or image_bytes == b"RECALL_FAKE_JPEG":
                _logger.warning("screenshot provider returned empty/fake data, skipping")
                time.sleep(interval)
                continue

            phash = CaptureService._build_phash(image_bytes)

            if change_only and last_phash is not None and phash == last_phash:
                _logger.debug("screen unchanged (phash=%s), skipping", phash)
                time.sleep(interval)
                continue

            _write_screenshot(
                sync_dir=sync_dir,
                device_id=device_id,
                image_bytes=image_bytes,
                phash=phash,
            )
            last_phash = phash

        except Exception:
            _logger.exception("capture failed, will retry")

        time.sleep(interval)

    _logger.info("slave stopped")


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    args = _parse_args()

    if not args.sync_dir:
        print("Error: --sync-dir or RECALL_SYNC_DIR is required", file=sys.stderr)
        sys.exit(1)

    sync_dir = Path(args.sync_dir).expanduser().resolve()
    run(sync_dir=sync_dir, device_id=args.device_id, interval=args.interval, change_only=args.change_only)


if __name__ == "__main__":
    main()
