"""Learning API tests"""
import pytest
from fastapi import status

pytestmark = pytest.mark.asyncio


class TestResources:
    async def test_list_resources(self, client):
        """Test listing resources"""
        response = await client.get("/api/v1/learning/resources")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "items" in data

    async def test_create_resource(self, client, user_token):
        """Test creating resource"""
        resource_data = {
            "name": "Test Resource",
            "resource_type": "course",
            "tags": "test,beginner",
            "url": "https://example.com/test",
            "duration_or_quantity": "5 hours",
            "difficulty": "easy"
        }
        response = await client.post(
            "/api/v1/learning/resources",
            json=resource_data,
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["name"] == "Test Resource"
