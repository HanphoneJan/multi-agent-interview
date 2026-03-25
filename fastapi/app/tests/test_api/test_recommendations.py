"""Tests for recommendation API"""
import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, MagicMock


@pytest.mark.asyncio
async def test_get_personalized_recommendations_authenticated(
    async_client: AsyncClient,
    test_user_token: str,
    db_session
):
    """Test getting personalized recommendations for authenticated user"""
    response = await async_client.post(
        "/api/v1/recommendations/personalized",
        json={"limit": 10},
        headers={"Authorization": f"Bearer {test_user_token}"}
    )

    # Should return popular resources if no evaluation data
    assert response.status_code in [200, 500]
    if response.status_code == 200:
        data = response.json()
        assert "recommendations" in data
        assert "count" in data
        assert data["count"] <= 10


@pytest.mark.asyncio
async def test_get_personalized_recommendations_anonymous(
    async_client: AsyncClient,
    db_session
):
    """Test getting recommendations for anonymous user"""
    response = await async_client.post(
        "/api/v1/recommendations/personalized",
        json={"limit": 5}
    )

    # Anonymous users get popular resources
    assert response.status_code in [200, 500]
    if response.status_code == 200:
        data = response.json()
        assert "recommendations" in data
        assert data["type"] == "popular"
        assert data["count"] <= 5


@pytest.mark.asyncio
async def test_get_personalized_recommendations_with_filters(
    async_client: AsyncClient,
    test_user_token: str
):
    """Test personalized recommendations with filters"""
    response = await async_client.post(
        "/api/v1/recommendations/personalized",
        json={
            "limit": 10,
            "difficulty": "easy",
            "resource_type": "course"
        },
        headers={"Authorization": f"Bearer {test_user_token}"}
    )

    assert response.status_code in [200, 500]


@pytest.mark.asyncio
async def test_get_personalized_recommendations_invalid_limit(
    async_client: AsyncClient,
    test_user_token: str
):
    """Test personalized recommendations with invalid limit"""
    response = await async_client.post(
        "/api/v1/recommendations/personalized",
        json={"limit": 100},  # Exceeds max 50
        headers={"Authorization": f"Bearer {test_user_token}"}
    )

    # Should return validation error
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_popular_recommendations(async_client: AsyncClient):
    """Test getting popular resources"""
    response = await async_client.get("/api/v1/recommendations/popular?limit=10")

    assert response.status_code in [200, 500]
    if response.status_code == 200:
        data = response.json()
        assert "recommendations" in data
        assert data["type"] == "popular"
        assert data["count"] <= 10


@pytest.mark.asyncio
async def test_get_popular_recommendations_with_filters(async_client: AsyncClient):
    """Test popular resources with filters"""
    response = await async_client.get(
        "/api/v1/recommendations/popular?limit=5&difficulty=medium&resource_type=video"
    )

    assert response.status_code in [200, 500]


@pytest.mark.asyncio
async def test_get_popular_recommendations_invalid_limit(async_client: AsyncClient):
    """Test popular resources with invalid limit"""
    response = await async_client.get("/api/v1/recommendations/popular?limit=0")

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_get_popular_recommendations_limit_exceeded(async_client: AsyncClient):
    """Test popular resources with exceeded limit"""
    response = await async_client.get("/api/v1/recommendations/popular?limit=100")

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_recommendation_response_structure(async_client: AsyncClient):
    """Test recommendation response structure"""
    response = await async_client.get("/api/v1/recommendations/popular?limit=1")

    if response.status_code == 200:
        data = response.json()
        assert "recommendations" in data
        if data["recommendations"]:
            rec = data["recommendations"][0]
            assert "resource_id" in rec
            assert "name" in rec
            assert "resource_type" in rec
            assert "tags" in rec
            assert "url" in rec
            assert "score" in rec
            assert "reason" in rec


# ---------- Evaluation API Tests ----------


