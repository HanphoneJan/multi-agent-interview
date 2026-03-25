"""Tests for RecommendationService"""
import pytest
from unittest.mock import AsyncMock, MagicMock

from app.services.recommendation_service import RecommendationService


@pytest.fixture
def recommendation_service():
    """Create recommendation service instance"""
    return RecommendationService()


@pytest.fixture
def mock_db():
    """Create mock database session"""
    return AsyncMock()


class TestRecommendationService:
    """Test cases for RecommendationService"""

    def test_hybrid_weights(self, recommendation_service):
        """Test hybrid recommendation weights"""
        assert recommendation_service.HYBRID_WEIGHTS["rule_based"] == 0.5
        assert recommendation_service.HYBRID_WEIGHTS["content_based"] == 0.3
        assert recommendation_service.HYBRID_WEIGHTS["collaborative"] == 0.2
        total = sum(recommendation_service.HYBRID_WEIGHTS.values())
        assert total == pytest.approx(1.0)

    def test_calculate_tag_similarity(self, recommendation_service):
        """Test tag similarity (Jaccard)"""
        sim = recommendation_service._calculate_tag_similarity(
            ["Python", "Java"],
            [["Python", "Go"], ["Java", "Rust"]]
        )
        assert 0 <= sim <= 1.0

    def test_calculate_tag_similarity_empty(self, recommendation_service):
        """Test tag similarity with empty tags"""
        assert recommendation_service._calculate_tag_similarity([], [["Python"]]) == 0.0
        assert recommendation_service._calculate_tag_similarity(["Python"], []) == 0.0

    def test_diversify_recommendations(self, recommendation_service):
        """Test diversity reordering"""
        recs = [
            {"id": 1, "resource_type": "course", "final_score": 0.9},
            {"id": 2, "resource_type": "course", "final_score": 0.8},
            {"id": 3, "resource_type": "article", "final_score": 0.7},
        ]
        diversified = recommendation_service._diversify_recommendations(recs)
        assert len(diversified) == len(recs)
        types = [r["resource_type"] for r in diversified]
        assert "course" in types
        assert "article" in types

    def test_merge_recommendations(self, recommendation_service):
        """Test merging recommendations from multiple sources"""
        rule = [{"id": 1, "rule_score": 0.8, "content_score": 0, "collab_score": 0}]
        content = [{"id": 1, "rule_score": 0, "content_score": 0.6, "collab_score": 0},
                  {"id": 2, "rule_score": 0, "content_score": 0.7, "collab_score": 0}]
        collab = [{"id": 1, "rule_score": 0, "content_score": 0, "collab_score": 0.5}]
        merged = recommendation_service._merge_recommendations(rule, content, collab)
        assert len(merged) >= 1
        for m in merged:
            assert "final_score" in m
