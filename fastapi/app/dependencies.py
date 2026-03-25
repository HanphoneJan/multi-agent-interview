"""Dependency Injection (SQLAlchemy Core)"""
from typing import Annotated, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings, Settings
from app.database import get_db
from app.core.security import verify_token
from app.models.user import users

# Type aliases for dependencies
SessionDep = Annotated[AsyncSession, Depends(get_db)]
SettingsDep = Annotated[Settings, Depends(get_settings)]

# Security
security = HTTPBearer()
optional_security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    db: SessionDep,
    settings: SettingsDep,
) -> dict:
    """Get current authenticated user"""
    token = credentials.credentials
    payload = verify_token(token, settings.JWT_SECRET_KEY)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )

    user_id = payload.get("user_id")
    if not isinstance(user_id, int):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid user_id format: {type(user_id)}"
        )
    result = await db.execute(
        select(users).where(users.c.id == user_id)
    )
    user = result.first()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )

    # Convert Row to dict
    return dict(user._asdict())


async def get_current_user_optional(
    credentials: Annotated[Optional[HTTPAuthorizationCredentials], Depends(optional_security)],
    db: SessionDep,
    settings: SettingsDep,
) -> Optional[dict]:
    """Get current user (optional, allows anonymous access)"""
    if credentials is None:
        return None

    token = credentials.credentials
    payload = verify_token(token, settings.JWT_SECRET_KEY)

    if payload is None:
        return None

    user_id = payload.get("user_id")
    result = await db.execute(
        select(users).where(users.c.id == user_id)
    )
    user = result.first()

    if user:
        return dict(user._asdict())
    return None
