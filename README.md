# task-flow

개인용 Task 카드 관리 웹 앱. 설계는 [PRD.md](PRD.md), [ARCHITECTURE.md](ARCHITECTURE.md), [DECISIONS.md](DECISIONS.md) 참고.

현재 상태: 카드 등록 · 수정 · 상태 변경 · 삭제, 우선순위 · 담당자, 가입 · 로그인과 사용자별 카드가 있다. 마감일(날짜만, 없어도 됨)과 기한 초과 표시가 있고, 목록은 서버가 기한 초과 → 우선순위 → 가까운 마감일 → ID 순으로 정렬한다. (R-009, #19)

## 준비물
- uv (Python 3.12는 uv가 관리)
- Node.js LTS + npm

## 세션 비밀값 (처음 한 번)
로그인 세션 서명에 쓰는 비밀값이 필요하다. 값은 Git에 넣지 않는다.
```
cd backend
cp .env.example .env
# .env의 SESSION_SECRET= 뒤에 긴 임의의 문자열을 직접 적는다.
# 만들기: uv run python -c "import secrets; print(secrets.token_hex(32))"
```
`SESSION_SECRET`이 없으면 API가 시작하지 않는다. `.env`는 `.gitignore`에 들어 있다.

## AI 제안 키 (선택)
`POST /api/tasks/suggest`(Task 우선순위 · 마감일 제안, R-012)를 쓰려면 Anthropic API 키가 필요하다. 값은 Git에 넣지 않고 `backend/.env`의 `ANTHROPIC_API_KEY=` 뒤에 직접 적거나 같은 이름의 환경 변수로 준다.
- 키가 없어도 앱은 그대로 시작한다. 이 기능만 503 "AI 기능 꺼짐"으로 답한다.
- 이 기능을 쓰면 카드의 제목 · 설명이 Anthropic으로 전송된다.
- 제안은 돌려주기만 하고 저장하지 않는다. 화면은 아직 없다. (D-020)

## 기존 DB 마이그레이션 (이전 형식 DB가 있을 때)
DB 형식은 alembic으로 바꾼다. 앱은 시작할 때 DB를 바꾸지 않고, 이전 형식이면 시작을 거절하고 이 절차를 안내한다.
1. 앱(API · 화면)을 모두 종료한다.
2. `backend/data/task-flow.db`를 복사해서 백업한다. 되돌리기는 이 백업 파일로 바꿔 놓는 방법뿐이다. (downgrade는 없다)
3. 이전한다.
```
cd backend
uv run alembic upgrade head
uv run alembic current   # 0001 (head)가 나오면 끝
```
리비전 `0001`이 하는 일: 주인 없는 카드를 로그인할 수 없는 `legacy` 사용자에게 붙이고(D-018), 우선순위를 LOW · NORMAL · HIGH로 바꾸고(NONE · MEDIUM → NORMAL), `due_date` 컬럼을 더한다(D-019). 전후 카드 수 · id · 소유자를 검증하고 틀리면 원본을 그대로 둔 채 멈춘다. 이미 새 형식인 DB에서는 아무것도 바꾸지 않는다.

## 인계: 사용자와 권한
- 화면 첫 진입에서 가입하거나 로그인한다. 카드는 만든 사용자에게만 보인다.
- API 응답: 로그인 안 함 401, 다른 사용자의 카드 404, 검증 실패 422. 403은 정의만 있고 지금은 쓰지 않는다. (D-017)
- 테스트: `cd backend && uv run pytest`

## 실행
터미널 두 개를 연다.

API (FastAPI, http://127.0.0.1:8000):
```
cd backend
uv run uvicorn app.main:app --reload --port 8000
```

화면 (React · Vite, http://localhost:5173):
```
cd frontend
npm install   # 처음 한 번
npm run dev
```

브라우저에서 http://localhost:5173 을 열면 "API 연결됨"이 보인다. 화면의 `/api` 요청은 Vite 프록시가 API(8000)로 넘긴다.

## 확인
- API 상태: `GET http://127.0.0.1:8000/api/health` → `{"status":"ok"}`
- 화면 빌드: `cd frontend && npm run build`
