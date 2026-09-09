import time
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from backend.app.core.config import settings
from backend.app.api.v1.router import api_router
from backend.app.db.init_db import init_db

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure storage paths exist
    os.makedirs(settings.LOCAL_STORAGE_PATH, exist_ok=True)
    os.makedirs(settings.LOCAL_THUMBNAILS_PATH, exist_ok=True)
    
    # Initialize DB & Seed Data
    try:
        await init_db()
    except Exception as e:
        print(f"Warning during DB init: {e}")
    yield

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-Powered Government Infrastructure Complaint & Resolution Platform API",
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS Configuration (Supports local dev, configured origins, and Vercel cloud previews)
cors_origins = settings.cors_origins_list
if "*" in cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origin_regex=r"^https?://.*",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_origin_regex=r"^https://.*\.vercel\.app$",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Latency & Security Headers Middleware
@app.middleware("http")
async def add_process_time_and_security_headers(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time-Sec"] = f"{process_time:.4f}"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    return response

from prometheus_fastapi_instrumentator import Instrumentator

# Mount API Routers
app.include_router(api_router, prefix=settings.API_V1_PREFIX)

# Expose Prometheus Metrics (/metrics)
Instrumentator().instrument(app).expose(app, endpoint="/metrics", tags=["Monitoring"])

# Health checks
@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT
    }

@app.get("/ready", tags=["Health"])
async def readiness_check():
    return {"status": "ready"}
