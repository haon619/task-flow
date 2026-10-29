import sqlite3

from fastapi.testclient import TestClient

from app.main import app


def _patch(client, card, **fields):
    body = {"title": card["title"], "description": ""} | fields
    return client.patch(f"/api/tasks/{card['id']}", json=body)


def test_due_date_defaults_to_null(client):
    card = client.post("/api/tasks", json={"title": "t"}).json()
    assert card["due_date"] is None


def test_create_with_due_date(client):
    res = client.post("/api/tasks", json={"title": "t", "due_date": "2026-11-01"})
    assert res.status_code == 201
    assert res.json()["due_date"] == "2026-11-01"
    assert client.get("/api/tasks").json()[0]["due_date"] == "2026-11-01"


def test_invalid_due_date_is_rejected(client):
    for bad in ["2026-13-01", "2026-02-30", "11/01/2026", "2026-11-01T00:00:00", "", "abc"]:
        res = client.post("/api/tasks", json={"title": "t", "due_date": bad})
        assert res.status_code == 422, bad
    assert client.get("/api/tasks").json() == []


def test_update_sets_changes_and_clears_due_date(client):
    card = client.post("/api/tasks", json={"title": "t"}).json()
    assert _patch(client, card, due_date="2026-11-01").json()["due_date"] == "2026-11-01"
    assert _patch(client, card, due_date="2026-12-24").json()["due_date"] == "2026-12-24"
    assert _patch(client, card, due_date=None).json()["due_date"] is None


def test_update_without_due_date_keeps_it(client):
    card = client.post("/api/tasks", json={"title": "t", "due_date": "2026-11-01"}).json()
    assert _patch(client, card, title="새 제목").json()["due_date"] == "2026-11-01"


def test_update_rejects_invalid_due_date_and_keeps_card(client):
    card = client.post("/api/tasks", json={"title": "t", "due_date": "2026-11-01"}).json()
    assert _patch(client, card, due_date="내일").status_code == 422
    assert client.get("/api/tasks").json()[0]["due_date"] == "2026-11-01"


def test_status_change_keeps_priority_and_due_date(client):
    card = client.post(
        "/api/tasks", json={"title": "t", "priority": "HIGH", "due_date": "2026-11-01"}
    ).json()
    res = client.patch(f"/api/tasks/{card['id']}/status", json={"status": "DONE"}).json()
    assert res["priority"] == "HIGH"
    assert res["due_date"] == "2026-11-01"


def test_other_users_card_due_date_is_404(client, other_client):
    card = client.post("/api/tasks", json={"title": "t"}).json()
    assert _patch(other_client, card, due_date="2026-11-01").status_code == 404


def test_old_priority_values_migrate_to_normal(db_file, upgrade):
    # D-019: NONE · MEDIUM은 NORMAL로, LOW · HIGH는 그대로. 카드와 id는 유지된다.
    conn = sqlite3.connect(db_file)
    conn.execute(
        "CREATE TABLE users (id INTEGER PRIMARY KEY AUTOINCREMENT, "
        "username TEXT NOT NULL UNIQUE, password_hash TEXT NOT NULL)"
    )
    conn.execute(
        "CREATE TABLE tasks (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, "
        "description TEXT NOT NULL DEFAULT '', status TEXT NOT NULL DEFAULT 'TODO' "
        "CHECK (status IN ('TODO', 'IN_PROGRESS', 'DONE')), "
        "priority TEXT NOT NULL DEFAULT 'NONE' "
        "CHECK (priority IN ('NONE', 'LOW', 'MEDIUM', 'HIGH')), "
        "assignee TEXT NOT NULL DEFAULT '', owner_id INTEGER REFERENCES users(id))"
    )
    conn.execute("INSERT INTO users (username, password_hash) VALUES ('u', '!')")
    conn.executemany(
        "INSERT INTO tasks (title, priority, owner_id) VALUES (?, ?, 1)",
        [("a", "NONE"), ("b", "LOW"), ("c", "MEDIUM"), ("d", "HIGH")],
    )
    conn.commit()
    conn.close()

    for _ in range(2):  # 다시 실행해도 아무것도 바꾸지 않는다
        upgrade()
        with TestClient(app):
            pass
        conn = sqlite3.connect(db_file)
        rows = conn.execute(
            "SELECT id, title, priority, due_date FROM tasks ORDER BY id"
        ).fetchall()
        conn.close()
        assert rows == [
            (1, "a", "NORMAL", None),
            (2, "b", "LOW", None),
            (3, "c", "NORMAL", None),
            (4, "d", "HIGH", None),
        ]
