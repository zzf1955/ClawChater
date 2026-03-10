from pathlib import Path

import pytest

from recall.db.database import init_db
from recall.db.screenshot import (
    create_screenshot,
    delete_screenshot,
    get_screenshot,
    list_screenshots,
    list_screenshots_by_status,
    update_screenshot_ocr,
)


@pytest.fixture
def db_path(tmp_path: Path) -> Path:
    path = tmp_path / "recall.db"
    init_db(path)
    return path


def test_screenshot_crud_success(db_path: Path) -> None:
    row = create_screenshot(
        captured_at="2026-03-10T10:00:00Z",
        file_path="screenshots/1.jpg",
        window_title="Editor",
        process_name="code",
        phash="ab12",
        db_path=db_path,
    )

    assert row["ocr_status"] == "pending"

    done = create_screenshot(
        captured_at="2026-03-10T10:01:00Z",
        file_path="screenshots/2.jpg",
        ocr_status="done",
        ocr_text="hello",
        db_path=db_path,
    )

    pending_rows = list_screenshots_by_status("pending", db_path=db_path)
    assert [item["id"] for item in pending_rows] == [row["id"]]

    all_rows = list_screenshots(start_time=None, end_time=None, limit=10, db_path=db_path)
    assert [item["id"] for item in all_rows] == [done["id"], row["id"]]

    updated = update_screenshot_ocr(
        row["id"],
        ocr_text="new text",
        ocr_status="done",
        db_path=db_path,
    )
    assert updated["ocr_text"] == "new text"
    assert updated["ocr_status"] == "done"

    assert delete_screenshot(done["id"], db_path=db_path) is True
    assert get_screenshot(done["id"], db_path=db_path) is None


def test_screenshot_error_paths(db_path: Path) -> None:
    with pytest.raises(ValueError):
        create_screenshot(
            captured_at="2026-03-10T10:00:00Z",
            file_path="screenshots/1.jpg",
            ocr_status="unknown",
            db_path=db_path,
        )

    with pytest.raises(ValueError):
        list_screenshots_by_status("invalid", db_path=db_path)

    with pytest.raises(LookupError):
        update_screenshot_ocr(999, ocr_text="x", ocr_status="done", db_path=db_path)
