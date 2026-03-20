"""app/routes — FastAPI route modules."""
from app.routes.api_routes import router as api_router
from app.routes.rl_routes import router as rl_router
from app.routes.ui_routes import router as ui_router

__all__ = ["api_router", "rl_router", "ui_router"]
