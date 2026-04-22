from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.bot.dispatcher import bot, dp
from app.core.config import settings

print(f"RABBITMQ_URL from settings: {settings.rabbitmq_url}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Запускаем поллинг в фоне (для демонстрации, в реальности лучше разделить процессы)
    import asyncio
    asyncio.create_task(dp.start_polling(bot))
    yield
    await dp.stop_polling()


app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)


@app.get("/health")
async def health():
    return {"status": "ok"}