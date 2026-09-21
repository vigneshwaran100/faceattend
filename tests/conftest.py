from unittest.mock import MagicMock
import pytest


@pytest.fixture(autouse=True)
def mock_startup_db_engine_connect(monkeypatch):
    """
    Prevent FastAPI lifespan startup from waiting on network timeouts
    when verifying database connection against a non-running local database during tests.
    """
    mock_conn = MagicMock()
    mock_conn.__enter__.return_value = mock_conn
    mock_conn.__exit__.return_value = None
    monkeypatch.setattr("app.api.main.engine.connect", lambda: mock_conn)
