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
    priority TEXT NOT NULL DEFAULT 'NONE'
        CHECK (priority IN ('NONE', 'LOW', 'MEDIUM', 'HIGH')),
    assignee TEXT NOT NULL DEFAULT '',
    owner_id INTEGER REFERENCES users(id)
)
"""

# R-008 이전에 만든 DB에 없는 컬럼. 기존 카드는 그대로 두고 기본값으로 채운다.
ADDED_COLUMNS = {
    "priority": "TEXT NOT NULL DEFAULT 'NONE' "
    "CHECK (priority IN ('NONE', 'LOW', 'MEDIUM', 'HIGH'))",
    "assignee": "TEXT NOT NULL DEFAULT ''",
    "owner_id": "INTEGER REFERENCES users(id)",
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
        conn.execute(USERS_SCHEMA)
        conn.execute(SCHEMA)
        existing = {row["name"] for row in conn.execute("PRAGMA table_info(tasks)")}
        for column, definition in ADDED_COLUMNS.items():
            if column not in existing:
                conn.execute(f"ALTER TABLE tasks ADD COLUMN {column} {definition}")
        assign_orphans_to_legacy(conn)
        conn.commit()
    finally:
        conn.close()


def assign_orphans_to_legacy(conn: sqlite3.Connection) -> int:
    """D-018: 주인 없는 카드를 로그인할 수 없는 legacy 사용자에게 붙인다. 붙인 수를 돌려준다."""
    orphans = conn.execute(
        "SELECT COUNT(*) FROM tasks WHERE owner_id IS NULL"
    ).fetchone()[0]
    if orphans == 0:
        return 0
    # '!'는 scrypt 해시 형식이 아니라 어떤 비밀번호로도 로그인할 수 없다.
    conn.execute(
        "INSERT OR IGNORE INTO users (username, password_hash) VALUES (?, '!')",
        (LEGACY_USERNAME,),
    )
    conn.execute(
        "UPDATE tasks SET owner_id = "
        "(SELECT id FROM users WHERE username = ?) WHERE owner_id IS NULL",
        (LEGACY_USERNAME,),
    )
    return orphans


def get_conn() -> Iterator[sqlite3.Connection]:
    conn = connect()
    try:
        yield conn
    finally:
        conn.close()
