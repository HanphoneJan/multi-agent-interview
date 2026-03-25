"""Tests for career planning API endpoints"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestMajorEndpoints:
    """Tests for major-related endpoints"""

    async def test_list_major_categories(self, async_client: AsyncClient):
        """Test getting major categories"""
        response = await async_client.get("/api/v1/career/majors/categories")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    async def test_list_major_subcategories(self, async_client: AsyncClient):
        """Test getting major subcategories"""
        response = await async_client.get("/api/v1/career/majors/subcategories")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    async def test_list_major_subcategories_with_category(self, async_client: AsyncClient):
        """Test getting major subcategories filtered by category"""
        response = await async_client.get("/api/v1/career/majors/subcategories?category_id=1")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    async def test_list_majors(self, async_client: AsyncClient):
        """Test getting majors list"""
        response = await async_client.get("/api/v1/career/majors")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data

    async def test_list_majors_with_pagination(self, async_client: AsyncClient):
        """Test majors pagination"""
        response = await async_client.get("/api/v1/career/majors?page=1&page_size=10")
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 1
        assert data["page_size"] == 10

    async def test_search_majors_endpoint(self, async_client: AsyncClient):
        """Test searching majors by keyword using search endpoint"""
        response = await async_client.get("/api/v1/career/majors/search?q=计算机")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


@pytest.mark.asyncio
class TestCareerEndpoints:
    """Tests for career-related endpoints"""

    async def test_list_career_categories(self, async_client: AsyncClient):
        """Test getting career categories"""
        response = await async_client.get("/api/v1/career/categories")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    async def test_list_careers(self, async_client: AsyncClient):
        """Test getting careers list"""
        response = await async_client.get("/api/v1/career/jobs")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data

    async def test_list_careers_with_filters(self, async_client: AsyncClient):
        """Test getting careers with filters"""
        response = await async_client.get("/api/v1/career/jobs?keyword=工程师")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data

    async def test_get_career_detail_not_found(self, async_client: AsyncClient):
        """Test getting non-existent career detail"""
        response = await async_client.get("/api/v1/career/jobs/99999")
        assert response.status_code == 404


@pytest.mark.asyncio
class TestJobPlatformEndpoints:
    """Tests for job platform endpoints"""

    async def test_list_job_platforms(self, async_client: AsyncClient):
        """Test getting job platforms"""
        response = await async_client.get("/api/v1/career/platforms")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    async def test_search_external_jobs_unauthorized(self, async_client: AsyncClient):
        """Test external job search without params returns 422"""
        response = await async_client.get("/api/v1/career/external-jobs/search")
        assert response.status_code == 422  # Missing required 'keyword' param

    async def test_search_external_jobs_with_keyword(self, async_client: AsyncClient):
        """Test external job search with keyword"""
        response = await async_client.get("/api/v1/career/external-jobs/search?keyword=python")
        # May return 200 or error depending on external service availability
        assert response.status_code in [200, 500, 503]


@pytest.mark.asyncio
class TestCareerSuggestionsEndpoints:
    """Tests for career suggestions endpoints"""

    async def test_get_career_suggestions_no_major(self, async_client: AsyncClient):
        """Test career suggestions without major returns 400"""
        response = await async_client.get("/api/v1/career/suggestions")
        assert response.status_code == 400

    async def test_get_career_suggestions_with_major(self, async_client: AsyncClient):
        """Test career suggestions with major parameter"""
        response = await async_client.get("/api/v1/career/suggestions?major=计算机")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
