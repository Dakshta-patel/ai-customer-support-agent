from fastapi import FastAPI

app = FastAPI(title="AI Customer Support Agent")


@app.get("/")
def read_root() -> dict[str, str]:
    return {"message": "AI Customer Support Agent backend is running."}


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
