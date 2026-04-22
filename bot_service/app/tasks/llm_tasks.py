import asyncio

from celery import shared_task
from aiogram import Bot

from app.core.config import settings
from app.services.openrouter_client import OpenRouterClient


@shared_task(name="llm_request", bind=True, max_retries=3)
def llm_request(self, tg_chat_id: int, prompt: str):
    async def _run():
        client = OpenRouterClient()
        messages = [{"role": "user", "content": prompt}]
        answer = await client.chat_completion(messages)

        bot = Bot(token=settings.telegram_bot_token)
        await bot.send_message(tg_chat_id, answer)
        await bot.session.close()

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(_run())