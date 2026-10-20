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


class TaskUpdate(BaseModel):
    # 제목과 설명을 항상 함께 보낸다. 설명이 빠져 실수로 지워지는 일을 막는다.
    title: str
    description: str

    _check_title = field_validator("title")(_require_title)


class TaskStatusUpdate(BaseModel):
    status: TaskStatus


class Task(BaseModel):
    id: int
    title: str
    description: str
    status: TaskStatus
