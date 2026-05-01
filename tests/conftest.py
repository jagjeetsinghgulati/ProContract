from __future__ import annotations

import os
from pathlib import Path

import pytest

from config import get_settings
from data_model.persistence import init_db


@pytest.fixture(autouse=True)
def isolated_db(tmp_path: Path):
    db_path = tmp_path / "test_procontracts.db"
    if db_path.exists():
        db_path.unlink()
    os.environ["DB_PATH"] = str(db_path)
    get_settings.cache_clear()
    init_db()
    yield
