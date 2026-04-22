from datetime import timedelta

from app.core.security import create_access_token, decode_token, hash_password, verify_password


def test_hash_and_verify_password():
    plain = "secret123"
    hashed = hash_password(plain)
    assert hashed != plain
    assert verify_password(plain, hashed)
    assert not verify_password("wrong", hashed)


def test_jwt_create_and_decode():
    payload = {"sub": "42", "role": "admin"}
    token = create_access_token(payload, expires_delta=timedelta(minutes=5))
    decoded = decode_token(token)
    assert decoded["sub"] == "42"
    assert decoded["role"] == "admin"
    assert "exp" in decoded
    assert "iat" in decoded
    