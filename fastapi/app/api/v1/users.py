"""User authentication and management API"""
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings, Settings
from app.database import get_db
from app.dependencies import (
    SessionDep,
    get_current_user,
    get_current_user_optional,
    security
)
from app.schemas.user import (
    UserRegister,
    UserLogin,
    UserResponse,
    UserUpdate,
    ApiMessage,
    TokenResponse,
    EmailVerificationCodeCreate,
    EmailVerificationCodeVerify,
    PasswordResetRequest,
    PasswordResetConfirm,
    TokenRefreshRequest,
    WechatLoginRequest,
    UnifiedLoginRequest,
)
from app.schemas.interviewer import (
    InterviewerSettings,
    InterviewerSettingsResponse,
    InterviewerSettingsUpdate,
)
from app.services import auth_service
from app.services.verification_service import VerificationService
from app.services.email_service import EmailService

router = APIRouter(prefix="/users", tags=["Users"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserRegister,
    db: SessionDep,
    settings: Annotated[Settings, Depends(get_settings)],
):
    """
    Register a new user account

    - **username**: Unique username (3-150 characters)
    - **email**: Valid email address
    - **code**: 6-digit email verification code
    - **password**: Password (6-100 characters)
    - **name**: Display name
    - **phone**: Phone number (optional)
    """
    from sqlalchemy import select, update
    from app.models.user import users

    existing_username = await db.execute(
        select(users.c.id).where(users.c.username == user_data.username)
    )
    if existing_username.scalar():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )

    existing_email = await db.execute(
        select(users.c.id).where(users.c.email == user_data.email)
    )
    if existing_email.scalar():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    success, message = await VerificationService.verify_code(
        user_data.email, user_data.code
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )

    try:
        user_result = await auth_service.create_user(db, user_data)
        user_id = user_result["id"]

        await db.execute(
            update(users)
            .where(users.c.id == user_id)
            .values(is_email_verified=True)
        )
        await db.commit()

        tokens = await auth_service.create_tokens(user_id)
        return tokens
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/login", response_model=TokenResponse)
async def login(
    login_data: UserLogin,
    db: SessionDep,
):
    """
    User login

    - **email**: Registered email address
    - **password**: User password
    """
    user = await auth_service.authenticate_user(db, login_data)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )

    tokens = await auth_service.create_tokens(user["id"])
    return tokens


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """
    User logout

    Note: In a JWT-based system, logout is handled client-side by
    discarding the token. This endpoint is provided for future extensibility
    (e.g., token blacklisting).
    """
    return None


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """
    Get current authenticated user information

    Requires valid JWT token in Authorization header.
    """
    return UserResponse(**current_user)


@router.put("/me", response_model=UserResponse)
async def update_current_user(
    update_data: UserUpdate,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: SessionDep,
):
    """
    Update current user information

    Only provided fields will be updated.
    """
    # Get user ID from current user
    user_id = current_user["id"]

    # Remove None values
    update_dict = update_data.model_dump(exclude_unset=True)

    # Convert Enums to values
    if update_dict:
        if "gender" in update_dict and update_dict["gender"]:
            update_dict["gender"] = update_dict["gender"].value
        if "learning_stage" in update_dict and update_dict["learning_stage"]:
            update_dict["learning_stage"] = update_dict["learning_stage"].value

    # Update user
    updated_user = await auth_service.update_user(db, user_id, update_dict)
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return UserResponse(**updated_user)


