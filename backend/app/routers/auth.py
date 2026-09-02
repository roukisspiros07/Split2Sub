from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.rate_limit import limiter
from app.schemas.auth import TokenResponse, UserLogin, UserOut, UserRegister
from app.security import create_access_token, hash_password, verify_password
from app.throttle import enforce_login_throttle, record_failed_login

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse)
@limiter.limit("10/minute")
async def register(
    request: Request,
    payload: UserRegister,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    email = payload.email.strip().lower()
    password = payload.password
    display_name = payload.display_name
    stmt = select(User).where(User.email == email)
    result = await db.execute(stmt)
    existing = result.scalar_one_or_none()
    if existing is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Email already registered")
    new_user = User(email=email, display_name=display_name, password_hash=hash_password(password))
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return TokenResponse(access_token=create_access_token(new_user.id))


@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/minute")
async def login(
    request: Request,
    payload: UserLogin,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    email = payload.email.strip().lower()
    password = payload.password
    enforce_login_throttle(email)
    stmt = select(User).where(User.email == email)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    if user is None or not verify_password(password, user.password_hash):
        record_failed_login(email)
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid credentials")
    return TokenResponse(access_token=create_access_token(user.id))


@router.get("/me", response_model=UserOut)
async def me(user: User = Depends(get_current_user)) -> UserOut:
    return user
