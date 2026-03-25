"""Tests for RAGRecommender"""
import pytest
from unittest.mock import AsyncMock, MagicMock

from app.recommenders.rag_recommender import RAGRecommender


@pytest.fixture
def rag_recommender():
    """Create RAG recommender with mock embedding service"""
    mock_embedding = MagicMock()
    mock_embedding.get_top_k_similar = AsyncMock(return_value=[])
    return RAGRecommender(embedding_service=mock_embedding, llm_engine=None)


@pytest.fixture
def sample_evaluation():
    """Sample evaluation with weak areas"""
    return {
        "id": 1,
        "user_id": 1,
        "overall_evaluation": "总体良好",
        "professional_knowledge": 55,
        "skill_match": 70,
        "language_expression": 50,
        "logical_thinking": 65,
        "stress_response": 75,
        "personality": 80,
        "motivation": 60,
        "value": 55,
    }


class TestRAGRecommender:
    """Test cases for RAGRecommender"""

    def test_identify_weak_areas(self, rag_recommender, sample_evaluation):
        """Test weak area identification (scores < 60)"""
        weak = rag_recommender._identify_weak_areas(sample_evaluation)
        assert "专业知识" in weak
        assert "语言表达" in weak
        assert "价值观匹配" in weak
        assert "逻辑思维" not in weak  # 65 >= 60

    def test_identify_weak_areas_all_good(self, rag_recommender):
        """Test no weak areas when all scores >= 60"""
        ev = {k: 70 for k in ["professional_knowledge", "skill_match", "language_expression",
                              "logical_thinking", "stress_response", "personality", "motivation", "value"]}
        ev["id"] = 1
        weak = rag_recommender._identify_weak_areas(ev)
        assert weak == []

    def test_build_query_text(self, rag_recommender, sample_evaluation):
        """Test query text building"""
        weak = ["专业知识", "语言表达"]
        text = rag_recommender._build_query_text(sample_evaluation, weak)
        assert "专业知识" in text or "55" in text
        assert "语言表达" in text or "50" in text

    @pytest.mark.asyncio
    async def test_async_recommend_no_evaluation(self, rag_recommender):
        """Test returns empty when evaluation not found"""
        mock_db = AsyncMock()
        # Mock _get_evaluation to return None
        rag_recommender._get_evaluation = AsyncMock(return_value=None)
        result = await rag_recommender.async_recommend(mock_db, evaluation_id=999, limit=5)
        assert result["weak_areas"] == []
        assert result["recommendations"] == []
        assert "评估记录不存在" in result["overall_advice"]

    @pytest.mark.asyncio
    async def test_async_recommend_no_weak_areas(self, rag_recommender, sample_evaluation):
        """Test returns empty recommendations when no weak areas"""
        sample_evaluation["professional_knowledge"] = 80
        sample_evaluation["language_expression"] = 85
        sample_evaluation["value"] = 90
        mock_db = AsyncMock()
        rag_recommender._get_evaluation = AsyncMock(return_value=sample_evaluation)
        result = await rag_recommender.async_recommend(mock_db, evaluation_id=1, limit=5)
        assert result["weak_areas"] == []
        assert "优秀" in result["overall_advice"] or "继续保持" in result["overall_advice"]

    @pytest.mark.asyncio
    async def test_async_recommend_fallback_with_resources(self, rag_recommender, sample_evaluation):
        """Test fallback recommendations when vector search returns results"""
        mock_db = AsyncMock()
        rag_recommender._get_evaluation = AsyncMock(return_value=sample_evaluation)
        rag_recommender._get_all_resources = AsyncMock(return_value=[
            {"id": 1, "name": "Python基础", "tags": "Python", "resource_type": "course", "difficulty": "easy"},
        ])
        rag_recommender._apply_filters = lambda r, f: r
        rag_recommender._vector_search = AsyncMock(return_value=[
            {"id": 1, "name": "Python基础", "score": 0.9, "similarity": 0.9, "tags": "Python",
             "resource_type": "course", "url": "https://example.com/python", "difficulty": "easy",
             "duration_or_quantity": "30分钟"},
        ])
        result = await rag_recommender.async_recommend(mock_db, evaluation_id=1, limit=5)
        assert "weak_areas" in result
        assert "recommendations" in result
        assert "overall_advice" in result
        if result["recommendations"]:
            assert "resource_id" in result["recommendations"][0] or "resource_name" in result["recommendations"][0]

    def test_train(self, rag_recommender):
        """Test train method exists (no-op or cache clear)"""
        rag_recommender.train()
