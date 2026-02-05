from pathlib import Path

from app.core import models
from app.core import paths


def test_init_db_creates_sqlite_in_app_support(tmp_path, monkeypatch) -> None:
    app_support = tmp_path / "Library" / "Application Support" / "Motherload"

    def fake_app_data_dir() -> Path:
        app_support.mkdir(parents=True, exist_ok=True)
        return app_support

    monkeypatch.setattr(paths, "get_app_data_dir", fake_app_data_dir)

    db_path = models.init_db()

    assert db_path == app_support / "motherload.sqlite"
    assert db_path.exists()
