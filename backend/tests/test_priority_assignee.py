import sqlite3

from fastapi.testclient import TestClient

from app.main import app


def test_defaults_when_not_given(client):
    card = client.post("/api/tasks", json={"title": "t"}).json()
    assert card["priority"] == "NONE"
    assert card["assignee"] == ""


def test_create_with_priority_and_assignee(client):
    res = client.post(
        "/api/tasks",
        json={"title": "t", "priority": "HIGH", "assignee": "  하온  "},
    )
    assert res.status_code == 201
    assert res.json()["priority"] == "HIGH"
    assert res.json()["assignee"] == "하온"
    assert client.get("/api/tasks").json()[0]["priority"] == "HIGH"


def test_invalid_priority_is_rejected(client):
    for bad in ["URGENT", "high", ""]:
        res = client.post("/api/tasks", json={"title": "t", "priority": bad})
        assert res.status_code == 422
    assert client.get("/api/tasks").json() == []


def test_assignee_too_long_is_rejected(client):
    res = client.post("/api/tasks", json={"title": "t", "assignee": "가" * 51})
    assert res.status_code == 422
    ok = client.post("/api/tasks", json={"title": "t", "assignee": "가" * 50})
    assert ok.status_code == 201


def test_update_changes_priority_and_assignee(client):
    card = client.post("/api/tasks", json={"title": "t"}).json()
    res = client.patch(
        f"/api/tasks/{card['id']}",
        json={"title": "t", "description": "", "priority": "LOW", "assignee": "나"},
    )
    assert res.status_code == 200
    assert res.json()["priority"] == "LOW"
    assert res.json()["assignee"] == "나"


def test_update_without_them_keeps_current_values(client):
    card = client.post(
        "/api/tasks", json={"title": "t", "priority": "MEDIUM", "assignee": "나"}
    ).json()
    res = client.patch(
        f"/api/tasks/{card['id']}", json={"title": "새 제목", "description": ""}
    )
    assert res.json()["priority"] == "MEDIUM"
    assert res.json()["assignee"] == "나"


def test_update_can_clear_assignee_and_priority(client):
    card = client.post(
        "/api/tasks", json={"title": "t", "priority": "HIGH", "assignee": "나"}
    ).json()
    res = client.patch(
        f"/api/tasks/{card['id']}",
        json={"title": "t", "description": "", "priority": "NONE", "assignee": ""},
    )
    assert res.json()["priority"] == "NONE"
    assert res.json()["assignee"] == ""


def test_update_rejects_invalid_priority_and_keeps_card(client):
    card = client.post("/api/tasks", json={"title": "t", "priority": "LOW"}).json()
    res = client.patch(
        f"/api/tasks/{card['id']}",
        json={"title": "t", "description": "", "priority": "URGENT"},
    )
    assert res.status_code == 422
    assert client.get("/api/tasks").json()[0]["priority"] == "LOW"


def test_status_change_keeps_priority_and_assignee(client):
    card = client.post(
        "/api/tasks", json={"title": "t", "priority": "HIGH", "assignee": "나"}
    ).json()
    res = client.patch(f"/api/tasks/{card['id']}/status", json={"status": "DONE"})
    assert res.json()["priority"] == "HIGH"
    assert res.json()["assignee"] == "나"


def test_existing_db_is_migrated_without_losing_cards(db_file):
    # R-008 이전 형태의 DB를 직접 만든다. 컬럼을 더해도 기존 카드는 그대로여야 한다.
    conn = sqlite3.connect(db_file)
    conn.execute(
        "CREATE TABLE tasks (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, "
        "description TEXT NOT NULL DEFAULT '', status TEXT NOT NULL DEFAULT 'TODO' "
        "CHECK (status IN ('TODO', 'IN_PROGRESS', 'DONE')))"
    )
    conn.execute(
        "INSERT INTO tasks (title, description, status) VALUES ('옛 카드', '설명', 'DONE')"
    )
    conn.commit()
    conn.close()

    # 시작하면 컬럼이 더해지고 옛 카드는 legacy 소유로 그대로 남는다. (D-018)
    # legacy는 로그인할 수 없어서 API 대신 DB를 직접 읽는다.
    with TestClient(app):
        pass
    conn = sqlite3.connect(db_file)
    conn.row_factory = sqlite3.Row
    row = conn.execute(
        "SELECT t.id, t.title, t.description, t.status, t.priority, t.assignee, "
        "u.username AS owner FROM tasks t JOIN users u ON u.id = t.owner_id"
    ).fetchall()
    assert [dict(r) for r in row] == [
        {
            "id": 1,
            "title": "옛 카드",
            "description": "설명",
            "status": "DONE",
            "priority": "NONE",
            "assignee": "",
            "owner": "legacy",
        }
    ]
    conn.close()

    # 두 번째 시작(이미 컬럼이 있는 DB)에서도 오류 없이 시작하고 카드 수가 같다.
    with TestClient(app):
        pass
    conn = sqlite3.connect(db_file)
    assert conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0] == 1
    conn.close()
