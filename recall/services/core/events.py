from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class BaseEvent:
    happened_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class ScreenChangeEvent(BaseEvent):
    pass


@dataclass
class ForceCaptureEvent(BaseEvent):
    pass


@dataclass
class ResourceAvailableEvent(BaseEvent):
    pass
