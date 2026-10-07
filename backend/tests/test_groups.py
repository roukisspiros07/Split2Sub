from httpx import AsyncClient

from tests.helpers import auth, register_user


async def test_create_group_returns_201(client: AsyncClient) -> None:
    token, _ = await register_user(client)

    response = await client.post("/groups", json={"name": "Spotify Fam"}, headers=auth(token))

    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Spotify Fam"
    assert "id" in body
    assert "created_at" in body


async def test_create_group_requires_auth(client: AsyncClient) -> None:
    response = await client.post("/groups", json={"name": "Spotify Fam"})

    assert response.status_code == 401


async def test_create_group_empty_name_returns_422(client: AsyncClient) -> None:
    token, _ = await register_user(client)

    response = await client.post("/groups", json={"name": ""}, headers=auth(token))

    assert response.status_code == 422


async def test_create_group_long_name_returns_422(client: AsyncClient) -> None:
    token, _ = await register_user(client)

    response = await client.post("/groups", json={"name": "x" * 101}, headers=auth(token))

    assert response.status_code == 422


async def test_list_groups_only_returns_mine(client: AsyncClient) -> None:
    alice, _ = await register_user(client, "Alice")
    bob, _ = await register_user(client, "Bob")
    await client.post("/groups", json={"name": "Alice Group"}, headers=auth(alice))
    await client.post("/groups", json={"name": "Bob Group"}, headers=auth(bob))

    response = await client.get("/groups", headers=auth(alice))

    assert response.status_code == 200
    names = [group["name"] for group in response.json()]
    assert names == ["Alice Group"]
