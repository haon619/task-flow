import sqlite3
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from .auth import session_secret
from .db import init_db
from .routes_auth import router as auth_router
from .routes_tasks import router as tasks_router


@asynccontextmanager
async def lifespan(_: FastAPI):
    session_secret()  # 비밀값이 없으면 시작하지 않는다.
    init_db()
    yield


app = FastAPI(title="task-flow", lifespan=lifespan)
app.include_router(auth_router)
app.include_router(tasks_router)


@app.exception_handler(sqlite3.Error)
async def storage_error_handler(_: Request, __: sqlite3.Error) -> JSONResponse:
    # 저장소 실패는 저장된 것으로 취급하지 않고 500으로 알린다.
    return JSONResponse(
        status_code=500, content={"detail": "저장소에 접근하지 못했습니다."}
    )


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
