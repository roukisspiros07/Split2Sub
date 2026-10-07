from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.deps import check_membership_role, get_current_user, get_owner_membership
from app.models.group import Group
from app.models.group_member import GroupMember
from app.models.invite import Invite
from app.models.user import User
from app.schemas.groups import GroupCreate, GroupOut, InviteCreate, InviteOut

router = APIRouter(prefix="/groups", tags=["groups"])


@router.post("", response_model=GroupOut, status_code=201)
async def create(
    payload: GroupCreate, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> GroupOut:
    group = Group(name=payload.name)
    db.add(group)
    await db.flush()
    member = GroupMember(group_id=group.id, user_id=user.id, role="owner")
    db.add(member)
    await db.commit()
    await db.refresh(group)
    return group


@router.get("", response_model=list[GroupOut], status_code=200)
async def list_groups(
    user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> list[GroupOut]:
    stmt = select(Group).join(GroupMember).where(GroupMember.user_id == user.id)
    results = await db.execute(stmt)
    return results.scalars().all()


@router.post("/{group_id}/invites", response_model=InviteOut, status_code=201)
async def invite(
    group_id: int,
    payload: InviteCreate,
    _: GroupMember = Depends(get_owner_membership),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> InviteOut:
    email = payload.email.strip().lower()
    result = await db.execute(select(User).where(User.email == email))
    invitee = result.scalar_one_or_none()
    if invitee is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")

    if await check_membership_role(db, group_id, invitee.id) is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Already a member")

    existing = await db.execute(
        select(Invite).where(
            Invite.group_id == group_id,
            Invite.email == email,
            Invite.status == "pending",
        )
    )
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Invite already pending")

    invite = Invite(group_id=group_id, email=email, created_by=user.id)
    db.add(invite)
    await db.commit()
    await db.refresh(invite)

    group = await db.get(Group, group_id)
    return InviteOut(
        id=invite.id,
        group_id=invite.group_id,
        group_name=group.name,
        email=invite.email,
        status=invite.status,
        created_at=invite.created_at,
    )
