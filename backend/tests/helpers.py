from uuid import uuid4

from httpx import AsyncClient


async def register_user(client: AsyncClient, display_name: str = "User") -> tuple[str, str]:
    email = f"test-{uuid4().hex[:8]}@example.com"
    response = await client.post(
        "/auth/register",
        json={"email": email, "password": "correct-horse-battery", "display_name": display_name},
    )
    assert response.status_code == 200
    return response.json()["access_token"], email


def auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}
