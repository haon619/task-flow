import importlib.util
import sqlite3
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app import db
from app.main import app

REVISION = (
    Path(__file__).resolve().parent.parent
    / "migrations"
    / "versions"
    / "0001_priority_normal_due_date_owner.py"
)

OLD_TASKS = (
    "CREATE TABLE tasks (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, "
    "description TEXT NOT NULL DEFAULT '', status TEXT NOT NULL DEFAULT 'TODO', "
    "priority TEXT NOT NULL DEFAULT 'NONE' "
    "CHECK (priority IN ('NONE', 'LOW', 'MEDIUM', 'HIGH')), "
    "assignee TEXT NOT NULL DEFAULT '', owner_id INTEGER REFERENCES users(id))"
)


def _old_db(path, titles=("a", "b", "c")):
    conn = sqlite3.connect(path)
    conn.execute(
        "CREATE TABLE users (id INTEGER PRIMARY KEY AUTOINCREMENT, "
        "username TEXT NOT NULL UNIQUE, password_hash TEXT NOT NULL)"
    )
    conn.execute(OLD_TASKS)
    conn.execute("INSERT INTO users (username, password_hash) VALUES ('u', '!')")
    conn.executemany(
        "INSERT INTO tasks (title, owner_id) VALUES (?, 1)", [(t,) for t in titles]
    )
    conn.commit()
    return conn


def test_app_refuses_to_start_on_old_format_db(db_file):
    _old_db(db_file).close()
    with pytest.raises(RuntimeError, match="alembic upgrade head"):
        db.init_db()
    # 거절만 하고 DB는 그대로다.
    conn = sqlite3.connect(db_file)
    assert conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0] == 3
    assert "'NONE'" in conn.execute(
        "SELECT sql FROM sqlite_master WHERE name = 'tasks'"
    ).fetchone()[0]
    conn.close()


def test_upgrade_on_new_db_changes_nothing(db_file, upgrade):
    # 앱이 만든 새 DB에 alembic을 실행해도 카드와 구조가 그대로다.
    with TestClient(app) as c:
        c.post("/api/auth/register", json={"username": "alice", "password": "password-1234"})
        c.post("/api/tasks", json={"title": "keep", "due_date": "2026-11-01"})
    conn = sqlite3.connect(db_file)
    before = conn.execute("SELECT sql FROM sqlite_master WHERE name = 'tasks'").fetchone()
    conn.close()
    upgrade()
    conn = sqlite3.connect(db_file)
    assert conn.execute("SELECT title, due_date FROM tasks").fetchall() == [("keep", "2026-11-01")]
    assert conn.execute("SELECT sql FROM sqlite_master WHERE name = 'tasks'").fetchone() == before
    conn.close()


def test_upgrade_creates_schema_when_db_is_empty(db_file, upgrade):
    upgrade()
    conn = sqlite3.connect(db_file)
    columns = {r[1] for r in conn.execute("PRAGMA table_info(tasks)")}
    conn.close()
    assert {"priority", "assignee", "owner_id", "due_date"} <= columns
    db.init_db()  # 새 형식이라 거절하지 않는다


def test_upgrade_keeps_id_counter_and_tables(db_file, upgrade):
    # 가장 큰 id의 카드를 지웠어도 새 카드가 그 id를 다시 쓰지 않는다.
    conn = _old_db(db_file)
    conn.execute("DELETE FROM tasks WHERE id = 3")
    conn.commit()
    conn.close()
    upgrade()
    conn = sqlite3.connect(db_file)
    conn.execute("INSERT INTO tasks (title, owner_id) VALUES ('new', 1)")
    conn.commit()
    ids = [r[0] for r in conn.execute("SELECT id FROM tasks ORDER BY id")]
    names = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    conn.close()
    assert ids == [1, 2, 4]
    assert "tasks_new" not in names and "alembic_version" in names


def test_upgrade_assigns_orphans_to_legacy_and_logs_nothing_else(db_file, upgrade):
    conn = _old_db(db_file)
    conn.execute("INSERT INTO tasks (title, owner_id) VALUES ('orphan', NULL)")
    conn.commit()
    conn.close()
    upgrade()
    conn = sqlite3.connect(db_file)
    assert conn.execute("SELECT COUNT(*) FROM tasks WHERE owner_id IS NULL").fetchone()[0] == 0
    owner = conn.execute(
        "SELECT u.username FROM tasks t JOIN users u ON u.id = t.owner_id WHERE t.title = 'orphan'"
    ).fetchone()[0]
    conn.close()
    assert owner == "legacy"


def test_revision_has_no_downgrade():
    # 되돌리기는 적용 전에 받아 둔 DB 백업 파일로 한다.
    spec = importlib.util.spec_from_file_location("rev0001", REVISION)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.revision == "0001"
    assert not hasattr(module, "downgrade")
