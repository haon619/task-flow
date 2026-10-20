import sqlite3

from fastapi import APIRouter, Depends, HTTPException, Response

from .db import get_conn
from .schemas import Task, TaskCreate, TaskStatusUpdate, TaskUpdate, TaskStatus

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


def _to_task(row: sqlite3.Row) -> Task:
    return Task(**dict(row))


def _get_or_404(conn: sqlite3.Connection, task_id: int) -> sqlite3.Row:
    row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="카드를 찾을 수 없습니다.")
    return row


@router.get("")
def list_tasks(conn: sqlite3.Connection = Depends(get_conn)) -> list[Task]:
    rows = conn.execute("SELECT * FROM tasks ORDER BY id").fetchall()
    return [_to_task(row) for row in rows]


@router.post("", status_code=201)
def create_task(
    body: TaskCreate, conn: sqlite3.Connection = Depends(get_conn)
) -> Task:
    cur = conn.execute(
        "INSERT INTO tasks (title, description, status, priority, assignee) "
        "VALUES (?, ?, ?, ?, ?)",
        (
            body.title,
            body.description,
            TaskStatus.TODO.value,
            body.priority.value,
            body.assignee,
        ),
    )
    conn.commit()
    return _to_task(_get_or_404(conn, cur.lastrowid))


@router.patch("/{task_id}")
def update_task(
    task_id: int, body: TaskUpdate, conn: sqlite3.Connection = Depends(get_conn)
) -> Task:
    # 상태는 이 요청으로 바뀌지 않는다.
    current = _get_or_404(conn, task_id)
    priority = body.priority.value if body.priority is not None else current["priority"]
    assignee = body.assignee if body.assignee is not None else current["assignee"]
    conn.execute(
        "UPDATE tasks SET title = ?, description = ?, priority = ?, assignee = ? "
        "WHERE id = ?",
        (body.title, body.description, priority, assignee, task_id),
    )
    conn.commit()
    return _to_task(_get_or_404(conn, task_id))


@router.patch("/{task_id}/status")
def update_task_status(
    task_id: int, body: TaskStatusUpdate, conn: sqlite3.Connection = Depends(get_conn)
) -> Task:
    _get_or_404(conn, task_id)
    conn.execute(
        "UPDATE tasks SET status = ? WHERE id = ?", (body.status.value, task_id)
    )
    conn.commit()
    return _to_task(_get_or_404(conn, task_id))


@router.delete("/{task_id}", status_code=204)
def delete_task(task_id: int, conn: sqlite3.Connection = Depends(get_conn)) -> Response:
    _get_or_404(conn, task_id)
    conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()
    return Response(status_code=204)
