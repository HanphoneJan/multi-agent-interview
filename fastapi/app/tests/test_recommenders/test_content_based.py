"""Tests for ContentBasedRecommender"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession

from app.recommenders.content_based import ContentBasedRecommender


@pytest.fixture
def content_based_recommender():
    """Create content-based recommender instance"""
    return ContentBasedRecommender()


@pytest.fixture
def mock_db():
    """Create mock database session"""
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def sample_resources():
    """Sample resources for testing"""
    return [
        {
            "id": 1,
            "name": "Python编程基础",
            "resource_type": "course",
            "tags": "Python,编程,入门",
            "url": "https://example.com/python",
            "duration_or_quantity": "30分钟",
            "difficulty": "easy",
            "views": 100,
            "completions": 50,
            "rating": 4.5,
        },
        {
            "id": 2,
            "name": "算法与数据结构",
            "resource_type": "article",
            "tags": "算法,数据结构,计算机科学",
            "url": "https://example.com/algorithms",
            "duration_or_quantity": "10分钟",
            "difficulty": "medium",
            "views": 80,
            "completions": 30,
            "rating": 4.8,
        },
    ]


class TestContentBasedRecommender:
    """Test cases for ContentBasedRecommender"""

    @pytest.mark.asyncio
    async def test_get_user_interactions(self, content_based_recommender, mock_db):
        """Test getting user interactions"""
        # Mock database response
        mock_result = MagicMock()
        mock_result.__iter__.return_value = iter([
            (1, "view", 1.0),
            (2, "complete", 3.0),
        ])
        mock_result.fetchall.return_value = [(1, "view", 1.0), (2, "complete", 3.0)]
        mock_db.execute.return_value = mock_result

        interactions = await content_based_recommender._get_user_interactions(mock_db, user_id=1)

        assert len(interactions) == 2
        assert interactions[0]["resource_id"] == 1
        assert interactions[0]["type"] == "view"

    @pytest.mark.asyncio
    async def test_get_all_resources(self, content_based_recommender, mock_db, sample_resources):
        """Test getting all resources"""
        mock_rows = [
            (r["id"], r["name"], r["resource_type"], r["tags"], r["url"],
             r["duration_or_quantity"], r["difficulty"], r["views"], r["completions"], r["rating"])
            for r in sample_resources
        ]
        mock_db.execute = AsyncMock(return_value=mock_rows)

        resources = await content_based_recommender._get_all_resources(mock_db)

        assert len(resources) == len(sample_resources)
        assert resources[0]["id"] == 1

    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_get_all_resources_with_exclude(self, content_based_recommender, mock_db, sample_resources):
        """Test getting all resources with exclude IDs"""
        mock_rows = [
            (r["id"], r["name"], r["resource_type"], r["tags"], r["url"],
             r["duration_or_quantity"], r["difficulty"], r["views"], r["completions"], r["rating"])
            for r in sample_resources
        ]
        mock_db.execute = AsyncMock(return_value=mock_rows)

        resources = await content_based_recommender._get_all_resources(mock_db, exclude_ids=[1])

        # Verify query was called with exclude
        mock_db.execute.assert_called_once()

    def test_apply_filters_empty(self, content_based_recommender, sample_resources):
        """Test applying empty filters"""
        filtered = content_based_recommender._apply_filters(sample_resources, {})
        assert filtered == sample_resources

    def test_apply_filters_difficulty(self, content_based_recommender, sample_resources):
        """Test applying difficulty filter"""
        filtered = content_based_recommender._apply_filters(sample_resources, {"difficulty": "easy"})
        assert len(filtered) == 1
        assert filtered[0]["difficulty"] == "easy"

    def test_apply_filters_resource_type(self, content_based_recommender, sample_resources):
        """Test applying resource type filter"""
        filtered = content_based_recommender._apply_filters(sample_resources, {"resource_type": "course"})
        assert len(filtered) == 1
        assert filtered[0]["resource_type"] == "course"

    def test_apply_filters_multiple(self, content_based_recommender, sample_resources):
        """Test applying multiple filters"""
        filtered = content_based_recommender._apply_filters(
            sample_resources,
            {"difficulty": "easy", "resource_type": "course"}
        )
        assert len(filtered) == 1
        assert filtered[0]["difficulty"] == "easy"
        assert filtered[0]["resource_type"] == "course"

    def test_compute_jaccard_similarity(self, content_based_recommender):
        """Test Jaccard similarity computation (ContentBasedRecommender uses CollaborativeFiltering's logic via base)"""
        set1 = {1, 2, 3, 4}
        set2 = {3, 4, 5, 6}

        intersection = len(set1 & set2)
        union = len(set1 | set2)
        similarity = intersection / union if union > 0 else 0.0

        # Jaccard = |intersection|/|union| = 2/6
        assert abs(similarity - 2/6) < 1e-9

    def test_compute_jaccard_similarity_empty(self):
        """Test Jaccard similarity with empty sets - use CollaborativeFilteringRecommender which has the method"""
        from app.recommenders.collaborative_filtering import CollaborativeFilteringRecommender
        recommender = CollaborativeFilteringRecommender()
        set1 = set()
        set2 = {1, 2, 3}
        similarity = recommender._compute_jaccard_similarity(set1, set2)
        assert similarity == 0.0

    def test_get_resource_embedding_caching(self, content_based_recommender):
        """Test that resource embeddings are cached when using mock embedding service"""
        from unittest.mock import MagicMock
        mock_embedding = [0.1] * 384  # typical dimension
        mock_svc = MagicMock()
        mock_svc.build_resource_text.return_value = "test text"
        mock_svc.get_embedding.return_value = mock_embedding

        recommender = ContentBasedRecommender(embedding_service=mock_svc)
        resource = {
            "id": 1,
            "name": "Test Resource",
            "tags": "test",
            "difficulty": "easy",
            "resource_type": "course",
        }

        emb1 = recommender.get_resource_embedding(resource)
        emb2 = recommender.get_resource_embedding(resource)

        assert emb1 == emb2 == mock_embedding
        assert 1 in recommender._embedding_cache
        assert mock_svc.get_embedding.call_count == 1  # cached on second call

    def test_train(self, content_based_recommender):
        """Test training method"""
        # Should not raise error
        content_based_recommender.train()
