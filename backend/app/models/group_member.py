from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Index, String, UniqueConstraint, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.base import Base

if TYPE_CHECKING:
    from app.models.group import Group
    from app.models.user import User


class GroupMember(Base):
    __tablename__ = "group_members"
    __table_args__ = (
        UniqueConstraint("group_id", "user_id", name="uq_group_member_group_user"),
        Index(
            "ix_group_member_one_owner",
            "group_id",
            unique=True,
            postgresql_where=text("role = 'owner'"),
        ),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    group: Mapped[Group] = relationship(back_populates="members")
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"), index=True)
    user: Mapped[User] = relationship(back_populates="memberships")
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    role: Mapped[str] = mapped_column(String(20), server_default="member")
