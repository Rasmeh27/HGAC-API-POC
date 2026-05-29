from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from src.core.config import get_settings
from src.presentation.api.routes import events, health


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        description="Backend PoC para Gate Inteligente HGAC",
    )

    app.include_router(health.router, prefix="/api/v1")
    app.include_router(events.router, prefix="/api/v1")

    app.mount("/evidence", StaticFiles(directory="evidence"), name="evidence")

    return app


app = create_app()
