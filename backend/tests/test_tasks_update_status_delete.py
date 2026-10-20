import sqlite3


def _create(client, title="t", description="d"):
    return client.post(
        "/api/tasks", json={"title": title, "description": description}
    ).json()


# --- 수정 (R-004) ---


def test_update_changes_title_and_description(client):
    card = _create(client)
    res = client.patch(
        f"/api/tasks/{card['id']}", json={"title": "새 제목", "description": "새 설명"}
    )
    assert res.status_code == 200
    assert res.json()["title"] == "새 제목"
    assert res.json()["description"] == "새 설명"
    assert client.get("/api/tasks").json()[0]["title"] == "새 제목"


def test_update_does_not_change_status(client):
    card = _create(client)
    client.patch(f"/api/tasks/{card['id']}/status", json={"status": "DONE"})
    res = client.patch(
        f"/api/tasks/{card['id']}", json={"title": "x", "description": ""}
    )
    assert res.json()["status"] == "DONE"


def test_update_can_clear_description(client):
    card = _create(client)
    res = client.patch(
        f"/api/tasks/{card['id']}", json={"title": "t", "description": ""}
    )
    assert res.status_code == 200
    assert res.json()["description"] == ""


def test_update_rejects_empty_and_whitespace_title(client):
    card = _create(client, title="원래")
    for title in ["", "   "]:
        res = client.patch(
            f"/api/tasks/{card['id']}", json={"title": title, "description": "d"}
        )
        assert res.status_code == 422
    assert client.get("/api/tasks").json()[0]["title"] == "원래"


def test_update_missing_card_is_404(client):
    res = client.patch("/api/tasks/999", json={"title": "x", "description": ""})
    assert res.status_code == 404


# --- 상태 변경 (R-002, D-008) ---


def test_status_can_move_freely_between_all_states(client):
    card = _create(client)
    url = f"/api/tasks/{card['id']}/status"
    # 한 단계씩이 아니어도 되고, 완료에서 되돌릴 수도 있다.
    for status in ["DONE", "TODO", "IN_PROGRESS", "DONE", "IN_PROGRESS", "TODO"]:
        res = client.patch(url, json={"status": status})
        assert res.status_code == 200
        assert res.json()["status"] == status
        assert client.get("/api/tasks").json()[0]["status"] == status


def test_status_outside_three_values_is_rejected(client):
    card = _create(client)
    url = f"/api/tasks/{card['id']}/status"
    client.patch(url, json={"status": "IN_PROGRESS"})
    for bad in ["ARCHIVED", "todo", "", None]:
        res = client.patch(url, json={"status": bad})
        assert res.status_code == 422
    assert client.get("/api/tasks").json()[0]["status"] == "IN_PROGRESS"


def test_status_missing_card_is_404(client):
    res = client.patch("/api/tasks/999/status", json={"status": "DONE"})
    assert res.status_code == 404


# --- 삭제 (R-005) ---


def test_delete_removes_card(client):
    keep = _create(client, title="keep")
    gone = _create(client, title="gone")
    res = client.delete(f"/api/tasks/{gone['id']}")
    assert res.status_code == 204
    assert [t["id"] for t in client.get("/api/tasks").json()] == [keep["id"]]


def test_delete_missing_card_is_404(client):
    assert client.delete("/api/tasks/999").status_code == 404


def test_delete_twice_second_is_404(client):
    card = _create(client)
    assert client.delete(f"/api/tasks/{card['id']}").status_code == 204
    assert client.delete(f"/api/tasks/{card['id']}").status_code == 404


# --- 저장 실패 (ARCHITECTURE 실패 흐름) ---


def _block_writes(db_file):
    # 이후의 쓰기를 저장소가 거부하도록 트리거를 심는다.
    conn = sqlite3.connect(db_file)
    for event in ["INSERT", "UPDATE", "DELETE"]:
        conn.execute(
            f"CREATE TRIGGER block_{event.lower()} BEFORE {event} ON tasks "
            "BEGIN SELECT RAISE(ABORT, 'disk full'); END"
        )
    conn.commit()
    conn.close()


def test_storage_failure_returns_500_and_changes_nothing(client, db_file):
    card = _create(client, title="원래")
    _block_writes(db_file)

    assert (
        client.post("/api/tasks", json={"title": "새 카드"}).status_code == 500
    )
    assert (
        client.patch(
            f"/api/tasks/{card['id']}", json={"title": "바뀜", "description": ""}
        ).status_code
        == 500
    )
    assert (
        client.patch(
            f"/api/tasks/{card['id']}/status", json={"status": "DONE"}
        ).status_code
        == 500
    )
    assert client.delete(f"/api/tasks/{card['id']}").status_code == 500

    cards = client.get("/api/tasks").json()
    assert len(cards) == 1
    assert cards[0]["title"] == "원래"
    assert cards[0]["status"] == "TODO"
