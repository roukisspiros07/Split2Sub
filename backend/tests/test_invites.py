from httpx import AsyncClient

from tests.helpers import auth, register_user


async def _create_group(client: AsyncClient, token: str, name: str = "Spotify Fam") -> int:
    response = await client.post("/groups", json={"name": name}, headers=auth(token))
    assert response.status_code == 201
    return response.json()["id"]


async def test_full_invite_flow(client: AsyncClient) -> None:
    owner, _ = await register_user(client, "Owner")
    friend, friend_email = await register_user(client, "Friend")
    group_id = await _create_group(client, owner)

    invite = await client.post(
        f"/groups/{group_id}/invites", json={"email": friend_email}, headers=auth(owner)
    )
    assert invite.status_code == 201
    assert invite.json()["group_name"] == "Spotify Fam"
    invite_id = invite.json()["id"]

    pending = await client.get("/invites/pending", headers=auth(friend))
    assert pending.status_code == 200
    assert [item["id"] for item in pending.json()] == [invite_id]

    accept = await client.post(f"/invites/{invite_id}/accept", headers=auth(friend))
    assert accept.status_code == 200
    assert accept.json()["status"] == "accepted"

    groups = await client.get("/groups", headers=auth(friend))
    assert [group["id"] for group in groups.json()] == [group_id]

    pending_after = await client.get("/invites/pending", headers=auth(friend))
    assert pending_after.json() == []


async def test_invite_requires_owner(client: AsyncClient) -> None:
    owner, _ = await register_user(client, "Owner")
    outsider, _ = await register_user(client, "Outsider")
    group_id = await _create_group(client, owner)

    response = await client.post(
        f"/groups/{group_id}/invites",
        json={"email": "whoever@example.com"},
        headers=auth(outsider),
    )

    assert response.status_code == 403


async def test_invite_unknown_email_returns_404(client: AsyncClient) -> None:
    owner, _ = await register_user(client, "Owner")
    group_id = await _create_group(client, owner)

    response = await client.post(
        f"/groups/{group_id}/invites", json={"email": "ghost@example.com"}, headers=auth(owner)
    )

    assert response.status_code == 404


async def test_invite_existing_member_returns_409(client: AsyncClient) -> None:
    owner, owner_email = await register_user(client, "Owner")
    group_id = await _create_group(client, owner)

    response = await client.post(
        f"/groups/{group_id}/invites", json={"email": owner_email}, headers=auth(owner)
    )

    assert response.status_code == 409


async def test_invite_duplicate_pending_returns_409(client: AsyncClient) -> None:
    owner, _ = await register_user(client, "Owner")
    friend, friend_email = await register_user(client, "Friend")
    group_id = await _create_group(client, owner)

    first = await client.post(
        f"/groups/{group_id}/invites", json={"email": friend_email}, headers=auth(owner)
    )
    second = await client.post(
        f"/groups/{group_id}/invites", json={"email": friend_email}, headers=auth(owner)
    )

    assert first.status_code == 201
    assert second.status_code == 409


async def test_accept_wrong_user_returns_403(client: AsyncClient) -> None:
    owner, _ = await register_user(client, "Owner")
    friend, friend_email = await register_user(client, "Friend")
    stranger, _ = await register_user(client, "Stranger")
    group_id = await _create_group(client, owner)
    invite = await client.post(
        f"/groups/{group_id}/invites", json={"email": friend_email}, headers=auth(owner)
    )
    invite_id = invite.json()["id"]

    response = await client.post(f"/invites/{invite_id}/accept", headers=auth(stranger))

    assert response.status_code == 403


async def test_accept_twice_returns_409(client: AsyncClient) -> None:
    owner, _ = await register_user(client, "Owner")
    friend, friend_email = await register_user(client, "Friend")
    group_id = await _create_group(client, owner)
    invite = await client.post(
        f"/groups/{group_id}/invites", json={"email": friend_email}, headers=auth(owner)
    )
    invite_id = invite.json()["id"]
    await client.post(f"/invites/{invite_id}/accept", headers=auth(friend))

    response = await client.post(f"/invites/{invite_id}/accept", headers=auth(friend))

    assert response.status_code == 409


async def test_accept_unknown_invite_returns_404(client: AsyncClient) -> None:
    friend, _ = await register_user(client, "Friend")

    response = await client.post("/invites/999999/accept", headers=auth(friend))

    assert response.status_code == 404
