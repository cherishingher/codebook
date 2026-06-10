from fastapi import FastAPI

from app.api import auth, campus, device, health, learner, teacher
from app.core.config import settings


def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name, version="0.1.0")

    @app.get("/api/v1")
    @app.get("/api/v1/")
    def api_index() -> dict:
        return {
            "status": "ok",
            "name": settings.app_name,
            "version": "0.1.0",
            "health": "/api/v1/health",
            "docs": "/docs",
        }

    app.include_router(health.router, prefix="/api/v1")
    app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
    app.include_router(learner.router, prefix="/api/v1/learner", tags=["learner"])
    app.include_router(teacher.router, prefix="/api/v1/teacher", tags=["teacher"])
    app.include_router(campus.router, prefix="/api/v1/campus", tags=["campus"])
    app.include_router(device.router, prefix="/api/v1/device", tags=["device"])
    return app


app = create_app()
