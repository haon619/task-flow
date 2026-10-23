import hashlib
import hmac
import os
import secrets
import sqlite3
from pathlib import Path

from fastapi import Depends, HTTPException, Request

from .db import get_conn

COOKIE_NAME = "session"
ENV_FILE = Path(__file__).resolve().parent.parent / ".env"
SCRYPT_PARAMS = {"n": 2**14, "r": 8, "p": 1}


def session_secret() -> bytes:
    # D-016: 비밀값은 환경 변수나 Git에 넣지 않는 backend/.env에서만 받는다.
    value = os.environ.get("SESSION_SECRET", "")
    if not value and ENV_FILE.exists():
        for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
            key, _, val = line.partition("=")
            if key.strip() == "SESSION_SECRET":
                value = val.strip()
    if not value:
        raise RuntimeError("SESSION_SECRET이 없습니다. backend/.env에 설정하세요.")
    return value.encode()


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(password.encode(), salt=salt, **SCRYPT_PARAMS)
    return f"scrypt${salt.hex()}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    # 로그인할 수 없는 계정(legacy)의 해시는 scrypt 형식이 아니라 항상 거절한다.
    try:
        scheme, salt_hex, digest_hex = stored.split("$")
    except ValueError:
        return False
    if scheme != "scrypt":
        return False
    digest = hashlib.scrypt(password.encode(), salt=bytes.fromhex(salt_hex), **SCRYPT_PARAMS)
    return hmac.compare_digest(digest.hex(), digest_hex)


def _sign(user_id: int) -> str:
    return hmac.new(session_secret(), str(user_id).encode(), hashlib.sha256).hexdigest()


def make_session(user_id: int) -> str:
    return f"{user_id}.{_sign(user_id)}"


def read_session(token: str | None) -> int | None:
    if not token:
        return None
    user_id, _, sig = token.partition(".")
    if not user_id.isdigit() or not hmac.compare_digest(sig, _sign(int(user_id))):
        return None
    return int(user_id)


def current_user(
    request: Request, conn: sqlite3.Connection = Depends(get_conn)
) -> sqlite3.Row:
    # D-017: 로그인하지 않았거나 세션이 잘못되면 401.
    user_id = read_session(request.cookies.get(COOKIE_NAME))
    row = (
        conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        if user_id is not None
        else None
    )
    if row is None:
        raise HTTPException(status_code=401, detail="로그인이 필요합니다.")
    return row