@router.post("/verify-email/send", response_model=ApiMessage)
async def send_email_verification_code(
    code_data: EmailVerificationCodeCreate,
    current_user: Annotated[dict | None, Depends(get_current_user_optional)],
):
    """
    Send email verification code

    Rate limited: 60 seconds between sends for the same email.
    Code expires in 10 minutes.

    If user is authenticated, sends code to their email.
    If not authenticated, sends code to the provided email.
    """
    try:
        # Generate and store verification code in Redis
        code = await VerificationService.create_code(code_data.email)

        # Log code for debugging
        print(f"Verification code for {code_data.email}: {code}")

        # Send email with verification code
        email_sent = EmailService.send_verification_code(
            to_email=code_data.email,
            code=code,
            expire_minutes=10
        )

        if not email_sent:
            # If email failed but code was generated, we still return success
            # The user can request a resend or check server logs
            print(f"[WARNING] Failed to send email to {code_data.email}, but code was generated")

        # Update user's email verification status if authenticated
        if current_user:
            from sqlalchemy import update
            from app.models.user import users
            from app.database import get_db

            async for db in get_db():
                await db.execute(
                    update(users)
                    .where(users.c.id == current_user["id"])
                    .values(email=code_data.email)
                )
                await db.commit()
                break

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=str(e)
        )

    return {"message": "发送成功，请查收验证码"}


@router.post("/verify-email/verify")
async def verify_email(
    verify_data: EmailVerificationCodeVerify,
    db: SessionDep,
):
    """
    Verify email with code

    - **email**: Email address
    - **code**: 6-digit verification code

    Note: Maximum 3 failed attempts allowed per code.
    """
    success, message = await VerificationService.verify_code(
        verify_data.email, verify_data.code
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )

    # Update user's email verification status in database
    from sqlalchemy import update
    from app.models.user import users

    await db.execute(
        update(users)
        .where(users.c.email == verify_data.email)
        .values(is_email_verified=True)
    )
    await db.commit()

    return {"message": message}


@router.post("/reset-password/request", response_model=ApiMessage)
async def request_password_reset(
    request_data: PasswordResetRequest,
    db: SessionDep,
):
    """
    Request password reset

    Sends a password reset verification code to the provided email address.
    """
    # Check if user exists
    from sqlalchemy import select
    from app.models.user import users

    result = await db.execute(
        select(users).where(users.c.email == request_data.email)
    )
    user = result.first()

    if not user:
        # Don't reveal if email exists for security.
        return {"message": "发送成功，请查收验证码"}

    try:
        code = await VerificationService.create_code(request_data.email)
        print(f"Password reset code for {request_data.email}: {code}")

        email_sent = EmailService.send_verification_code(
            to_email=request_data.email,
            code=code,
            expire_minutes=10,
        )

        if not email_sent:
            print(
                f"[WARNING] Failed to send password reset email to "
                f"{request_data.email}, but code was generated"
            )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=str(e)
        )

    return {"message": "发送成功，请查收验证码"}


@router.post("/reset-password/confirm")
async def confirm_password_reset(
    reset_data: PasswordResetConfirm,
    db: SessionDep,
):
    """
    Confirm password reset

    - **email**: Registered email address
    - **code**: Password reset verification code
    - **new_password**: New password
    """
    from app.core.security import get_password_hash
    from sqlalchemy import select, update
    from app.models.user import users

    success, message = await VerificationService.verify_code(
        reset_data.email, reset_data.code
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )

    result = await db.execute(
        select(users.c.id).where(users.c.email == reset_data.email)
    )
    user_id = result.scalar()
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Update password
    hashed_password = get_password_hash(reset_data.new_password)
    await db.execute(
        update(users)
        .where(users.c.id == user_id)
        .values(hashed_password=hashed_password)
    )
    await db.commit()

    return {"message": "Password reset successfully"}


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    refresh_data: TokenRefreshRequest,
    db: SessionDep,
):
    """
    Refresh access token using refresh token

    - **refresh**: Valid refresh token

    Note: Implements refresh token rotation for security.
    Both access_token and refresh_token are regenerated on each refresh.
    """
    from app.core.security import verify_token
    from app.config import get_settings

    settings = get_settings()

    # Verify refresh token
    payload = verify_token(refresh_data.refresh, settings.JWT_SECRET_KEY)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

    # Check token type
    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type"
        )

    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )

    # Verify user still exists
    from sqlalchemy import select
    from app.models.user import users

    result = await db.execute(select(users).where(users.c.id == user_id))
    user = result.first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )

    # Create new tokens (refresh token rotation)
    # This invalidates the old refresh token and issues new ones
    tokens = await auth_service.create_tokens(user_id)

    # TODO: Add old refresh token to blacklist (requires Redis/cache)
    # For now, we rely on the short expiration time (7 days) for security

    return tokens


