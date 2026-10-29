import sqlite3
from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Response

from .auth import current_user
from .db import get_conn
from .schemas import Task, TaskCreate, TaskStatusUpdate, TaskUpdate, TaskStatus

router = APIRouter(prefix="/api/tasks", tags=["tasks"])

# "오늘"은 서버 시계의 한국 시간(KST) 날짜다. 고정 오프셋이라 tzdata가 필요 없다.
KST = timezone(timedelta(hours=9))
PRIORITY_ORDER = {"HIGH": 0, "NORMAL": 1, "LOW": 2}


def today() -> date:
    return datetime.now(KST).date()


def _is_overdue(row: sqlite3.Row, today_iso: str) -> bool:
    # 기한 초과: 마감일이 오늘보다 이전이고 완료가 아닐 때. 계산만 하고 저장하지 않는다.
    return (
        row["due_date"] is not None
        and row["due_date"] < today_iso
        and row["status"] != TaskStatus.DONE.value
    )


def _to_task(row: sqlite3.Row) -> Task:
    return Task(**dict(row), is_overdue=_is_overdue(row, today().isoformat()))


def _sort_key(row: sqlite3.Row, today_iso: str) -> tuple:
    # 기한 초과 → 우선순위 → 가까운 마감일(없으면 맨 뒤) → 만든 순서(ID)
    due = row["due_date"]
    return (
        not _is_overdue(row, today_iso),
        PRIORITY_ORDER[row["priority"]],
        due is None,
        due or "",
        row["id"],
    )


def _get_or_404(
    conn: sqlite3.Connection, task_id: int, owner_id: int
) -> sqlite3.Row:
    # D-017: 다른 사용자의 카드는 없는 카드와 똑같이 404로 답한다.
    row = conn.execute(
        "SELECT * FROM tasks WHERE id = ? AND owner_id = ?", (task_id, owner_id)
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="카드를 찾을 수 없습니다.")
    return row


@router.get("")
def list_tasks(
    conn: sqlite3.Connection = Depends(get_conn),
    user: sqlite3.Row = Depends(current_user),
) -> list[Task]:
    rows = conn.execute(
        "SELECT * FROM tasks WHERE owner_id = ?", (user["id"],)
    ).fetchall()
    today_iso = today().isoformat()
    rows.sort(key=lambda row: _sort_key(row, today_iso))
    return [_to_task(row) for row in rows]


@router.post("", status_code=201)
def create_task(
    body: TaskCreate, conn: sqlite3.Connection = Depends(get_conn),
    user: sqlite3.Row = Depends(current_user),
) -> Task:
    cur = conn.execute(
        "INSERT INTO tasks (title, description, status, priority, assignee, owner_id, "
        "due_date) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (
            body.title,
            body.description,
            TaskStatus.TODO.value,
            body.priority.value,
            body.assignee,
            user["id"],
            body.due_date,
        ),
    )
    conn.commit()
    return _to_task(_get_or_404(conn, cur.lastrowid, user["id"]))


@router.patch("/{task_id}")
def update_task(
    task_id: int, body: TaskUpdate, conn: sqlite3.Connection = Depends(get_conn),
    user: sqlite3.Row = Depends(current_user),
) -> Task:
    # 상태는 이 요청으로 바뀌지 않는다.
    current = _get_or_404(conn, task_id, user["id"])
    priority = body.priority.value if body.priority is not None else current["priority"]
    assignee = body.assignee if body.assignee is not None else current["assignee"]
    due_date = (
        body.due_date if "due_date" in body.model_fields_set else current["due_date"]
    )
    conn.execute(
        "UPDATE tasks SET title = ?, description = ?, priority = ?, assignee = ?, "
        "due_date = ? WHERE id = ? AND owner_id = ?",
        (body.title, body.description, priority, assignee, due_date, task_id, user["id"]),
    )
    conn.commit()
    return _to_task(_get_or_404(conn, task_id, user["id"]))


@router.patch("/{task_id}/status")
def update_task_status(
    task_id: int, body: TaskStatusUpdate, conn: sqlite3.Connection = Depends(get_conn),
    user: sqlite3.Row = Depends(current_user),
) -> Task:
    _get_or_404(conn, task_id, user["id"])
    conn.execute(
        "UPDATE tasks SET status = ? WHERE id = ? AND owner_id = ?",
        (body.status.value, task_id, user["id"]),
    )
    conn.commit()
    return _to_task(_get_or_404(conn, task_id, user["id"]))


@router.delete("/{task_id}", status_code=204)
def delete_task(
    task_id: int,
    conn: sqlite3.Connection = Depends(get_conn),
    user: sqlite3.Row = Depends(current_user),
) -> Response:
    _get_or_404(conn, task_id, user["id"])
    conn.execute(
        "DELETE FROM tasks WHERE id = ? AND owner_id = ?", (task_id, user["id"])
    )
    conn.commit()
    return Response(status_code=204)
