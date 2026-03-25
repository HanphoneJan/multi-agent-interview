"""Test user API endpoints"""
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from app.core.security import verify_password
from app.models.user import users
from app.services.verification_service import VerificationService


async def create_registration_payload(**overrides):
    """Create registration payload with a valid verification code."""
    email = overrides.pop("email", f"register_{uuid.uuid4().hex[:8]}@example.com")
    payload = {
        "username": overrides.pop("username", f"user_{uuid.uuid4().hex[:8]}"),
        "email": email,
        "password": overrides.pop("password", "testpass123"),
    }

    await VerificationService.clear_all(email)
    payload["code"] = await VerificationService.create_code(email)
    payload.update(overrides)
    return payload


@pytest.mark.asyncio
async def test_register_user(async_client: AsyncClient):
    """Test user registration"""
    # Register user (password must be < 72 bytes for bcrypt)
    user_data = await create_registration_payload(
        username=f"testuser_{uuid.uuid4().hex[:8]}",
        email=f"test_{uuid.uuid4().hex[:8]}@example.com",
        password="test123",
        name="Test User",
    )
    response = await async_client.post("/api/v1/users/register", json=user_data)

    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_register_duplicate_username(async_client: AsyncClient):
    """Test registration with duplicate username"""
    # Register first user
    username = f"testuser_{uuid.uuid4().hex[:8]}"
    first_user = await create_registration_payload(
        username=username,
        email=f"test2_{uuid.uuid4().hex[:8]}@example.com",
        password="testpass123",
    )
    await async_client.post("/api/v1/users/register", json=first_user)

    # Try to register with same username
    duplicate_user = await create_registration_payload(
        username=username,
        email=f"test3_{uuid.uuid4().hex[:8]}@example.com",
        password="testpass123",
    )
    response = await async_client.post("/api/v1/users/register", json=duplicate_user)

    assert response.status_code == 400
    assert "already registered" in response.json()["detail"]


@pytest.mark.asyncio
async def test_login_success(async_client: AsyncClient):
    """Test successful login"""
    # Register user first
    email = f"login_{uuid.uuid4().hex[:8]}@example.com"
    user_data = await create_registration_payload(
        username=f"loginuser_{uuid.uuid4().hex[:8]}",
        email=email,
        password="loginpass123",
    )
    await async_client.post("/api/v1/users/register", json=user_data)

    # Login
    login_data = {
        "email": email,
        "password": "loginpass123",
    }
    response = await async_client.post("/api/v1/users/login", json=login_data)

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data


