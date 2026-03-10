from __future__ import annotations

from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse

from recall.api.schemas import ScreenshotItem, SettingsUpdate, SummaryCreate, SummaryItem
from recall.config import DATA_DIR
from recall.db.screenshot import get_screenshot, list_screenshots
from recall.db.setting import get_all_settings, update_settings
from recall.db.summary import create_summary, list_summaries

router = APIRouter(prefix="/api", tags=["api"])


def _parse_iso8601(value: str) -> datetime:
    normalized = value.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=f"invalid ISO8601 time: {value}") from exc


def _validate_time_range(start_time: str | None, end_time: str | None) -> None:
    if start_time:
        _parse_iso8601(start_time)
    if end_time:
        _parse_iso8601(end_time)
    if start_time and end_time and _parse_iso8601(start_time) > _parse_iso8601(end_time):
        raise HTTPException(status_code=422, detail="start_time must be less than or equal to end_time")


@router.get("/screenshots")
def get_screenshots(
    start_time: str | None = None,
    end_time: str | None = None,
    limit: int = Query(default=100, ge=1, le=1000),
) -> list[ScreenshotItem]:
    _validate_time_range(start_time, end_time)
    return list_screenshots(start_time=start_time, end_time=end_time, limit=limit)


@router.get("/screenshots/{screenshot_id}")
def get_screenshot_by_id(screenshot_id: int) -> ScreenshotItem:
    row = get_screenshot(screenshot_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Screenshot not found")
    return row


@router.get("/screenshots/{screenshot_id}/image")
def get_screenshot_image(screenshot_id: int) -> FileResponse:
    row = get_screenshot(screenshot_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Screenshot not found")
    image_path = (DATA_DIR / row["file_path"]).resolve()
    if DATA_DIR.resolve() not in image_path.parents:
        raise HTTPException(status_code=400, detail="Invalid image path")
    if not image_path.exists():
        raise HTTPException(status_code=404, detail="Image file missing")
    return FileResponse(path=image_path, media_type="image/jpeg", filename=Path(row["file_path"]).name)


@router.get("/summaries")
def get_summary_list(start_time: str | None = None, end_time: str | None = None) -> list[SummaryItem]:
    _validate_time_range(start_time, end_time)
    return list_summaries(start_time=start_time, end_time=end_time)


@router.post("/summaries", status_code=201)
def create_summary_item(payload: SummaryCreate) -> SummaryItem:
    try:
        return create_summary(
            start_time=payload.start_time,
            end_time=payload.end_time,
            summary=payload.summary,
            activity_type=payload.activity_type,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/config")
def get_config() -> dict[str, str]:
    return get_all_settings()


@router.post("/config")
def update_config(payload: SettingsUpdate) -> dict[str, str]:
    try:
        return update_settings(payload.root)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
