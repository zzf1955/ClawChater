from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Literal, TypeAlias


EventName: TypeAlias = Literal["screen_change", "force_capture", "resource_available", "config_updated"]


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(slots=True)
class BaseEvent:
    name: EventName
    happened_at: str = field(default_factory=_utc_now_iso)
    payload: dict[str, str | int | float | bool | None] = field(default_factory=dict)


@dataclass(slots=True)
class ScreenChangeEvent(BaseEvent):
    name: EventName = field(default="screen_change", init=False)


@dataclass(slots=True)
class ForceCaptureEvent(BaseEvent):
    name: EventName = field(default="force_capture", init=False)


@dataclass(slots=True)
class ResourceAvailableEvent(BaseEvent):
    name: EventName = field(default="resource_available", init=False)


@dataclass(slots=True)
class ConfigUpdatedEvent(BaseEvent):
    name: EventName = field(default="config_updated", init=False)


Event: TypeAlias = ScreenChangeEvent | ForceCaptureEvent | ResourceAvailableEvent | ConfigUpdatedEvent
