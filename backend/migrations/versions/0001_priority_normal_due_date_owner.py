"""priority NORMAL, due_date, owner

기존 DB를 지금 형식으로 옮긴다. (D-018, D-019, #19)
- users 테이블과 tasks.owner_id: 주인 없는 카드는 로그인할 수 없는 legacy 사용자에게 붙인다.
- tasks.assignee, tasks.due_date: 없으면 기본값(빈 문자열, 마감일 없음)으로 채운다.
- tasks.priority: CHECK를 LOW · NORMAL · HIGH로 바꾼다. NONE · MEDIUM은 NORMAL이 된다.

SQLite는 CHECK를 ALTER로 못 바꿔서 새 테이블에 복사한 뒤 바꿔치기한다.
이미 지금 형식인 DB는 아무것도 바꾸지 않는다. 되돌리기(downgrade)는 만들지 않는다.
되돌리려면 적용 전에 받아 둔 DB 백업 파일로 바꾼다.

Revision ID: 0001
Revises:
Create Date: 2026-10-29 10:29:24.846555

"""
from typing import Sequence, Union

from alembic import op

revision: str = "0001"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# 마이그레이션이 앱 코드 변경에 흔들리지 않게 이 시점의 형식을 여기에 복사해 둔다.
USERS_SQL = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL
)
"""

TASKS_SQL = """
CREATE TABLE {name} (
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

LEGACY_USERNAME = "legacy"
NEW_COLUMNS = {"priority", "assignee", "owner_id", "due_date"}


def _scalar(conn, sql: str):
    return conn.exec_driver_sql(sql).fetchone()[0]


def upgrade() -> None:
    conn = op.get_bind()
    conn.exec_driver_sql(USERS_SQL)

    table_sql = conn.exec_driver_sql(
        "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = 'tasks'"
    ).fetchone()
    if table_sql is None:
        # 카드 테이블이 아직 없는 새 DB
        conn.exec_driver_sql(TASKS_SQL.format(name="tasks"))
        return

    columns = {row[1] for row in conn.exec_driver_sql("PRAGMA table_info(tasks)")}
    if NEW_COLUMNS <= columns and "MEDIUM" not in table_sql[0] and "'NONE'" not in table_sql[0]:
        return  # 이미 지금 형식이다

    before = _scalar(conn, "SELECT COUNT(*) FROM tasks")
    ids_before = conn.exec_driver_sql("SELECT id FROM tasks ORDER BY id").fetchall()
    seq_row = (
        conn.exec_driver_sql(
            "SELECT seq FROM sqlite_sequence WHERE name = 'tasks'"
        ).fetchone()
        if conn.exec_driver_sql(
            "SELECT 1 FROM sqlite_master WHERE name = 'sqlite_sequence'"
        ).fetchone()
        else None
    )

    if "priority" in columns:
        priority = (
            "CASE priority WHEN 'LOW' THEN 'LOW' WHEN 'HIGH' THEN 'HIGH' ELSE 'NORMAL' END"
        )
    else:
        priority = "'NORMAL'"
    assignee = "assignee" if "assignee" in columns else "''"
    owner = "owner_id" if "owner_id" in columns else "NULL"
    due = "due_date" if "due_date" in columns else "NULL"

    # 복사에 실패해도 원래 tasks는 그대로 남도록, 새 테이블이 맞는지 확인한 뒤에 바꿔치기한다.
    conn.exec_driver_sql("DROP TABLE IF EXISTS tasks_new")
    conn.exec_driver_sql(TASKS_SQL.format(name="tasks_new"))
    conn.exec_driver_sql(
        "INSERT INTO tasks_new (id, title, description, status, priority, assignee, "
        "owner_id, due_date) SELECT id, title, description, status, "
        f"{priority}, {assignee}, {owner}, {due} FROM tasks"
    )

    orphans = _scalar(conn, "SELECT COUNT(*) FROM tasks_new WHERE owner_id IS NULL")
    if orphans:
        # '!'는 scrypt 해시 형식이 아니라 어떤 비밀번호로도 로그인할 수 없다.
        conn.exec_driver_sql(
            "INSERT OR IGNORE INTO users (username, password_hash) "
            f"VALUES ('{LEGACY_USERNAME}', '!')"
        )
        conn.exec_driver_sql(
            "UPDATE tasks_new SET owner_id = "
            f"(SELECT id FROM users WHERE username = '{LEGACY_USERNAME}') "
            "WHERE owner_id IS NULL"
        )

    ids_after = conn.exec_driver_sql("SELECT id FROM tasks_new ORDER BY id").fetchall()
    bad = _scalar(
        conn,
        "SELECT COUNT(*) FROM tasks_new WHERE owner_id IS NULL "
        "OR priority NOT IN ('LOW', 'NORMAL', 'HIGH')",
    )
    if len(ids_after) != before or ids_after != ids_before or bad:
        conn.exec_driver_sql("DROP TABLE tasks_new")
        raise RuntimeError(
            f"이전 검증 실패: 카드 {before}건 → {len(ids_after)}건, 주인 없음·잘못된 우선순위 {bad}건. "
            "DB는 바꾸지 않았다."
        )

    # 자동 증가 번호가 줄지 않게 이전 값을 이어 간다.
    keep_seq = max([seq_row[0] if seq_row else 0] + [row[0] for row in ids_after])
    conn.exec_driver_sql("DROP TABLE tasks")
    conn.exec_driver_sql("ALTER TABLE tasks_new RENAME TO tasks")
    conn.exec_driver_sql(
        f"UPDATE sqlite_sequence SET seq = {int(keep_seq)} WHERE name = 'tasks'"
    )
