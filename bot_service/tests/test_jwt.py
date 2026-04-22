import time
import pytest
from jose import jwt

from app.core.config import settings
from app.core.jwt import decode_and_validate


def test_decode_valid_token(valid_jwt_payload):
    """Проверка, что корректный токен успешно декодируется."""
    token = jwt.encode(valid_jwt_payload, settings.jwt_secret, algorithm=settings.jwt_alg)
    decoded = decode_and_validate(token)
    assert decoded["sub"] == valid_jwt_payload["sub"]
    assert decoded["role"] == valid_jwt_payload["role"]


def test_decode_invalid_signature():
    """Токен с неверной подписью вызывает ValueError."""
    token = jwt.encode({"sub": "42"}, "wrong_secret", algorithm=settings.jwt_alg)
    with pytest.raises(ValueError, match="Invalid token"):
        decode_and_validate(token)


def test_decode_malformed_token():
    """Полностью мусорный токен вызывает ValueError."""
    with pytest.raises(ValueError, match="Invalid token"):
        decode_and_validate("not.a.token")


def test_decode_expired_token():
    """Истёкший токен вызывает ValueError с сообщением 'Token expired'."""
    payload = {"sub": "42", "exp": int(time.time()) - 10}
    token = jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_alg)
    with pytest.raises(ValueError, match="Token expired"):
        decode_and_validate(token)


def test_decode_missing_sub_claim():
    """Токен без поля sub считается невалидным."""
    token = jwt.encode({"role": "user"}, settings.jwt_secret, algorithm=settings.jwt_alg)
    with pytest.raises(ValueError, match="Missing sub claim"):
        decode_and_validate(token)
        