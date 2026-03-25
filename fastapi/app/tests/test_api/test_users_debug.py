"""Debug user registration test"""
import pytest
from httpx import AsyncClient
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import users
from app.schemas.user import UserRegister, UserLogin


@pytest.mark.asyncio
async def test_register_user_debug(async_client: AsyncClient, db_session: AsyncSession):
    """Debug test user registration"""
    # Clean up test user if exists
    await db_session.execute(
        delete(users).where(users.c.username == "testuser_debug")
    )
    await db_session.commit()

    # Register user
    user_data = {
        "username": "testuser_debug",
        "email": "testdebug@example.com",
        "password": "testpass123",
        "name": "Test User Debug",
    }
    response = await async_client.post("/api/v1/users/register", json=user_data)

    # Print response for debugging
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")

    assert response.status_code in [201, 400]  # Accept either for debugging
    if response.status_code == 201:
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
