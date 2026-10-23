from fastapi.testclient import TestClient

from app.main import app


def test_list_is_empty_at_start(client):
    res = client.get("/api/tasks")
    assert res.status_code == 200
    assert res.json() == []


def test_create_returns_card_with_todo_status(client):
    res = client.post("/api/tasks", json={"title": "장보기", "description": "우유"})
    assert res.status_code == 201
    body = res.json()
    assert body["title"] == "장보기"
    assert body["description"] == "우유"
    assert body["status"] == "TODO"
    assert isinstance(body["id"], int)


def test_description_is_optional(client):
    res = client.post("/api/tasks", json={"title": "설명 없음"})
    assert res.status_code == 201
    assert res.json()["description"] == ""


def test_title_is_trimmed(client):
    res = client.post("/api/tasks", json={"title": "  앞뒤 공백  "})
    assert res.json()["title"] == "앞뒤 공백"


def test_empty_title_is_rejected(client):
    res = client.post("/api/tasks", json={"title": ""})
    assert res.status_code == 422
    assert client.get("/api/tasks").json() == []


def test_whitespace_only_title_is_rejected(client):
    res = client.post("/api/tasks", json={"title": "   "})
    assert res.status_code == 422
    assert client.get("/api/tasks").json() == []


def test_missing_title_is_rejected(client):
    res = client.post("/api/tasks", json={"description": "제목 없음"})
    assert res.status_code == 422


def test_list_is_in_creation_order(client):
    for title in ["a", "b", "c"]:
        client.post("/api/tasks", json={"title": title})
    titles = [t["title"] for t in client.get("/api/tasks").json()]
    assert titles == ["a", "b", "c"]


def test_cards_survive_restart(db_file):
    # R-006: 앱을 껐다 켜도(새 클라이언트, 같은 DB 파일) 카드가 남는다.
    creds = {"username": "alice", "password": "password-1234"}
    with TestClient(app) as first:
        first.post("/api/auth/register", json=creds)
        first.post("/api/tasks", json={"title": "남아야 함"})
    with TestClient(app) as second:
        second.post("/api/auth/login", json=creds)
        titles = [t["title"] for t in second.get("/api/tasks").json()]
    assert titles == ["남아야 함"]
