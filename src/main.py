import uvloop
uvloop.install()

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import ORJSONResponse
import time
import logging
from contextlib import asynccontextmanager

from .utils.execution_time_middleware import ExecutionTimeMiddleware
from .api import projects, dependencies

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Python Vulnerability Tracker with performance optimizations")
    logger.info("Using uvloop for enhanced async performance")
    yield
    logger.info("Shutting down Python Vulnerability Tracker")


app = FastAPI(
    title="Python Vulnerability Tracker",
    description="High-performance vulnerability tracking service",
    version="1.0.0",
    lifespan=lifespan,
    default_response_class=ORJSONResponse,  # Use orjson for faster JSON responses
)

# Add performance monitoring middleware
app.add_middleware(ExecutionTimeMiddleware)

# Add CORS middleware for better API accessibility
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add Gzip compression for better response times
app.add_middleware(GZipMiddleware, minimum_size=1000)

@app.get("/health")
async def health():
    return {"status": "ok", "timestamp": time.time()}

app.include_router(projects.router, prefix="/api", tags=["projects"])
app.include_router(dependencies.router, prefix="/api", tags=["dependencies"])

# Startup/shutdown handled by lifespan