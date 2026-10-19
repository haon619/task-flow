from fastapi import FastAPI

app = FastAPI(title="task-flow")


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
