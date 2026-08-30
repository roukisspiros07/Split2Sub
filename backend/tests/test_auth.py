from uuid import uuid4

from httpx import AsyncClient


async def _unique_email() -> str:
    return f"auth-test-{uuid4().hex[:12]}@example.com"


async def test_register_and_login_and_me_roundtrip(client: AsyncClient) -> None:
    email = await _unique_email()
    password = "correct-horse-battery"

    register = await client.post(
        "/auth/register",
        json={"email": email, "password": password, "display_name": "Bob"},
    )
    assert register.status_code == 200

    login = await client.post(
        "/auth/login",
        json={"email": email.upper(), "password": password},
    )
    assert login.status_code == 200
    login_token = login.json()["access_token"]

    me = await client.get("/auth/me", headers={"Authorization": f"Bearer {login_token}"})
    assert me.status_code == 200
    body = me.json()
    assert body["email"] == email
    assert body["display_name"] == "Bob"
    assert "password_hash" not in body


async def test_register_duplicate_email_conflicts(client: AsyncClient) -> None:
    email = await _unique_email()
    payload = {"email": email, "password": "correct-horse-battery", "display_name": "Bob"}

    first = await client.post("/auth/register", json=payload)
    second = await client.post("/auth/register", json=payload)

    assert first.status_code == 200
    assert second.status_code == 409


async def test_me_requires_auth(client: AsyncClient) -> None:
    no_token = await client.get("/auth/me")
    assert no_token.status_code == 401

    bad_token = await client.get("/auth/me", headers={"Authorization": "Bearer not.a.jwt"})
    assert bad_token.status_code == 401


async def test_login_wrong_password_rejected(client: AsyncClient) -> None:
    email = await _unique_email()
    await client.post(
        "/auth/register",
        json={"email": email, "password": "correct-horse-battery", "display_name": "Bob"},
    )

    login = await client.post(
        "/auth/login",
        json={"email": email, "password": "wrong-password"},
    )
    assert login.status_code == 401