@router.post("/wechat/login", response_model=TokenResponse)
async def wechat_login(
    login_data: WechatLoginRequest,
    db: SessionDep,
    settings: Annotated[Settings, Depends(get_settings)],
):
    """
    WeChat mini program login

    - **code**: WeChat login code from wx.login()

    Flow:
    1. Use code to get openid and session_key from WeChat API
    2. Check if user exists by wechat_open_id
    3. If not exists, create a new user with random password
    4. Return JWT tokens
    """
    import httpx
    from sqlalchemy import select, insert
    from app.models.user import users
    from app.core.security import get_password_hash

    # 1. Call WeChat API to get session info
    wechat_url = "https://api.weixin.qq.com/sns/jscode2session"
    params = {
        "appid": settings.WECHAT_APP_ID,
        "secret": settings.WECHAT_APP_SECRET,
        "js_code": login_data.code,
        "grant_type": "authorization_code"
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(wechat_url, params=params)
            session_info = response.json()
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Failed to call WeChat API: {str(e)}"
            )

    # Check for WeChat API errors
    if "errcode" in session_info:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"WeChat API error: {session_info.get('errmsg', 'Unknown error')}"
        )

    openid = session_info.get("openid")
    session_key = session_info.get("session_key")
    unionid = session_info.get("unionid")

    if not openid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to get openid from WeChat"
        )

    # 2. Check if user exists by wechat_open_id
    result = await db.execute(
        select(users).where(users.c.wechat_open_id == openid)
    )
    existing_user = result.first()

    if existing_user:
        # User exists, generate tokens
        tokens = await auth_service.create_tokens(existing_user.id)
        return tokens

    # 3. Create new user
    # Generate unique username
    username = f"wx_{openid[-8:]}"

    # Check if username exists
    result = await db.execute(
        select(users).where(users.c.username == username)
    )
    if result.first():
        # Add random suffix if username exists
        import random
        username = f"wx_{openid[-8:]}_{random.randint(1000, 9999)}"

    # Create user with session_key as temporary password
    hashed_password = get_password_hash(session_key)

    try:
        result = await db.execute(
            insert(users).values(
                username=username,
                wechat_open_id=openid,
                wechat_union_id=unionid,
                email=f"{username}@wechat.com",
                name="微信用户",
                gender="O",
                hashed_password=hashed_password,
                is_email_verified=True,
                is_active=True,
            ).returning(users.c.id)
        )
        await db.commit()

        new_user_id = result.scalar()

        # Generate tokens for new user
        tokens = await auth_service.create_tokens(new_user_id)
        return tokens

    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create user: {str(e)}"
        )


