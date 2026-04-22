from jose import JWTError, ExpiredSignatureError, jwt

from app.core.config import settings


def decode_and_validate(token: str) -> dict:
    """
    Декодирует и валидирует JWT.
    Возвращает payload или выбрасывает ValueError при ошибке.
    """
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_alg])
        if "sub" not in payload:
            raise ValueError("Missing sub claim")
        return payload
    except ExpiredSignatureError:
        raise ValueError("Token expired")
    except JWTError:
        raise ValueError("Invalid token")