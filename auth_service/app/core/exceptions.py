from fastapi import HTTPException, status


class BaseHTTPException(HTTPException):
    """Базовый класс для HTTP-исключений сервиса."""

    def __init__(self, detail: str, status_code: int, headers: dict | None = None):
        super().__init__(status_code=status_code, detail=detail, headers=headers)


class UserAlreadyExistsError(BaseHTTPException):
    def __init__(self):
        super().__init__("User with this email already exists", status.HTTP_409_CONFLICT)


class InvalidCredentialsError(BaseHTTPException):
    def __init__(self):
        super().__init__(
            "Invalid email or password",
            status.HTTP_401_UNAUTHORIZED,
            headers={"WWW-Authenticate": "Bearer"},
        )


class InvalidTokenError(BaseHTTPException):
    def __init__(self):
        super().__init__(
            "Invalid token",
            status.HTTP_401_UNAUTHORIZED,
            headers={"WWW-Authenticate": "Bearer"},
        )


class TokenExpiredError(BaseHTTPException):
    def __init__(self):
        super().__init__(
            "Token expired",
            status.HTTP_401_UNAUTHORIZED,
            headers={"WWW-Authenticate": "Bearer"},
        )


class UserNotFoundError(BaseHTTPException):
    def __init__(self):
        super().__init__("User not found", status.HTTP_404_NOT_FOUND)


class PermissionDeniedError(BaseHTTPException):
    def __init__(self):
        super().__init__("Permission denied", status.HTTP_403_FORBIDDEN)