@pytest.mark.asyncio
async def test_login_invalid_credentials(async_client: AsyncClient):
    """Test login with invalid credentials"""
    login_data = {
        "email": "nonexistent@example.com",
        "password": "wrongpassword",
    }
    response = await async_client.post("/api/v1/users/login", json=login_data)

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user(async_client: AsyncClient):
    """Test getting current user info"""
    # Register and login
    username = f"getuser_{uuid.uuid4().hex[:8]}"
    email = f"getuser_{uuid.uuid4().hex[:8]}@example.com"
    user_data = await create_registration_payload(
        username=username,
        email=email,
        password="getpass123",
        name="Get User",
    )
    register_response = await async_client.post("/api/v1/users/register", json=user_data)
    token = register_response.json()["access_token"]

    # Get current user
    headers = {"Authorization": f"Bearer {token}"}
    response = await async_client.get("/api/v1/users/me", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert data["username"] == username
    assert data["email"] == email
    assert data["name"] == "Get User"


@pytest.mark.asyncio
async def test_get_current_user_unauthorized(async_client: AsyncClient):
    """Test getting current user without authorization"""
    response = await async_client.get("/api/v1/users/me")

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_update_user(async_client: AsyncClient):
    """Test updating user information"""
    # Register and login
    user_data = await create_registration_payload(
        username=f"updateuser_{uuid.uuid4().hex[:8]}",
        email=f"updateuser_{uuid.uuid4().hex[:8]}@example.com",
        password="updatepass123",
        name="Update User",
    )
    register_response = await async_client.post("/api/v1/users/register", json=user_data)
    token = register_response.json()["access_token"]

    # Update user
    update_data = {
        "name": "Updated Name",
        "major": "Computer Science",
        "university": "Test University",
    }
    headers = {"Authorization": f"Bearer {token}"}
    response = await async_client.put("/api/v1/users/me", json=update_data, headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Name"
    assert data["major"] == "Computer Science"


@pytest.mark.asyncio
async def test_send_verification_code(async_client: AsyncClient):
    """Test sending email verification code"""
    email = f"verify_{uuid.uuid4().hex[:8]}@example.com"

    # Clean up any existing verification data
    await VerificationService.clear_all(email)

    response = await async_client.post(
        "/api/v1/users/verify-email/send",
        json={"email": email}
    )

    assert response.status_code == 200
    assert response.json()["message"] == "发送成功，请查收验证码"

    # Clean up after test
    await VerificationService.clear_all(email)


@pytest.mark.asyncio
async def test_send_verification_code_rate_limit(async_client: AsyncClient):
    """Test rate limiting for sending verification code"""
    email = f"verify_{uuid.uuid4().hex[:8]}@example.com"

    # Clean up any existing verification data
    await VerificationService.clear_all(email)

    # First request should succeed
    response1 = await async_client.post(
        "/api/v1/users/verify-email/send",
        json={"email": email}
    )
    assert response1.status_code == 200

    # Second request within 60 seconds should fail with 429
    response2 = await async_client.post(
        "/api/v1/users/verify-email/send",
        json={"email": email}
    )
    assert response2.status_code == 429
    assert "wait" in response2.json()["detail"].lower()

    # Clean up after test
    await VerificationService.clear_all(email)


@pytest.mark.asyncio
async def test_verify_email_success(async_client: AsyncClient):
    """Test successful email verification"""
    email = f"verify_{uuid.uuid4().hex[:8]}@example.com"

    # Clean up any existing verification data
    await VerificationService.clear_all(email)

    # Create a verification code
    code = await VerificationService.create_code(email)

    response = await async_client.post(
        "/api/v1/users/verify-email/verify",
        json={"email": email, "code": code}
    )

    assert response.status_code == 200
    assert "success" in response.json()["message"].lower()


@pytest.mark.asyncio
async def test_verify_email_invalid_code(async_client: AsyncClient):
    """Test email verification with invalid code"""
    email = f"verify_{uuid.uuid4().hex[:8]}@example.com"

    # Clean up any existing verification data
    await VerificationService.clear_all(email)

    response = await async_client.post(
        "/api/v1/users/verify-email/verify",
        json={"email": email, "code": "000000"}
    )

    assert response.status_code == 400

    # Clean up after test
    await VerificationService.clear_all(email)


@pytest.mark.asyncio
async def test_verify_email_max_attempts(async_client: AsyncClient):
    """Test max attempts limit for email verification"""
    email = f"verify_{uuid.uuid4().hex[:8]}@example.com"

    # Clean up any existing verification data
    await VerificationService.clear_all(email)

    # Create a verification code
    code = await VerificationService.create_code(email)

    # Make 3 failed attempts
    for _ in range(3):
        response = await async_client.post(
            "/api/v1/users/verify-email/verify",
            json={"email": email, "code": "000000"}
        )
        assert response.status_code == 400

    # 4th attempt should fail with "too many attempts" message
    response = await async_client.post(
        "/api/v1/users/verify-email/verify",
        json={"email": email, "code": code}
    )
    assert response.status_code == 400
    assert "too many" in response.json()["detail"].lower()

    # Clean up after test
    await VerificationService.clear_all(email)


@pytest.mark.asyncio
async def test_logout(async_client: AsyncClient):
    """Test user logout"""
    # Register and login
    user_data = await create_registration_payload(
        username=f"logoutuser_{uuid.uuid4().hex[:8]}",
        email=f"logout_{uuid.uuid4().hex[:8]}@example.com",
        password="logoutpass123",
    )
    register_response = await async_client.post("/api/v1/users/register", json=user_data)
    token = register_response.json()["access_token"]

    # Logout
    headers = {"Authorization": f"Bearer {token}"}
    response = await async_client.post("/api/v1/users/logout", headers=headers)

    assert response.status_code == 204


@pytest.mark.asyncio
async def test_request_password_reset(async_client: AsyncClient):
    """Test requesting password reset code."""
    email = f"resetreq_{uuid.uuid4().hex[:8]}@example.com"

    register_response = await async_client.post(
        "/api/v1/users/register",
        json=await create_registration_payload(
            username=f"resetreq_{uuid.uuid4().hex[:8]}",
            email=email,
            password="resetreq123",
        ),
    )
    assert register_response.status_code == 201

    await VerificationService.clear_all(email)

    response = await async_client.post(
        "/api/v1/users/reset-password/request",
        json={"email": email},
    )

    assert response.status_code == 200
    assert response.json()["message"] == "发送成功，请查收验证码"

    await VerificationService.clear_all(email)


@pytest.mark.asyncio
async def test_reset_password_with_email_verification_code(
    async_client: AsyncClient,
    db_session: AsyncSession,
):
    """Test password reset using email + verification code."""
    email = f"reset_{uuid.uuid4().hex[:8]}@example.com"
    original_password = "oldpass123"
    new_password = "newpass123"

    register_response = await async_client.post(
        "/api/v1/users/register",
        json=await create_registration_payload(
            username=f"resetuser_{uuid.uuid4().hex[:8]}",
            email=email,
            password=original_password,
        ),
    )
    assert register_response.status_code == 201

    await VerificationService.clear_all(email)
    code = await VerificationService.create_code(email)

    response = await async_client.post(
        "/api/v1/users/reset-password/confirm",
        json={
            "email": email,
            "code": code,
            "new_password": new_password,
        },
    )

    assert response.status_code == 200
    assert response.json()["message"] == "Password reset successfully"

    result = await db_session.execute(select(users).where(users.c.email == email))
    user = result.first()
    assert user is not None
    assert verify_password(new_password, user.hashed_password)

    await VerificationService.clear_all(email)
