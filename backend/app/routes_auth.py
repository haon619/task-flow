import sqlite3

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel, field_validator

from .auth import (
    COOKIE_NAME,
    current_user,
    hash_password,
    make_session,
    verify_password,
)
from .db import LEGACY_USERNAME, get_conn

router = APIRouter(prefix="/api/auth", tags=["auth"])


class Credentials(BaseModel):
    username: str
    password: str

    @field_validator("username")
    @classmethod
    def _username(cls, value: str) -> str:
        value = value.strip()
        if not value or len(value) > 50:
            raise ValueError("아이디는 1~50자여야 합니다.")
        return value

    @field_validator("password")
    @classmethod
    def _password(cls, value: str) -> str:
        if len(value) < 8:
            raise ValueError("비밀번호는 8자 이상이어야 합니다.")
        return value


class User(BaseModel):
    id: int
    username: str


def _set_session(response: Response, user_id: int) -> None:
    response.set_cookie(
        COOKIE_NAME, make_session(user_id), httponly=True, samesite="lax"
    )


@router.post("/register", status_code=201)
def register(
    body: Credentials, response: Response, conn: sqlite3.Connection = Depends(get_conn)
) -> User:
    if body.username == LEGACY_USERNAME:
        raise HTTPException(status_code=409, detail="이미 있는 아이디입니다.")
    try:
        cur = conn.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            (body.username, hash_password(body.password)),
        )
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=409, detail="이미 있는 아이디입니다.")
    conn.commit()
    _set_session(response, cur.lastrowid)
    return User(id=cur.lastrowid, username=body.username)


@router.post("/login")
def login(
    body: Credentials, response: Response, conn: sqlite3.Connection = Depends(get_conn)
) -> User:
    row = conn.execute(
        "SELECT * FROM users WHERE username = ?", (body.username,)
    ).fetchone()
    if row is None or not verify_password(body.password, row["password_hash"]):
        raise HTTPException(status_code=401, detail="아이디 또는 비밀번호가 맞지 않습니다.")
    _set_session(response, row["id"])
    return User(id=row["id"], username=row["username"])


@router.post("/logout", status_code=204)
def logout(response: Response) -> None:
    response.delete_cookie(COOKIE_NAME)


@router.get("/me")
def me(user: sqlite3.Row = Depends(current_user)) -> User:
    return User(id=user["id"], username=user["username"])
