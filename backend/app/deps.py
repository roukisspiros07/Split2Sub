from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import InvalidTokenError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.group_member import GroupMember
from app.models.user import User
from app.security import decode_token

bearer_scheme = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    try:
        user_id = decode_token(credentials.credentials)
    except InvalidTokenError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid credentials") from None
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid credentials")
    return user


async def check_membership_role(
    db: AsyncSession,
    group_id: int,
    user_id: int,
) -> GroupMember | None:
    stmt = select(GroupMember).where(
        GroupMember.group_id == group_id,
        GroupMember.user_id == user_id,
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_owner_membership(
    group_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> GroupMember:
    membership = await check_membership_role(db, group_id, user.id)
    if membership is None or membership.role != "owner":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Only the owner can do this")
    return membership
