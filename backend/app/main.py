from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import api_routes, rl_routes, ui_routes
from app.config.settings import settings

app = FastAPI(title=settings.PROJECT_NAME)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_routes.router)
app.include_router(rl_routes.router)
app.include_router(ui_routes.router)

@app.get("/")
def root():
    return {"status": "healthy", "model_loaded": True, "message": "Welcome to the RL-based API Orchestration System"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8001, reload=True)
