import pytest
import respx
from httpx import Response

from app.services.openrouter_client import OpenRouterClient
from app.core.config import settings


@pytest.mark.asyncio
async def test_openrouter_client_success():
    """Проверка успешного вызова OpenRouter с моком HTTP."""
    client = OpenRouterClient()
    test_prompt = "Привет, как дела?"
    expected_answer = "Привет! У меня всё отлично."

    with respx.mock as mock:
        # Мокаем только конкретный POST-запрос
        mock.post(f"{settings.openrouter_base_url}/chat/completions").mock(
            return_value=Response(
                200,
                json={
                    "choices": [
                        {"message": {"content": expected_answer}}
                    ]
                }
            )
        )

        answer = await client.chat_completion([{"role": "user", "content": test_prompt}])
        assert answer == expected_answer

        # Проверяем, что запрос был выполнен с ожидаемым телом
        last_request = mock.calls.last.request
        assert last_request.headers["Authorization"] == f"Bearer {settings.openrouter_api_key}"
        payload = last_request.content.decode()
        assert test_prompt in payload
        assert settings.openrouter_model in payload


@pytest.mark.asyncio
async def test_openrouter_client_http_error():
    """При HTTP-ошибке (например, 500) клиент должен выбросить исключение."""
    client = OpenRouterClient()
    with respx.mock as mock:
        mock.post(f"{settings.openrouter_base_url}/chat/completions").mock(
            return_value=Response(500, json={"error": "Internal Server Error"})
        )

        with pytest.raises(Exception):  # httpx.HTTPStatusError оборачивается в raise_for_status
            await client.chat_completion([{"role": "user", "content": "test"}])


@pytest.mark.asyncio
async def test_openrouter_client_timeout():
    """Имитация таймаута соединения."""
    client = OpenRouterClient()
    with respx.mock as mock:
        mock.post(f"{settings.openrouter_base_url}/chat/completions").mock(side_effect=TimeoutError)

        with pytest.raises(Exception):
            await client.chat_completion([{"role": "user", "content": "test"}])
            