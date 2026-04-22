import json
from aiogram import Router, types
from aiogram.filters import Command
from app.tasks.llm_tasks import llm_request

from app.core.jwt import decode_and_validate
from app.infra.redis import get_redis

from app.infra.celery_app import celery_app

# Принудительно обновляем брокер у задачи (иначе не работает)
llm_request.bind(celery_app)



router = Router()


@router.message(Command("token"))
async def set_token(message: types.Message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("Использование: /token [jwt]")
        return

    token = parts[1].strip()
    try:
        payload = decode_and_validate(token)
        user_id = payload["sub"]
    except ValueError as e:
        await message.answer(f"Токен недействителен: {e}")
        return

    redis = await get_redis()
    key = f"token:{message.from_user.id}"
    # Сохраняем токен и sub пользователя
    await redis.set(key, json.dumps({"token": token, "sub": user_id}))
    await message.answer("✅ Токен принят. Теперь можно задавать вопросы.")


@router.message()
async def handle_text(message: types.Message):
    redis = await get_redis()
    key = f"token:{message.from_user.id}"
    data_raw = await redis.get(key)
    if not data_raw:
        await message.answer("❌ Сначала передайте токен командой /token (jwt)")
        return

    data = json.loads(data_raw)
    token = data["token"]
    try:
        decode_and_validate(token)
    except ValueError as e:
        await message.answer(f"❌ Токен недействителен: {e}\nПовторите /token")
        return

    try:
        # Отправляем задачу в Celery
        llm_request.delay(message.chat.id, message.text)
        await message.answer("⏳ Запрос принят, ожидайте ответа...")
    except Exception as e:
        await message.answer(f"❌ Ошибка при отправке запроса: {e}")
        print(f"!!! Exception in handle_text: {e}")
        raise