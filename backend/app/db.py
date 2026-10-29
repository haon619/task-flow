import os
import sqlite3
from collections.abc import Iterator
from pathlib import Path

DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "data" / "task-flow.db"

LEGACY_USERNAME = "legacy"

USERS_SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL
)
"""

SCHEMA = """
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'TODO'
        CHECK (status IN ('TODO', 'IN_PROGRESS', 'DONE')),
    priority TEXT NOT NULL DEFAULT 'NORMAL'
        CHECK (priority IN ('LOW', 'NORMAL', 'HIGH')),
    assignee TEXT NOT NULL DEFAULT '',
    owner_id INTEGER REFERENCES users(id),
    due_date TEXT
)
"""

REQUIRED_COLUMNS = {"priority", "assignee", "owner_id", "due_date"}


def db_path() -> Path:
    return Path(os.environ.get("TASK_FLOW_DB", DEFAULT_DB_PATH))


def connect() -> sqlite3.Connection:
    path = db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = connect()
    try:
        # 없는 DB는 지금 형식으로 만든다. 이미 있는 DB의 형식 변경은 alembic이 한다.
        conn.execute(USERS_SCHEMA)
        conn.execute(SCHEMA)
        conn.commit()
        if not is_current(conn):
            raise RuntimeError(
                "DB가 이전 형식입니다. DB 파일을 백업한 뒤 backend에서 "
                "`uv run alembic upgrade head`를 실행하세요."
            )
    finally:
        conn.close()


def is_current(conn: sqlite3.Connection) -> bool:
    """tasks가 지금 형식(필수 컬럼이 있고 우선순위가 LOW · NORMAL · HIGH)인지."""
    columns = {row["name"] for row in conn.execute("PRAGMA table_info(tasks)")}
    sql = conn.execute(
        "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = 'tasks'"
    ).fetchone()["sql"]
    return REQUIRED_COLUMNS <= columns and "MEDIUM" not in sql and "'NONE'" not in sql


def get_conn() -> Iterator[sqlite3.Connection]:
    conn = connect()
    try:
        yield conn
    finally:
        conn.close()
