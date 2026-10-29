from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient

from app.main import app

ALEMBIC_INI = Path(__file__).resolve().parent.parent / "alembic.ini"


@pytest.fixture(autouse=True)
def session_secret(monkeypatch):
    monkeypatch.setenv("SESSION_SECRET", "test-secret-not-for-production")


@pytest.fixture
def db_file(tmp_path, monkeypatch):
    path = tmp_path / "test.db"
    monkeypatch.setenv("TASK_FLOW_DB", str(path))
    return path


@pytest.fixture
def upgrade(db_file):
    """db_file에 대해 `alembic upgrade head`를 실행하는 함수. 실제 DB가 아니라 임시 DB만 쓴다."""

    def run() -> None:
        command.upgrade(Config(str(ALEMBIC_INI)), "head")

    return run


def _register(c: TestClient, username: str) -> None:
    res = c.post(
        "/api/auth/register", json={"username": username, "password": "password-1234"}
    )
    assert res.status_code == 201


@pytest.fixture
def client(db_file):
    # with 블록으로 lifespan(init_db)을 실행한다. 기본 클라이언트는 alice로 로그인되어 있다.
    with TestClient(app) as c:
        _register(c, "alice")
        yield c


@pytest.fixture
def other_client(client):
    """다른 사용자(bob)로 로그인된 클라이언트. client와 같은 DB를 쓴다."""
    c = TestClient(app)
    _register(c, "bob")
    yield c
    c.close()


@pytest.fixture
def anon_client(client):
    c = TestClient(app)
    yield c
    c.close()
