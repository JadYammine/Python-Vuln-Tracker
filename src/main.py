from fastapi import FastAPI

app = FastAPI(title="Python Vulnerability Tracker")


@app.get("/health")
async def health():
    return {"status": "ok"}