from __future__ import annotations

from datetime import datetime


def parse_iso8601(value: str) -> datetime:
    """Parse an ISO 8601 string, accepting trailing 'Z' as UTC."""
    normalized = value.replace("Z", "+00:00")
    return datetime.fromisoformat(normalized)
