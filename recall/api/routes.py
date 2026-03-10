from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse

from recall.api.schemas import SettingsUpdate, SummaryCreate
from recall.config import DATA_DIR
from recall.db.screenshot import get_screenshot, list_screenshots
from recall.db.setting import get_all_settings, update_settings
from recall.db.summary import create_summary, list_summaries

router = APIRouter(prefix="/api", tags=["api"])


@router.get("/screenshots")
def get_screenshots(
    start_time: str | None = None,
    end_time: str | None = None,
    limit: int = Query(default=100, ge=1, le=1000),
) -> list[dict]:
    return list_screenshots(start_time=start_time, end_time=end_time, limit=limit)


@router.get("/screenshots/{screenshot_id}")
def get_screenshot_by_id(screenshot_id: int) -> dict:
    row = get_screenshot(screenshot_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Screenshot not found")
    return row


@router.get("/screenshots/{screenshot_id}/image")
def get_screenshot_image(screenshot_id: int) -> FileResponse:
    row = get_screenshot(screenshot_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Screenshot not found")
    image_path = DATA_DIR / row["file_path"]
    if not image_path.exists():
        raise HTTPException(status_code=404, detail="Image file missing")
    return FileResponse(path=image_path, media_type="image/jpeg", filename=Path(row["file_path"]).name)


@router.get("/summaries")
def get_summary_list(start_time: str | None = None, end_time: str | None = None) -> list[dict]:
    return list_summaries(start_time=start_time, end_time=end_time)


@router.post("/summaries")
def create_summary_item(payload: SummaryCreate) -> dict:
    return create_summary(
        start_time=payload.start_time,
        end_time=payload.end_time,
        summary=payload.summary,
        activity_type=payload.activity_type,
    )


@router.get("/config")
def get_config() -> dict[str, str]:
    return get_all_settings()


@router.post("/config")
def update_config(payload: SettingsUpdate) -> dict[str, str]:
    return update_settings(payload.values)
