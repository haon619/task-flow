# task-flow

개인용 Task 카드 관리 웹 앱. 설계는 [PRD.md](PRD.md), [ARCHITECTURE.md](ARCHITECTURE.md), [DECISIONS.md](DECISIONS.md) 참고.

현재 상태: M0 (기본 구조만 있음). 카드 기능, 데이터베이스, 로그인은 아직 없다.

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

## 기존 DB 마이그레이션 (로그인 도입 전에 쓰던 DB가 있을 때)
```
cd backend
uv run python scripts/migrate_owner.py
```
실행 전에 `task-flow.db.bak`으로 백업하고, 기존 카드를 `legacy` 사용자에게 붙인다. 전후 카드 수가 같고 주인 없는 카드가 0건이면 "검증 통과"가 나온다. (D-018)

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
