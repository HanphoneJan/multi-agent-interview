"""Tests for RuleBasedRecommender"""
import pytest
from unittest.mock import AsyncMock, MagicMock

from app.recommenders.rule_based import RuleBasedRecommender, _parse_tags


def test_parse_tags():
    """Test tag parsing"""
    assert _parse_tags("Python,Java") == ["Python", "Java"]
    assert _parse_tags("Python Java") == ["Python", "Java"]
    assert _parse_tags("") == []
    assert _parse_tags("  a  ") == ["a"]


@pytest.fixture
def rule_based_recommender():
    """Create rule-based recommender instance"""
    return RuleBasedRecommender()


class TestRuleBasedRecommender:
    """Test cases for RuleBasedRecommender"""

    def test_init_rules(self, rule_based_recommender):
        """Test rule configuration"""
        assert "professional_knowledge" in rule_based_recommender.rules
        assert rule_based_recommender.rules["professional_knowledge"]["threshold"] == 60
        assert "Python" in rule_based_recommender.rules["professional_knowledge"]["tags"]

    @pytest.mark.asyncio
    async def test_recommend_empty_without_db(self, rule_based_recommender):
        """Test returns empty when db is None"""
        result = await rule_based_recommender.recommend(user_id=1, limit=5, db=None)
        assert result == []

    @pytest.mark.asyncio
    async def test_recommend_returns_popular_when_no_evaluation(
        self, rule_based_recommender
    ):
        """Test returns popular resources when user has no evaluation"""
        mock_db = AsyncMock()
        # Mock: no evaluation row
        mock_result = MagicMock()
        mock_result.first.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)

        # Mock _get_popular_resources
        rule_based_recommender._get_popular_resources = AsyncMock(
            return_value=[
                {
                    "resource_id": 1,
                    "name": "Test",
                    "resource_type": "course",
                    "tags": ["Python"],
                    "difficulty": "easy",
                    "url": "https://example.com",
                    "duration_or_quantity": "30min",
                    "score": 0.9,
                    "reason": "Popular",
                    "recommender": "rule_based",
                }
            ]
        )

        result = await rule_based_recommender.recommend(user_id=1, limit=5, db=mock_db)
        assert len(result) == 1
        assert result[0]["resource_id"] == 1
        assert result[0]["recommender"] == "rule_based"

    def test_train_no_op(self, rule_based_recommender):
        """Test train is a no-op"""
        rule_based_recommender.train()
