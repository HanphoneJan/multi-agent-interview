"""Tests for HybridRecommender"""
import pytest
from unittest.mock import AsyncMock, MagicMock

from app.recommenders.hybrid import HybridRecommender


@pytest.fixture
def mock_rule_based():
    """Mock rule-based recommender"""
    m = MagicMock()
    m.recommend = AsyncMock(return_value=[
        {"resource_id": 1, "score": 0.8, "reason": "rule", "resource_type": "course"},
        {"resource_id": 2, "score": 0.6, "reason": "rule", "resource_type": "article"},
    ])
    m.train = MagicMock()
    return m


@pytest.fixture
def mock_content_based():
    """Mock content-based recommender"""
    m = MagicMock()
    m.async_recommend = AsyncMock(return_value=[
        {"resource_id": 2, "score": 0.9, "reason": "content", "resource_type": "article"},
        {"resource_id": 3, "score": 0.7, "reason": "content", "resource_type": "video"},
    ])
    m.train = MagicMock()
    return m


@pytest.fixture
def mock_collaborative():
    """Mock collaborative recommender"""
    m = MagicMock()
    m.async_recommend = AsyncMock(return_value=[
        {"resource_id": 1, "score": 0.5, "reason": "collab", "resource_type": "course"},
        {"resource_id": 3, "score": 0.4, "reason": "collab", "resource_type": "video"},
    ])
    m.train = MagicMock()
    return m


@pytest.fixture
def hybrid_with_mocks(mock_rule_based, mock_content_based, mock_collaborative):
    """HybridRecommender with mocked components (avoids RuleBasedRecommender import)"""
    return HybridRecommender(
        rule_based=mock_rule_based,
        content_based=mock_content_based,
        collaborative=mock_collaborative,
    )


class TestHybridRecommender:
    """Test cases for HybridRecommender"""

    @pytest.mark.asyncio
    async def test_init_weights(self, hybrid_with_mocks):
        """Test weight configuration"""
        assert hybrid_with_mocks.weights["rule_based"] == 0.5
        assert hybrid_with_mocks.weights["content_based"] == 0.3
        assert hybrid_with_mocks.weights["collaborative"] == 0.2

    @pytest.mark.asyncio
    async def test_recommend_aggregates_sources(
        self, hybrid_with_mocks, mock_rule_based, mock_content_based, mock_collaborative
    ):
        """Test that recommendations from all sources are aggregated"""
        mock_db = AsyncMock()

        result = await hybrid_with_mocks.recommend(user_id=1, limit=5, db=mock_db)

        mock_rule_based.recommend.assert_called_once()
        mock_content_based.async_recommend.assert_called_once()
        mock_collaborative.async_recommend.assert_called_once()
        assert len(result) <= 5
        for rec in result:
            assert "resource_id" in rec
            assert "score" in rec
            assert "reason" in rec
            assert "recommender" in rec
            assert rec["recommender"] == "hybrid"

    @pytest.mark.asyncio
    async def test_recommend_empty_without_db(self, hybrid_with_mocks):
        """Test returns empty when db is None"""
        result = await hybrid_with_mocks.recommend(user_id=1, limit=5, db=None)
        assert result == []

    def test_apply_diversity(self, hybrid_with_mocks):
        """Test diversity limits per resource type"""
        resources = [
            {"resource_id": 1, "resource_type": "course", "score": 1.0},
            {"resource_id": 2, "resource_type": "course", "score": 0.9},
            {"resource_id": 3, "resource_type": "course", "score": 0.8},
            {"resource_id": 4, "resource_type": "article", "score": 0.7},
        ]
        diverse = hybrid_with_mocks._apply_diversity(resources, max_per_type=2)
        course_count = sum(1 for r in diverse if r["resource_type"] == "course")
        assert course_count <= 2

    def test_train_delegates_to_components(
        self, hybrid_with_mocks, mock_rule_based, mock_content_based, mock_collaborative
    ):
        """Test train() calls all component recommenders"""
        hybrid_with_mocks.train()
        mock_rule_based.train.assert_called_once()
        mock_content_based.train.assert_called_once()
        mock_collaborative.train.assert_called_once()
