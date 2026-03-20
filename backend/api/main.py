"""
Single FastAPI application — port 8000.
Includes ALL routes: simulation, RL decisions, UI dashboard, training, evaluation.

Run from backend/ directory:
    uvicorn api.main:app --port 8000 --reload
"""
import json
import logging
import os
import time
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse

from api.models import HealthResponse
from api.routes import router as primary_router

logger = logging.getLogger(__name__)

API_KEY = os.getenv("API_KEY", "")
CORS_ORIGINS_RAW = os.getenv("CORS_ORIGINS", '["http://localhost:3000","http://localhost:5173"]')
try:
    CORS_ORIGINS = json.loads(CORS_ORIGINS_RAW)
except Exception:
    CORS_ORIGINS = ["http://localhost:3000", "http://localhost:5173"]

_model_loaded = False
_db_connected = False


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _model_loaded, _db_connected
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    logger.info("Starting up (port 8000)")

    # Init async DB tables
    try:
        from app.config.database import create_all_tables
        await create_all_tables()
        _db_connected = True
        logger.info("Database tables ready.")
    except Exception as exc:
        logger.warning("DB init failed (continuing without DB): %s", exc)

    # Preload RL model
    try:
        from api.routes import _get_env_and_model
        _, model = _get_env_and_model()
        _model_loaded = model is not None
    except Exception as exc:
        logger.warning("Model preload failed: %s", exc)

    yield
    logger.info("Shutdown complete.")


app = FastAPI(
    title="RL API Orchestration",
    description="PPO-based intelligent API routing system — all endpoints on port 8000.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def api_key_middleware(request: Request, call_next) -> Response:
    skip = {"/", "/health", "/docs", "/openapi.json", "/redoc"}
    if API_KEY and request.url.path not in skip:
        if request.headers.get("X-API-Key", "") != API_KEY:
            return JSONResponse(status_code=401, content={"detail": "Invalid or missing API key"})
    return await call_next(request)


@app.middleware("http")
async def logging_middleware(request: Request, call_next) -> Response:
    start = time.perf_counter()
    response = await call_next(request)
    ms = round((time.perf_counter() - start) * 1000, 2)
    response.headers["X-Response-Time-Ms"] = str(ms)
    logger.info(json.dumps({"method": request.method, "path": request.url.path,
                             "status": response.status_code, "ms": ms}))
    return response


# ── Primary routes (simulation, training, evaluation, logs) ──────────────────
app.include_router(primary_router)

# ── App routes (RL decisions, UI dashboard) ──────────────────────────────────
try:
    from app.routes.api_routes import router as app_api_router
    from app.routes.rl_routes import router as rl_router
    from app.routes.ui_routes import router as ui_router
    app.include_router(app_api_router)
    app.include_router(rl_router)
    app.include_router(ui_router)
    logger.info("App sub-routers registered: /api, /rl, /ui")
except Exception as exc:
    logger.warning("Could not register app sub-routers: %s", exc)


@app.get("/", include_in_schema=False)
async def root() -> RedirectResponse:
    return RedirectResponse(url="/docs")


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        model_loaded=_model_loaded,
        db_connected=_db_connected,
        version="1.0.0",
        env=os.getenv("APP_ENV", "development"),
    )