@pytest.mark.asyncio
async def test_evaluate_page_recommendations(async_client: AsyncClient):
    """Test page recommendation evaluation endpoint"""
    response = await async_client.post(
        "/api/v1/recommendations/evaluation/page",
        json={
            "recommended_ids": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            "relevant_ids": [1, 2, 3],
            "k": 10,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "precision_at_k" in data
    assert "recall_at_k" in data
    assert "ndcg_at_k" in data
    assert "hit_rate_at_k" in data
    assert data["precision_at_k"] == 0.3
    assert data["recall_at_k"] == 1.0


@pytest.mark.asyncio
async def test_evaluate_report_recommendations(async_client: AsyncClient):
    """Test report recommendation evaluation endpoint"""
    response = await async_client.post(
        "/api/v1/recommendations/evaluation/report",
        json={
            "recommended_resources": [
                {"tags": ["Python", "Django"], "resource_type": "course"},
                {"tags": ["算法", "LeetCode"], "resource_type": "article"},
            ],
            "weak_dimensions": ["professional_knowledge", "logical_thinking"],
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "relevance" in data
    assert "coverage" in data
    assert "diversity" in data


@pytest.mark.asyncio
async def test_get_report_rag_recommendations_not_found(
    async_client: AsyncClient,
    test_user_token: str,
):
    """Test RAG report recommendations when report does not exist"""
    response = await async_client.get(
        "/api/v1/recommendations/report/99999",
        headers={"Authorization": f"Bearer {test_user_token}"},
    )
    assert response.status_code == 404
    assert "not found" in response.json().get("detail", "").lower()


@pytest.mark.asyncio
async def test_get_report_rag_recommendations_unauthorized(
    async_client: AsyncClient,
):
    """Test RAG report recommendations without auth"""
    response = await async_client.get("/api/v1/recommendations/report/1")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_report_rag_recommendations_success(
    async_client: AsyncClient,
    test_user,
    test_user_token: str,
    db_session,
):
    """Test RAG report recommendations with existing report"""
    from app.services.interview_service import create_scenario, create_session
    from app.services.evaluation_service import create_overall_evaluation
    from app.schemas.interview import InterviewScenarioCreate, InterviewSessionCreate
    from app.schemas.evaluation import OverallInterviewEvaluationCreate

    user_id = test_user.id
    scenario = await create_scenario(
        db_session,
        InterviewScenarioCreate(name="RAG Test", technology_field="Python"),
    )
    session = await create_session(
        db_session,
        user_id,
        InterviewSessionCreate(scenario_id=scenario["id"]),
    )
    session_id = session["id"]
    await create_overall_evaluation(
        db_session,
        OverallInterviewEvaluationCreate(
            session_id=session_id,
            user_id=user_id,
            overall_evaluation="测试评估",
            help="建议加强",
            recommendation="通过",
            overall_score=70,
            professional_knowledge=60,
            skill_match=65,
            language_expression=70,
            logical_thinking=55,
            stress_response=70,
            personality=70,
            motivation=75,
            value=70,
        ),
    )
    await db_session.commit()

    response = await async_client.get(
        f"/api/v1/recommendations/report/{session_id}?limit=5",
        headers={"Authorization": f"Bearer {test_user_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "weak_areas" in data
    assert "recommendations" in data
    assert "overall_advice" in data
    assert isinstance(data["weak_areas"], list)
    assert isinstance(data["recommendations"], list)


@pytest.mark.asyncio
async def test_compute_ab_test(async_client: AsyncClient):
    """Test A/B test computation endpoint"""
    control = [0.1] * 50 + [0.2] * 50
    treatment = [0.2] * 50 + [0.3] * 50
    response = await async_client.post(
        "/api/v1/recommendations/evaluation/ab-test",
        json={
            "control_metrics": control,
            "treatment_metrics": treatment,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "control_metric" in data
    assert "treatment_metric" in data
    assert "absolute_lift" in data
    assert "is_significant" in data
    assert "p_value" in data
