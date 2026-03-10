from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, RootModel, field_validator, model_validator


def _parse_iso8601(value: str) -> datetime:
    normalized = value.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise ValueError(f"invalid ISO8601 time: {value}") from exc


class ScreenshotItem(BaseModel):
    id: int
    captured_at: str
    file_path: str
    ocr_text: str | None = None
    ocr_status: str
    window_title: str | None = None
    process_name: str | None = None
    phash: str | None = None


class SummaryItem(BaseModel):
    id: int
    start_time: str
    end_time: str
    summary: str
    activity_type: str | None = None
    created_at: str

class SummaryCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    start_time: str
    end_time: str
    summary: str
    activity_type: str | None = None

    @field_validator("start_time", "end_time")
    @classmethod
    def validate_time(cls, value: str) -> str:
        _parse_iso8601(value)
        return value

    @model_validator(mode="after")
    def validate_time_range(self) -> "SummaryCreate":
        if _parse_iso8601(self.start_time) > _parse_iso8601(self.end_time):
            raise ValueError("start_time must be less than or equal to end_time")
        return self


class SettingsUpdate(RootModel[dict[str, str]]):
    @field_validator("root")
    @classmethod
    def validate_settings(cls, values: dict[str, str]) -> dict[str, str]:
        normalized: dict[str, str] = {}
        for key, value in values.items():
            stripped = key.strip()
            if not stripped:
                raise ValueError("setting key must not be empty")
            normalized[stripped] = value
        return normalized
