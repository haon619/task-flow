import sqlite3

from app import db

TASK = {"title": "내 할 일", "description": "설명"}


def test_anonymous_gets_401_everywhere(anon_client):
    assert anon_client.get("/api/tasks").status_code == 401
    assert anon_client.post("/api/tasks", json=TASK).status_code == 401
    assert anon_client.patch("/api/tasks/1", json=TASK).status_code == 401
    assert (
        anon_client.patch("/api/tasks/1/status", json={"status": "DONE"}).status_code
        == 401
    )
    assert anon_client.delete("/api/tasks/1").status_code == 401
    assert anon_client.get("/api/auth/me").status_code == 401


def test_forged_cookie_gets_401(anon_client):
    anon_client.cookies.set("session", "1.deadbeef")
    assert anon_client.get("/api/tasks").status_code == 401


def test_other_users_task_is_404_not_403(client, other_client):
    task_id = client.post("/api/tasks", json=TASK).json()["id"]
    assert other_client.patch(f"/api/tasks/{task_id}", json=TASK).status_code == 404
    assert (
        other_client.patch(
            f"/api/tasks/{task_id}/status", json={"status": "DONE"}
        ).status_code
        == 404
    )
    assert other_client.delete(f"/api/tasks/{task_id}").status_code == 404
    # 없는 카드와 응답이 같아 존재 여부가 새지 않는다.
    missing = other_client.delete("/api/tasks/9999")
    assert other_client.delete(f"/api/tasks/{task_id}").json() == missing.json()
    # 주인의 카드는 그대로다.
    mine = client.get("/api/tasks").json()
    assert [t["id"] for t in mine] == [task_id]
    assert mine[0]["status"] == "TODO"


def test_list_shows_only_own_tasks(client, other_client):
    client.post("/api/tasks", json=TASK)
    other_client.post("/api/tasks", json={"title": "bob 것"})
    assert [t["title"] for t in client.get("/api/tasks").json()] == ["내 할 일"]
    assert [t["title"] for t in other_client.get("/api/tasks").json()] == ["bob 것"]


def test_login_logout_flow(anon_client):
    bad = anon_client.post(
        "/api/auth/login", json={"username": "alice", "password": "wrong-password"}
    )
    assert bad.status_code == 401
    res = anon_client.post(
        "/api/auth/login", json={"username": "alice", "password": "password-1234"}
    )
    assert res.status_code == 200
    assert anon_client.get("/api/auth/me").json()["username"] == "alice"
    anon_client.post("/api/auth/logout")
    assert anon_client.get("/api/tasks").status_code == 401


def test_duplicate_username_is_409(anon_client):
    res = anon_client.post(
        "/api/auth/register", json={"username": "alice", "password": "password-1234"}
    )
    assert res.status_code == 409


def test_no_hash_in_responses_and_password_not_stored_plain(client, db_file):
    res = client.get("/api/auth/me")
    assert set(res.json()) == {"id", "username"}
    assert "password" not in res.text and "scrypt" not in res.text
    conn = sqlite3.connect(db_file)
    stored = conn.execute(
        "SELECT password_hash FROM users WHERE username = 'alice'"
    ).fetchone()[0]
    conn.close()
    assert stored.startswith("scrypt$") and "password-1234" not in stored


def test_legacy_cannot_login_or_register(anon_client):
    for path in ("login", "register"):
        res = anon_client.post(
            f"/api/auth/{path}",
            json={"username": "legacy", "password": "password-1234"},
        )
        assert res.status_code in (401, 409)


def test_migration_keeps_all_tasks_and_assigns_legacy(tmp_path, monkeypatch):
    # R-008 이후 · 로그인 이전 형태의 기존 DB (owner_id, users 없음)
    path = tmp_path / "old.db"
    conn = sqlite3.connect(path)
    conn.execute(
        "CREATE TABLE tasks (id INTEGER PRIMARY KEY AUTOINCREMENT, "
        "title TEXT NOT NULL, description TEXT NOT NULL DEFAULT '', "
        "status TEXT NOT NULL DEFAULT 'TODO', "
        "priority TEXT NOT NULL DEFAULT 'NONE', "
        "assignee TEXT NOT NULL DEFAULT '')"
    )
    conn.executemany("INSERT INTO tasks (title) VALUES (?)", [("a",), ("b",), ("c",)])
    conn.commit()
    conn.close()
    monkeypatch.setenv("TASK_FLOW_DB", str(path))
    db.init_db()
    db.init_db()  # 두 번 실행해도 같다
    conn = sqlite3.connect(path)
    assert conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0] == 3
    assert (
        conn.execute("SELECT COUNT(*) FROM tasks WHERE owner_id IS NULL").fetchone()[0]
        == 0
    )
    owners = conn.execute(
        "SELECT DISTINCT u.username FROM tasks t JOIN users u ON u.id = t.owner_id"
    ).fetchall()
    conn.close()
    assert owners == [("legacy",)]


def test_expired_session_gets_401(client, monkeypatch):
    from app import auth

    assert client.get("/api/tasks").status_code == 200
    real = auth.time.time
    monkeypatch.setattr(auth.time, "time", lambda: real() + auth.SESSION_MAX_AGE + 1)
    assert client.get("/api/tasks").status_code == 401
    assert client.get("/api/auth/me").status_code == 401
