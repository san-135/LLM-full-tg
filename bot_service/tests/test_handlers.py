import json
from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest
from aiogram.types import Message, User, Chat
from fakeredis import aioredis as fake_aioredis

from app.bot.handlers import set_token, handle_text


@pytest.fixture(autouse=True)
def patch_message_answer():
    with patch.object(Message, "answer", new_callable=AsyncMock) as mock_answer:
        yield mock_answer


def make_message(text: str, user_id: int = 123, chat_id: int = 123) -> Message:
    """Вспомогательная функция для создания fake Message с корректной датой."""
    return Message(
        message_id=1,
        date=datetime.now(),            # <-- Добавлена дата
        chat=Chat(id=chat_id, type="private"),
        from_user=User(id=user_id, is_bot=False, first_name="Test"),
        text=text,
    )


async def test_set_token_valid(valid_jwt_payload, mocker, patch_message_answer):
    fake_redis = fake_aioredis.FakeRedis(decode_responses=True)
    mocker.patch("app.bot.handlers.get_redis", return_value=fake_redis)

    msg = make_message(
        "/token eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI0MiIsInJvbGUiOiJ1c2VyIn0.abc"
    )

    with patch("app.bot.handlers.decode_and_validate", return_value=valid_jwt_payload):
        await set_token(msg)

    data_raw = await fake_redis.get("token:123")
    assert data_raw is not None
    data = json.loads(data_raw)
    assert data["sub"] == valid_jwt_payload["sub"]

    msg.answer.assert_called_once()
    assert "Токен принят" in msg.answer.call_args[0][0]



@pytest.mark.asyncio
async def test_set_token_missing_jwt(mocker, patch_message_answer):
    """Команда /token без аргумента выдаёт подсказку."""
    fake_redis = fake_aioredis.FakeRedis(decode_responses=True)
    mocker.patch("app.bot.handlers.get_redis", return_value=fake_redis)
    msg = make_message("/token")
    await set_token(msg)
    msg.answer.assert_called_once()
    assert "Использование: /token" in msg.answer.call_args[0][0]


@pytest.mark.asyncio
async def test_set_token_invalid(mocker, patch_message_answer):
    """Невалидный JWT не сохраняется, пользователь получает ошибку."""
    fake_redis = fake_aioredis.FakeRedis(decode_responses=True)
    mocker.patch("app.bot.handlers.get_redis", return_value=fake_redis)
    msg = make_message("/token bad.token.here")

    with patch("app.bot.handlers.decode_and_validate", side_effect=ValueError("Invalid token")):
        await set_token(msg)

    assert await fake_redis.get("token:123") is None

    msg.answer.assert_called_once()
    assert "Токен недействителен" in msg.answer.call_args[0][0]


@pytest.mark.asyncio
async def test_handle_text_no_token(mocker, patch_message_answer):
    """Обычное сообщение без предварительной установки токена вызывает отказ."""
    fake_redis = fake_aioredis.FakeRedis(decode_responses=True)
    mocker.patch("app.bot.handlers.get_redis", return_value=fake_redis)
    msg = make_message("Как дела?")
    await handle_text(msg)
    msg.answer.assert_called_once()
    assert "Сначала передайте токен" in msg.answer.call_args[0][0]


@pytest.mark.asyncio
async def test_handle_text_with_valid_token(mocker, patch_message_answer):
    """При наличии валидного токена задача Celery ставится в очередь."""
    fake_redis = fake_aioredis.FakeRedis(decode_responses=True)
    mocker.patch("app.bot.handlers.get_redis", return_value=fake_redis)

    await fake_redis.set(
        "token:123",
        json.dumps({"token": "valid.jwt.token", "sub": "42"})
    )

    msg = make_message("Что такое FastAPI?")
    mock_delay = mocker.patch("app.bot.handlers.llm_request.delay")
    mocker.patch("app.bot.handlers.decode_and_validate", return_value={"sub": "42"})

    await handle_text(msg)

    mock_delay.assert_called_once_with(123, "Что такое FastAPI?")
    msg.answer.assert_called_once()
    assert "Запрос принят" in msg.answer.call_args[0][0]


@pytest.mark.asyncio
async def test_handle_text_with_expired_token(mocker, patch_message_answer):
    """Если сохранённый токен истёк, бот требует повторной авторизации."""
    fake_redis = fake_aioredis.FakeRedis(decode_responses=True)
    mocker.patch("app.bot.handlers.get_redis", return_value=fake_redis)

    await fake_redis.set(
        "token:123",
        json.dumps({"token": "expired.token", "sub": "42"})
    )

    msg = make_message("Помоги!")

    with patch("app.bot.handlers.decode_and_validate", side_effect=ValueError("Token expired")):
        await handle_text(msg)

    msg.answer.assert_called_once()
    assert "Токен недействителен" in msg.answer.call_args[0][0]
    assert "Token expired" in msg.answer.call_args[0][0]


@pytest.mark.asyncio
async def test_handle_text_llm_request_not_called_on_invalid(mocker, patch_message_answer):
    """Если токен невалиден, задача Celery НЕ должна вызываться."""
    fake_redis = fake_aioredis.FakeRedis(decode_responses=True)
    mocker.patch("app.bot.handlers.get_redis", return_value=fake_redis)

    await fake_redis.set(
        "token:123",
        json.dumps({"token": "bad.token", "sub": "42"})
    )

    msg = make_message("Сгенерируй стих")
    mock_delay = mocker.patch("app.bot.handlers.llm_request.delay")

    with patch("app.bot.handlers.decode_and_validate", side_effect=ValueError("Invalid token")):
        await handle_text(msg)

    mock_delay.assert_not_called()
    msg.answer.assert_called_once()
    assert "Токен недействителен" in msg.answer.call_args[0][0]
