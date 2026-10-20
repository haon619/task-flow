import sqlite3

from fastapi import APIRouter, Depends

from .db import get_conn
from .schemas import Task, TaskCreate, TaskStatus

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


def _to_task(row: sqlite3.Row) -> Task:
    return Task(**dict(row))


@router.get("")
def list_tasks(conn: sqlite3.Connection = Depends(get_conn)) -> list[Task]:
    rows = conn.execute("SELECT * FROM tasks ORDER BY id").fetchall()
    return [_to_task(row) for row in rows]


@router.post("", status_code=201)
def create_task(
    body: TaskCreate, conn: sqlite3.Connection = Depends(get_conn)
) -> Task:
    cur = conn.execute(
        "INSERT INTO tasks (title, description, status) VALUES (?, ?, ?)",
        (body.title, body.description, TaskStatus.TODO.value),
    )
    conn.commit()
    row = conn.execute("SELECT * FROM tasks WHERE id = ?", (cur.lastrowid,)).fetchone()
    return _to_task(row)
