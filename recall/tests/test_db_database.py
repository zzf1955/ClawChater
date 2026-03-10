import sqlite3
from pathlib import Path

from recall.db.database import DEFAULT_SETTINGS, init_db


def test_init_db_is_idempotent(tmp_path: Path) -> None:
    db_path = tmp_path / "recall.db"

    init_db(db_path)
    init_db(db_path)

    assert db_path.exists()

    with sqlite3.connect(db_path) as conn:
        tables = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name IN ('screenshots', 'summaries', 'settings')"
            ).fetchall()
        }
        assert tables == {"screenshots", "summaries", "settings"}

        key_count = conn.execute("SELECT COUNT(*) FROM settings").fetchone()[0]
        assert key_count == len(DEFAULT_SETTINGS)

        duplicates = conn.execute(
            "SELECT key, COUNT(*) FROM settings GROUP BY key HAVING COUNT(*) > 1"
        ).fetchall()
        assert duplicates == []


def test_index_query_plan_smoke(tmp_path: Path) -> None:
    db_path = tmp_path / "recall.db"
    init_db(db_path)

    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            INSERT INTO screenshots(captured_at, file_path, ocr_status)
            VALUES
              ('2026-03-10T10:00:00Z', 'screenshots/a.jpg', 'pending'),
              ('2026-03-10T10:01:00Z', 'screenshots/b.jpg', 'done'),
              ('2026-03-10T10:02:00Z', 'screenshots/c.jpg', 'error')
            """
        )
        conn.execute(
            """
            INSERT INTO summaries(start_time, end_time, summary)
            VALUES ('2026-03-10T10:00:00Z', '2026-03-10T11:00:00Z', 'work log')
            """
        )

        status_plan = " ".join(
            row[3]
            for row in conn.execute(
                "EXPLAIN QUERY PLAN SELECT * FROM screenshots WHERE ocr_status = 'pending'"
            ).fetchall()
        )
        captured_plan = " ".join(
            row[3]
            for row in conn.execute(
                "EXPLAIN QUERY PLAN SELECT * FROM screenshots WHERE captured_at >= '2026-03-10T10:00:00Z'"
            ).fetchall()
        )
        summary_plan = " ".join(
            row[3]
            for row in conn.execute(
                "EXPLAIN QUERY PLAN SELECT * FROM summaries WHERE start_time >= '2026-03-10T10:00:00Z' AND end_time <= '2026-03-10T11:00:00Z'"
            ).fetchall()
        )

    assert "idx_screenshots_ocr_status" in status_plan
    assert "idx_screenshots_captured_at" in captured_plan
    assert "idx_summaries_time" in summary_plan
