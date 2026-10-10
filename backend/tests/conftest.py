import pytest
from backend.app.services import storage


@pytest.fixture(autouse=True)
def isolate_test_database(monkeypatch, tmp_path):
    """Isolates the SQLite database to a temporary directory for each test run.
    Prevents tests from clearing or polluting the production generations.db.
    """
    test_db = tmp_path / "test_generations.db"
    monkeypatch.setattr(storage, "DB_PATH", str(test_db))
    storage.init_db()
    yield
