"""
Secondary FastAPI application — run from backend/ directory:
    uvicorn app.main:app --port 8001 --reload
"""
import json
import logging
import time
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from app.config.database import create_all_tables
from app.config.settings import settings
from app.routes.api_routes import router as api_router
from app.routes.rl_routes import router as rl_router
from app.routes.ui_routes import router as ui_router

logger = logging.getLogger(__name__)

_rl_agent = None
_db_connected = False


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _rl_agent, _db_connected

    logger.info("Starting up app (env=%s)", settings.APP_ENV)

    try:
        await create_all_tables()
        _db_connected = True
        logger.info("Database tables ready.")
    except Exception as exc:
        logger.warning("DB init failed (continuing without DB): %s", exc)

    try:
        from app.services.rl_agent import RLAgent
        _rl_agent = RLAgent(model_path=settings.MODEL_PATH)
        _rl_agent.load_model()
    except Exception as exc:
        logger.warning("RLAgent load failed: %s", exc)

    yield

    logger.info("Shutting down app.")
    _rl_agent = None


app = FastAPI(
    title="RL API Orchestration — App",
    description="Secondary FastAPI app with integrated RL environment (port 8001).",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def json_logging_middleware(request: Request, call_next) -> Response:
    start = time.perf_counter()
    response = await call_next(request)
    duration_ms = (time.perf_counter() - start) * 1000
    logger.info(json.dumps({
        "method": request.method,
        "path": request.url.path,
        "status": response.status_code,
        "duration_ms": round(duration_ms, 2),
    }))
    return response


app.include_router(api_router)
app.include_router(rl_router)
app.include_router(ui_router)


@app.get("/", include_in_schema=False)
async def root() -> RedirectResponse:
    return RedirectResponse(url="/docs")


@app.get("/health", tags=["Health"])
async def health() -> dict[str, Any]:
    model_loaded = _rl_agent is not None and getattr(_rl_agent, "is_loaded", False)
    return {
        "status": "ok",
        "model_loaded": model_loaded,
        "db_connected": _db_connected,
        "env": settings.APP_ENV,
    }
