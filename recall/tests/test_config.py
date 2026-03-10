from pathlib import Path

from recall import config


def test_paths_are_under_project() -> None:
    assert config.BASE_DIR.name == "recall"
    assert config.DATA_DIR == config.BASE_DIR / "data"
    assert config.SCREENSHOTS_DIR == config.DATA_DIR / "screenshots"


def test_ensure_data_dirs_creates_required_paths(tmp_path: Path, monkeypatch) -> None:
    data_dir = tmp_path / "data"
    screenshots_dir = data_dir / "screenshots"

    monkeypatch.setattr(config, "DATA_DIR", data_dir)
    monkeypatch.setattr(config, "SCREENSHOTS_DIR", screenshots_dir)

    config.ensure_data_dirs()

    assert data_dir.exists()
    assert screenshots_dir.exists()
