from pathlib import Path

import pytest

from recall.db.database import init_db
from recall.db.summary import create_summary, delete_summary, get_summary, list_summaries, update_summary


@pytest.fixture
def db_path(tmp_path: Path) -> Path:
    path = tmp_path / "recall.db"
    init_db(path)
    return path


def test_summary_crud_success(db_path: Path) -> None:
    row = create_summary(
        start_time="2026-03-10T10:00:00Z",
        end_time="2026-03-10T11:00:00Z",
        summary="focus coding",
        db_path=db_path,
    )

    fetched = get_summary(row["id"], db_path=db_path)
    assert fetched is not None
    assert fetched["summary"] == "focus coding"

    updated = update_summary(
        row["id"],
        start_time="2026-03-10T10:00:00Z",
        end_time="2026-03-10T12:00:00Z",
        summary="focus coding and review",
        activity_type="coding",
        db_path=db_path,
    )
    assert updated["activity_type"] == "coding"

    rows = list_summaries(start_time="2026-03-10T09:00:00Z", end_time="2026-03-10T13:00:00Z", db_path=db_path)
    assert len(rows) == 1

    assert delete_summary(row["id"], db_path=db_path) is True
    assert get_summary(row["id"], db_path=db_path) is None


def test_summary_error_paths(db_path: Path) -> None:
    with pytest.raises(ValueError):
        create_summary(
            start_time="2026-03-10T11:00:00Z",
            end_time="2026-03-10T10:00:00Z",
            summary="invalid",
            db_path=db_path,
        )

    with pytest.raises(ValueError):
        create_summary(
            start_time="2026/03/10 10:00:00",
            end_time="2026-03-10T11:00:00Z",
            summary="invalid",
            db_path=db_path,
        )

    with pytest.raises(LookupError):
        update_summary(
            999,
            start_time="2026-03-10T10:00:00Z",
            end_time="2026-03-10T11:00:00Z",
            summary="missing",
            activity_type=None,
            db_path=db_path,
        )
