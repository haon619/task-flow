import os
import sqlite3
from collections.abc import Iterator
from pathlib import Path

DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "data" / "task-flow.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'TODO'
        CHECK (status IN ('TODO', 'IN_PROGRESS', 'DONE')),
    priority TEXT NOT NULL DEFAULT 'NONE'
        CHECK (priority IN ('NONE', 'LOW', 'MEDIUM', 'HIGH')),
    assignee TEXT NOT NULL DEFAULT ''
)
"""

# R-008 이전에 만든 DB에 없는 컬럼. 기존 카드는 그대로 두고 기본값으로 채운다.
ADDED_COLUMNS = {
    "priority": "TEXT NOT NULL DEFAULT 'NONE' "
    "CHECK (priority IN ('NONE', 'LOW', 'MEDIUM', 'HIGH'))",
    "assignee": "TEXT NOT NULL DEFAULT ''",
}


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
        conn.execute(SCHEMA)
        existing = {row["name"] for row in conn.execute("PRAGMA table_info(tasks)")}
        for column, definition in ADDED_COLUMNS.items():
            if column not in existing:
                conn.execute(f"ALTER TABLE tasks ADD COLUMN {column} {definition}")
        conn.commit()
    finally:
        conn.close()


def get_conn() -> Iterator[sqlite3.Connection]:
    conn = connect()
    try:
        yield conn
    finally:
        conn.close()
