from pydantic import BaseModel


class SummaryCreate(BaseModel):
    start_time: str
    end_time: str
    summary: str
    activity_type: str | None = None


class SettingsUpdate(BaseModel):
    values: dict[str, str]
