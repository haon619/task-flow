# task-flow

개인용 Task 카드 관리 웹 앱. 설계는 [PRD.md](PRD.md), [ARCHITECTURE.md](ARCHITECTURE.md), [DECISIONS.md](DECISIONS.md) 참고.

현재 상태: M0 (기본 구조만 있음). 카드 기능, 데이터베이스, 로그인은 아직 없다.

## 준비물
- uv (Python 3.12는 uv가 관리)
- Node.js LTS + npm

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
