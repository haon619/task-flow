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

# 이전에 만든 DB에 없는 컬럼. 기존 카드는 그대로 두고 기본값으로 채운다.
ADDED_COLUMNS = {
    "priority": "TEXT NOT NULL DEFAULT 'NORMAL' "
    "CHECK (priority IN ('LOW', 'NORMAL', 'HIGH'))",
    "assignee": "TEXT NOT NULL DEFAULT ''",
    "owner_id": "INTEGER REFERENCES users(id)",
    "due_date": "TEXT",
}

COLUMNS = "id, title, description, status, priority, assignee, owner_id, due_date"


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
        migrate_priority(conn)
        assign_orphans_to_legacy(conn)
        conn.commit()
    finally:
        conn.close()


def migrate_priority(conn: sqlite3.Connection) -> bool:
    """D-019: 우선순위 CHECK를 LOW · NORMAL · HIGH로 바꾼다. 바꿨으면 True.

    SQLite는 CHECK 제약을 ALTER로 못 바꿔서 테이블을 다시 만든다.
    NONE · MEDIUM은 NORMAL로, LOW · HIGH와 나머지 값은 그대로 옮긴다.
    """
    sql = conn.execute(
        "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = 'tasks'"
    ).fetchone()["sql"]
    if "MEDIUM" not in sql and "'NONE'" not in sql:
        return False
    conn.commit()
    conn.execute("BEGIN")
    try:
        seq = conn.execute(
            "SELECT seq FROM sqlite_sequence WHERE name = 'tasks'"
        ).fetchone()
        conn.execute("ALTER TABLE tasks RENAME TO tasks_old")
        conn.execute(SCHEMA)
        conn.execute(
            f"INSERT INTO tasks ({COLUMNS}) SELECT id, title, description, status, "
            "CASE priority WHEN 'LOW' THEN 'LOW' WHEN 'HIGH' THEN 'HIGH' "
            "ELSE 'NORMAL' END, assignee, owner_id, due_date FROM tasks_old"
        )
        conn.execute("DROP TABLE tasks_old")
        if seq is not None:
            conn.execute(
                "UPDATE sqlite_sequence SET seq = ? WHERE name = 'tasks'",
                (seq["seq"],),
            )
        conn.execute("COMMIT")
    except Exception:
        conn.execute("ROLLBACK")
        raise
    return True


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
