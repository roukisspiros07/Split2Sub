from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.deps import check_membership_role, get_current_user
from app.models.group import Group
from app.models.group_member import GroupMember
from app.models.invite import Invite
from app.models.user import User
from app.schemas.groups import InviteOut

router = APIRouter(prefix="/invites", tags=["invites"])


@router.get("/pending", response_model=list[InviteOut])
async def invites(
    user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> list[InviteOut]:
    stmt = (
        select(Invite, Group.name)
        .join(Group)
        .where(
            Invite.email == user.email,
            Invite.status == "pending",
        )
    )
    results = await db.execute(stmt)
    return [
        InviteOut(
            id=invite.id,
            group_id=invite.group_id,
            group_name=group_name,
            email=invite.email,
            status=invite.status,
            created_at=invite.created_at,
        )
        for invite, group_name in results.all()
    ]


@router.post("/{invite_id}/accept", response_model=InviteOut, status_code=200)
async def accept(
    invite_id: int, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> InviteOut:
    stmt = select(Invite).where(Invite.id == invite_id)
    results = await db.execute(stmt)
    invite = results.scalar_one_or_none()
    if invite is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Invite not found")
    if invite.email != user.email:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Email doesn't match")
    if invite.status != "pending":
        raise HTTPException(status.HTTP_409_CONFLICT, "Invite already resolved")
    if await check_membership_role(db, invite.group_id, user.id) is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Already a member")
    db.add(GroupMember(group_id=invite.group_id, user_id=user.id, role="member"))
    invite.status = "accepted"
    await db.commit()
    group = await db.get(Group, invite.group_id)
    return InviteOut(
        id=invite.id,
        group_id=invite.group_id,
        group_name=group.name,
        email=invite.email,
        status=invite.status,
        created_at=invite.created_at,
    )
