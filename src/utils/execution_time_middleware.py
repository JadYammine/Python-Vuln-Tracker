import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

class ExecutionTimeMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.perf_counter()
        response = await call_next(request)
        end_time = time.perf_counter()
        exec_time_ms = (end_time - start_time) * 1000
        response.headers["X-Execution-Time-ms"] = f"{exec_time_ms:.2f}"
        return response
