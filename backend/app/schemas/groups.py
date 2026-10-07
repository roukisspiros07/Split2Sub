from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class GroupCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)


class GroupOut(BaseModel):
    id: int
    name: str
    created_at: datetime


class InviteCreate(BaseModel):
    email: EmailStr


class InviteOut(BaseModel):
    id: int
    group_id: int
    group_name: str
    email: str
    status: str
    created_at: datetime
