from datetime import date, datetime, timezone

import pytest

from app import routes_tasks

TODAY = date(2026, 10, 29)


@pytest.fixture(autouse=True)
def fixed_today(monkeypatch):
    monkeypatch.setattr(routes_tasks, "today", lambda: TODAY)


def _make(client, title, due=None, status="TODO", priority="NORMAL"):
    card = client.post(
        "/api/tasks", json={"title": title, "due_date": due, "priority": priority}
    ).json()
    if status != "TODO":
        client.patch(f"/api/tasks/{card['id']}/status", json={"status": status})
    return card["id"]


@pytest.mark.parametrize("status", ["TODO", "IN_PROGRESS"])
def test_overdue_judgement_table(client, status):
    ids = {
        "어제": _make(client, "어제", "2026-10-28", status),
        "오늘": _make(client, "오늘", "2026-10-29", status),
        "내일": _make(client, "내일", "2026-10-30", status),
        "없음": _make(client, "없음", None, status),
    }
    by_id = {t["id"]: t["is_overdue"] for t in client.get("/api/tasks").json()}
    assert by_id[ids["어제"]] is True
    assert by_id[ids["오늘"]] is False
    assert by_id[ids["내일"]] is False
    assert by_id[ids["없음"]] is False


def test_done_card_is_never_overdue(client):
    for label, due in [("어제", "2026-10-28"), ("오늘", "2026-10-29"),
                       ("내일", "2026-10-30"), ("없음", None)]:
        _make(client, label, due, "DONE")
    assert [t["is_overdue"] for t in client.get("/api/tasks").json()] == [False] * 4


def test_overdue_is_in_every_response_and_does_not_change_status(client):
    card = client.post("/api/tasks", json={"title": "t", "due_date": "2026-10-01"}).json()
    assert card["is_overdue"] is True
    assert card["status"] == "TODO"
    res = client.patch(f"/api/tasks/{card['id']}/status", json={"status": "DONE"}).json()
    assert res["is_overdue"] is False
    res = client.patch(f"/api/tasks/{card['id']}/status", json={"status": "TODO"}).json()
    assert res["is_overdue"] is True


def test_is_overdue_is_not_accepted_from_requests(client):
    card = client.post(
        "/api/tasks", json={"title": "t", "due_date": "2026-11-30", "is_overdue": True}
    ).json()
    assert card["is_overdue"] is False


def test_sort_order_overdue_priority_due_then_id(client):
    a = _make(client, "초과 NORMAL", "2026-10-20", priority="NORMAL")
    b = _make(client, "초과 HIGH 늦음", "2026-10-28", priority="HIGH")
    c = _make(client, "초과 HIGH 이름", "2026-10-10", priority="HIGH")
    d = _make(client, "HIGH 마감 있음", "2026-11-05", priority="HIGH")
    e = _make(client, "HIGH 마감 없음", None, priority="HIGH")
    f = _make(client, "NORMAL 가까움", "2026-10-30", priority="NORMAL")
    g = _make(client, "LOW", "2026-10-30", priority="LOW")
    h = _make(client, "NORMAL 같은 마감 먼저", "2026-11-01", priority="NORMAL")
    i = _make(client, "NORMAL 같은 마감 나중", "2026-11-01", priority="NORMAL")
    order = [t["id"] for t in client.get("/api/tasks").json()]
    # 기한 초과(우선순위, 마감일 순) → 그 밖(우선순위, 마감일 순, 마감일 없음은 뒤, 같으면 ID)
    assert order == [c, b, a, d, e, f, h, i, g]


def test_sort_applies_only_to_own_cards(client, other_client):
    mine = _make(client, "내 것", "2026-10-01")
    theirs = other_client.post("/api/tasks", json={"title": "남의 것", "due_date": "2026-10-01"}).json()
    assert [t["id"] for t in client.get("/api/tasks").json()] == [mine]
    assert [t["id"] for t in other_client.get("/api/tasks").json()] == [theirs["id"]]


def test_today_uses_kst_date(monkeypatch):
    # UTC 15:30은 KST로 다음 날 00:30이다.
    class FakeDatetime(datetime):
        @classmethod
        def now(cls, tz=None):
            return datetime(2026, 10, 28, 15, 30, tzinfo=timezone.utc).astimezone(tz)

    monkeypatch.undo()
    monkeypatch.setattr(routes_tasks, "datetime", FakeDatetime)
    assert routes_tasks.today() == date(2026, 10, 29)
