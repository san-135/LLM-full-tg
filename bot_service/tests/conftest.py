import pytest


@pytest.fixture
def valid_jwt_payload():
    """Пример валидного payload для создания тестового JWT."""
    return {"sub": "31", "role": "user"}