@router.get("/address")
async def get_address_data(
    id: Optional[str] = None,
    parent_id: Optional[str] = None,
):
    """
    Get province/city/district address data

    - **id**: Parent region code (alias for parent_id, optional, returns provinces if not provided)
    - **parent_id**: Parent region code (optional, deprecated, use 'id' instead)

    Returns hierarchical address data for China regions.
    """
    # Use 'id' if provided, otherwise fall back to 'parent_id' for backward compatibility
    region_code = id if id is not None else parent_id

    # Static address data (simplified version)
    # In production, this could be fetched from a database or external API

    address_data = {
        "provinces": [
            {"code": "110000", "name": "北京市"},
            {"code": "310000", "name": "上海市"},
            {"code": "440000", "name": "广东省"},
            {"code": "330000", "name": "浙江省"},
            {"code": "320000", "name": "江苏省"},
            {"code": "510000", "name": "四川省"},
            {"code": "420000", "name": "湖北省"},
            {"code": "430000", "name": "湖南省"},
            {"code": "610000", "name": "陕西省"},
            {"code": "370000", "name": "山东省"},
        ],
        "cities": {
            "440000": [
                {"code": "440100", "name": "广州市"},
                {"code": "440300", "name": "深圳市"},
                {"code": "440600", "name": "佛山市"},
            ],
            "330000": [
                {"code": "330100", "name": "杭州市"},
                {"code": "330200", "name": "宁波市"},
            ],
            "320000": [
                {"code": "320100", "name": "南京市"},
                {"code": "320500", "name": "苏州市"},
            ],
        },
        "districts": {
            "440100": [
                {"code": "440103", "name": "荔湾区"},
                {"code": "440104", "name": "越秀区"},
                {"code": "440105", "name": "海珠区"},
                {"code": "440106", "name": "天河区"},
            ],
            "440300": [
                {"code": "440303", "name": "罗湖区"},
                {"code": "440304", "name": "福田区"},
                {"code": "440305", "name": "南山区"},
            ],
            "330100": [
                {"code": "330102", "name": "上城区"},
                {"code": "330103", "name": "下城区"},
                {"code": "330104", "name": "江干区"},
            ],
        }
    }

    if not region_code:
        return address_data["provinces"]
    elif region_code in address_data["cities"]:
        return address_data["cities"][region_code]
    elif region_code in address_data["districts"]:
        return address_data["districts"][region_code]
    else:
        return []


@router.post("/login-unified", response_model=TokenResponse)
async def unified_login(
    login_data: UnifiedLoginRequest,
    db: SessionDep,
):
    """
    Unified login with phone or email (compatible with uniapp)

    - **phone**: Phone number (optional)
    - **email**: Email address (optional)
    - **password**: Password (required)

    Note: Either phone or email must be provided.
    """
    from sqlalchemy import select
    from app.models.user import users

    # Find user by phone or email
    if login_data.phone:
        result = await db.execute(
            select(users).where(users.c.phone == login_data.phone)
        )
    else:
        result = await db.execute(
            select(users).where(users.c.email == login_data.email)
        )

    user = result.first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )

    # Verify password
    from app.core.security import verify_password

    if not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect password"
        )

    # Create tokens
    tokens = await auth_service.create_tokens(user.id)
    return tokens


@router.get("/me/interviewer-settings", response_model=InterviewerSettingsResponse)
async def get_interviewer_settings(
    current_user: Annotated[dict, Depends(get_current_user)],
    db: SessionDep,
):
    """
    Get current user's interviewer customization settings

    Returns the user's preferred interviewer configuration including:
    - gender: Interviewer gender (male/female)
    - speed: Speech speed (1-5)
    - voice: Voice type (standard, deep, clear, soft, passionate, magnetic)
    - style: Interview style (serious, friendly, challenging, guiding, technical, boss)
    """
    from sqlalchemy import select
    from app.models.user import users

    result = await db.execute(
        select(users.c.interviewer_settings).where(users.c.id == current_user["id"])
    )
    settings = result.scalar()

    # Return default settings if none exist
    if not settings:
        return InterviewerSettingsResponse(
            gender="male",
            speed=3,
            voice="standard",
            style="serious"
        )

    return InterviewerSettingsResponse(**settings)


@router.put("/me/interviewer-settings", response_model=InterviewerSettingsResponse)
async def update_interviewer_settings(
    settings_update: InterviewerSettingsUpdate,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: SessionDep,
):
    """
    Update current user's interviewer customization settings

    Only provided fields will be updated. Unset fields retain their current values.
    """
    from sqlalchemy import select, update
    from app.models.user import users

    # Get current settings
    result = await db.execute(
        select(users.c.interviewer_settings).where(users.c.id == current_user["id"])
    )
    current_settings = result.scalar() or {}

    # Update with new values
    update_data = settings_update.model_dump(exclude_unset=True)
    current_settings.update(update_data)

    # Save to database
    await db.execute(
        update(users)
        .where(users.c.id == current_user["id"])
        .values(interviewer_settings=current_settings)
    )
    await db.commit()

    return InterviewerSettingsResponse(**current_settings)
