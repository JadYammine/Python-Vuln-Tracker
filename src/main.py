from fastapi import FastAPI

from .utils.execution_time_middleware import ExecutionTimeMiddleware
from .api import projects, dependencies

app = FastAPI(title="Python Vulnerability Tracker")
app.add_middleware(ExecutionTimeMiddleware)

@app.get("/health")
async def health():
    return {"status": "ok"}

app.include_router(projects.router, prefix="/api", tags=["projects"])
app.include_router(dependencies.router, prefix="/api", tags=["dependencies"])