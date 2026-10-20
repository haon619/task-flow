from enum import Enum

from pydantic import BaseModel, field_validator


class TaskStatus(str, Enum):
    TODO = "TODO"
    IN_PROGRESS = "IN_PROGRESS"
    DONE = "DONE"


def _require_title(value: str) -> str:
    # D-010, D-011: 비어 있거나 공백만 있는 제목은 저장하지 않는다.
    value = value.strip()
    if not value:
        raise ValueError("제목은 비워 둘 수 없습니다.")
    return value


class TaskCreate(BaseModel):
    title: str
    description: str = ""

    _check_title = field_validator("title")(_require_title)


class Task(BaseModel):
    id: int
    title: str
    description: str
    status: TaskStatus
