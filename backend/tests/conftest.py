import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def db_file(tmp_path, monkeypatch):
    path = tmp_path / "test.db"
    monkeypatch.setenv("TASK_FLOW_DB", str(path))
    return path


@pytest.fixture
def client(db_file):
    # with 블록으로 lifespan(init_db)을 실행한다.
    with TestClient(app) as c:
        yield c
