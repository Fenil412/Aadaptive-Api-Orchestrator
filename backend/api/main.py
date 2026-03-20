"""
Adaptive API Orchestrator — FastAPI Application Entry Point.

Run with:
    cd backend
    uvicorn api.main:app --reload --port 8000
"""

import os
import sys
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

load_dotenv()

from api.routes import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events."""
    # ── Startup ──
    print("\n" + "=" * 50)
    print("🚀 Adaptive API Orchestrator — Starting Up")
    print("=" * 50)

    # Try to initialize database
    try:
        from db.connection import init_database
        init_database()
    except Exception as e:
        print(f"⚠️  Database not available: {e}")
        print("   Running in memory-only mode")

    # Preload model if exists
    model_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "models",
        "ppo_api_orchestrator.zip",
    )
    if os.path.exists(model_path):
        print(f"✅ Trained model found at: {model_path}")
    else:
        print(f"⚠️  No trained model found. Use POST /train to train one.")

    print("=" * 50 + "\n")

    yield

    # ── Shutdown ──
    print("\n👋 Shutting down Adaptive API Orchestrator")


# ── Create FastAPI App ──
app = FastAPI(
    title="Adaptive API Orchestrator",
    description=(
        "An RL-powered API gateway that uses PPO (Proximal Policy Optimization) "
        "to intelligently route API requests based on latency, cost, and "
        "reliability metrics."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS Middleware ──
cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Register Routes ──
app.include_router(router)


if __name__ == "__main__":
    import uvicorn

    host = os.getenv("BACKEND_HOST", "0.0.0.0")
    port = int(os.getenv("BACKEND_PORT", "8000"))
    uvicorn.run("api.main:app", host=host, port=port, reload=True)
