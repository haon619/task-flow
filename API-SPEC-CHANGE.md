# API-SPEC-CHANGE: priority · due_date (R-009, #19)

기존 [API-SPEC.md](API-SPEC.md)는 고치지 않고 변경만 적는다. 규칙은 [BUSINESS-RULES.md](BUSINESS-RULES.md), 저장은 [DATA-MODEL.md](DATA-MODEL.md). 백엔드 API와 화면에 반영했다(`priority` · `due_date` 등록 · 수정 · 응답, 422 규칙, 기한 초과 계산, 서버 정렬, 화면의 마감일 입력 · 표시 · 기한 초과 표시).

## 변경
- 카드에 `priority`와 `due_date` 필드를 추가한다. 응답과 등록 · 수정 요청에서 쓴다.
  - `priority`: `LOW` · `NORMAL` · `HIGH`. 등록할 때 보내지 않으면 `NORMAL`.
  - `due_date`: `YYYY-MM-DD` 문자열 또는 `null`.
- 수정 요청에서 필드를 보내지 않으면 그대로 둔다.
- `due_date`를 `null`로 보내면 지우고, 새 날짜를 보내면 바꾼다.
- `priority`는 지울 수 없다. `null`로 보내면 422로 거절한다.
- 허용 밖의 값(세 단계 밖의 우선순위, 날짜 형식이 아닌 `due_date`)은 저장하지 않고 422로 거절한다. 카드는 이전 값을 유지한다.

- 지난 날짜도 `due_date`로 받는다. 과거 날짜를 막는 검증은 없다.
- 목록 응답은 서버가 정렬해서 준다: 기한 초과 → 우선순위(HIGH → NORMAL → LOW) → 가까운 마감일(없으면 맨 뒤) → ID.
- 모든 카드 응답에 `is_overdue`(true/false)가 들어간다. 마감일이 오늘(서버 시계, KST)보다 이전이고 상태가 `DONE`이 아닐 때 true다. 계산한 값이라 요청으로 보내도 무시하고 저장하지 않는다.

## 그대로인 것
- 로그인하지 않으면 401, 남의 카드는 404. (D-017)
- 상태 변경 요청은 `priority` · `due_date`를 바꾸지 않는다.

## 아직 정하지 않은 것
- "임박" 여부를 응답에 담을지 — "임박" 표시를 만드는 이슈 전에 정한다. (BUSINESS-RULES 참고)
- 우선순위 · 마감일로 거르는 조회 조건 — 이번 범위 밖, 다음 이슈.
