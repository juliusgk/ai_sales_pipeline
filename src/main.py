"""FastAPI application entry point."""

from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Startup and shutdown events."""
    # Startup: verify database connectivity
    from src.database import engine

    async with engine.begin() as conn:
        # Enable pgvector extension
        await conn.execute(
            __import__("sqlalchemy").text("CREATE EXTENSION IF NOT EXISTS vector")
        )
    yield
    # Shutdown: dispose engine
    await engine.dispose()


app = FastAPI(
    title="AI Sales Pipeline",
    description="AI-powered sales pipeline assistant with RAG-connected SLM",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS — restrict in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if not settings.is_production else [],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------- API Key Auth Middleware ----------


@app.middleware("http")
async def api_key_auth(request: Request, call_next):
    """Simple API key authentication middleware."""
    # Skip auth for health check and docs
    if request.url.path in ("/health", "/docs", "/openapi.json", "/redoc"):
        return await call_next(request)

    api_key = request.headers.get("Authorization", "").replace("Bearer ", "")
    if api_key != settings.api_key:
        return JSONResponse(status_code=401, content={"detail": "Invalid API key"})

    return await call_next(request)


# ---------- Health Check ----------


@app.get("/health", tags=["system"])
async def health_check():
    """Health check endpoint — no auth required."""
    return {"status": "healthy", "environment": settings.environment}


# ---------- Register Routers ----------

from src.api.router import api_router

app.include_router(api_router, prefix="/api")
