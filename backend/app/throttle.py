from datetime import UTC, datetime, timedelta

from fastapi import HTTPException, status

COOLDOWN = timedelta(seconds=30)
_last_failed: dict[str, datetime] = {}


def enforce_login_throttle(email: str) -> None:
    last = _last_failed.get(email)
    if last is not None and datetime.now(UTC) - last < COOLDOWN:
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS,
            "Too many attempts, try again later",
        )


def record_failed_login(email: str) -> None:
    _last_failed[email] = datetime.now(UTC)
