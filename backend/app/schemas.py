from enum import Enum

from pydantic import BaseModel, field_validator


class TaskStatus(str, Enum):
    TODO = "TODO"
    IN_PROGRESS = "IN_PROGRESS"
    DONE = "DONE"


class Priority(str, Enum):
    NONE = "NONE"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


ASSIGNEE_MAX_LENGTH = 50


def _require_title(value: str) -> str:
    # D-010, D-011: 비어 있거나 공백만 있는 제목은 저장하지 않는다.
    value = value.strip()
    if not value:
        raise ValueError("제목은 비워 둘 수 없습니다.")
    return value


def _clean_assignee(value: str | None) -> str | None:
    # D-015: 담당자는 선택이고 짧은 문자열이다. 앞뒤 공백은 지운다.
    if value is None:
        return None
    value = value.strip()
    if len(value) > ASSIGNEE_MAX_LENGTH:
        raise ValueError(f"담당자는 {ASSIGNEE_MAX_LENGTH}자 이하여야 합니다.")
    return value


class TaskCreate(BaseModel):
    title: str
    description: str = ""
    priority: Priority = Priority.NONE
    assignee: str = ""

    _check_title = field_validator("title")(_require_title)
    _check_assignee = field_validator("assignee")(_clean_assignee)


class TaskUpdate(BaseModel):
    # 제목과 설명을 항상 함께 보낸다. 설명이 빠져 실수로 지워지는 일을 막는다.
    title: str
    description: str
    # 우선순위 · 담당자는 보내지 않으면 현재 값을 유지한다.
    priority: Priority | None = None
    assignee: str | None = None

    _check_title = field_validator("title")(_require_title)
    _check_assignee = field_validator("assignee")(_clean_assignee)


class TaskStatusUpdate(BaseModel):
    status: TaskStatus


class Task(BaseModel):
    id: int
    title: str
    description: str
    status: TaskStatus
    priority: Priority
    assignee: str
