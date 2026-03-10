from pathlib import Path

import pytest

from recall.db.database import DEFAULT_SETTINGS, init_db
from recall.db.setting import delete_setting, get_all_settings, get_setting, set_setting, update_settings


@pytest.fixture
def db_path(tmp_path: Path) -> Path:
    path = tmp_path / "recall.db"
    init_db(path)
    return path


def test_setting_crud_success(db_path: Path) -> None:
    settings = get_all_settings(db_path)
    assert settings["CHANGE_THRESHOLD"] == "5"
    assert len(settings) == len(DEFAULT_SETTINGS)

    assert set_setting("CHANGE_THRESHOLD", "8", db_path) == "8"
    assert get_setting("CHANGE_THRESHOLD", db_path) == "8"

    result = update_settings({"OCR_BATCH_SIZE": "12", "NEW_KEY": "x"}, db_path)
    assert result["OCR_BATCH_SIZE"] == "12"
    assert result["NEW_KEY"] == "x"

    assert delete_setting("NEW_KEY", db_path) is True
    assert get_setting("NEW_KEY", db_path) is None


def test_setting_error_paths(db_path: Path) -> None:
    with pytest.raises(ValueError):
        set_setting("", "1", db_path)

    with pytest.raises(ValueError):
        update_settings({" ": "1"}, db_path)
