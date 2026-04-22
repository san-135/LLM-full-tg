import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_full_auth_flow(async_client: AsyncClient):
    # Register
    reg_resp = await async_client.post(
        "/auth/register",
        json={"email": "test@email.com", "password": "secret123"},
    )
    assert reg_resp.status_code == 201
    user = reg_resp.json()
    assert user["email"] == "test@email.com"

    # Login (OAuth2 form)
    login_resp = await async_client.post(
        "/auth/login",
        data={"username": "test@email.com", "password": "secret123"},
    )
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]

    # Get 'me' with token
    me_resp = await async_client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_resp.status_code == 200
    assert me_resp.json()["email"] == "test@email.com"


@pytest.mark.asyncio
async def test_negative_cases(async_client: AsyncClient):
    # Register duplicate
    await async_client.post("/auth/register", json={"email": "dup@ex.com", "password": "123456"})
    resp = await async_client.post("/auth/register", json={"email": "dup@ex.com", "password": "123456"})
    assert resp.status_code == 409

    # Login wrong password
    resp = await async_client.post("/auth/login", data={"username": "dup@ex.com", "password": "wrong"})
    assert resp.status_code == 401

    # /me without token
    resp = await async_client.get("/auth/me")
    assert resp.status_code == 401

    # /me with invalid token
    resp = await async_client.get("/auth/me", headers={"Authorization": "Bearer garbage"})
    assert resp.status_code == 401
    