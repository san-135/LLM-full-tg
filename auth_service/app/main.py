from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from app.api.router import api_router
from app.core.config import settings
from app.db.base import Base
from app.db.session import engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        lifespan=lifespan,
    )
    app.include_router(api_router)

    @app.get("/")
    async def redirect_to_docs():
        """
        Перенаправляем сразу в Swagger UI для удобства.
        """
        return RedirectResponse(url="/docs")
    
    @app.get("/health")
    async def health():
        """
        Простая проверка работоспособности сервиса.
        """
        return {"status": "ok", "environment": settings.env}

    return app


app = create_app()
