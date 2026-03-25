"""Authentication service"""
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import select, insert, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    verify_token
)
from app.config import get_settings
from app.models.user import users
from app.schemas.user import UserCreate, UserLogin

settings = get_settings()


async def create_user(db: AsyncSession, user_data: UserCreate) -> dict:
    """Create a new user"""
    # Check if username already exists
    result = await db.execute(
        select(users).where(users.c.username == user_data.username)
    )
    if result.first():
        raise ValueError("Username already registered")

    # Check if email already exists
    if user_data.email:
        result = await db.execute(
            select(users).where(users.c.email == user_data.email)
        )
        if result.first():
            raise ValueError("Email already registered")

    # Hash password
    hashed_password = get_password_hash(user_data.password)

    # Create user
    # Handle enum values
    gender_value = user_data.gender if user_data.gender else "O"
    learning_stage_value = user_data.learning_stage if user_data.learning_stage else None
    
    stmt = insert(users).values(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_password,
        name=user_data.name,
        phone=user_data.phone,
        gender=gender_value,
        age=user_data.age,
        major=user_data.major,
        university=user_data.university,
        learning_stage=learning_stage_value,
        province=user_data.province,
        city=user_data.city,
        ethnicity=user_data.ethnicity,
    ).returning(users.c.id)

    result = await db.execute(stmt)
    await db.commit()

    user_id = result.scalar_one()
    return {"id": user_id}


async def authenticate_user(db: AsyncSession, login_data: UserLogin) -> Optional[dict]:
    """Authenticate user and return user data if successful"""
    # Find user by email
    result = await db.execute(
        select(users).where(users.c.email == login_data.email)
    )
    user = result.first()

    if not user:
        return None

    # Verify password
    if not verify_password(login_data.password, user.hashed_password):
        return None

    # Update last_login
    await db.execute(
        update(users)
        .where(users.c.id == user.id)
        .values(last_login=datetime.utcnow())
    )
    await db.commit()

    # Convert Row to dict
    return dict(user._asdict())


async def create_tokens(user_id: int) -> dict:
    """Create access and refresh tokens"""
    access_token = create_access_token(data={"user_id": user_id})
    refresh_token = create_refresh_token(data={"user_id": user_id})
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


async def get_user_by_id(db: AsyncSession, user_id: int) -> Optional[dict]:
    """Get user by ID"""
    result = await db.execute(
        select(users).where(users.c.id == user_id)
    )
    user = result.first()
    if user:
        return dict(user._asdict())
    return None


async def update_user(db: AsyncSession, user_id: int, update_data: dict) -> Optional[dict]:
    """Update user information"""
    # Build update values dict, only include non-None values
    update_values = {}
    for key, value in update_data.items():
        if value is not None:
            if isinstance(value, type):  # Handle Enum
                update_values[key] = value.value
            else:
                update_values[key] = value

    if not update_values:
        return await get_user_by_id(db, user_id)

    # Update user
    stmt = (
        update(users)
        .where(users.c.id == user_id)
        .values(**update_values)
    )
    await db.execute(stmt)
    await db.commit()

    return await get_user_by_id(db, user_id)


async def get_user_interviewer_settings(db: AsyncSession, user_id: int) -> dict:
    """Get user's interviewer settings

    Returns:
        dict: Interviewer settings with defaults if not set
    """
    from app.schemas.interviewer import InterviewerSettingsResponse

    result = await db.execute(
        select(users.c.interviewer_settings).where(users.c.id == user_id)
    )
    settings = result.scalar()

    if settings:
        return settings

    # Return default settings
    return {
        "gender": "male",
        "speed": 3,
        "voice": "standard",
        "style": "serious"
    }
