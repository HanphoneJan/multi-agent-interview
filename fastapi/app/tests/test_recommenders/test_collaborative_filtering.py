"""Tests for CollaborativeFilteringRecommender"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession

from app.recommenders.collaborative_filtering import CollaborativeFilteringRecommender


@pytest.fixture
def collaborative_recommender():
    """Create collaborative filtering recommender instance"""
    return CollaborativeFilteringRecommender()


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
            "name": "Resource 1",
            "resource_type": "course",
            "tags": "Python,编程",
            "url": "https://example.com/1",
            "duration_or_quantity": "30分钟",
            "difficulty": "easy",
            "views": 100,
            "completions": 50,
            "rating": 4.5,
        },
        {
            "id": 2,
            "name": "Resource 2",
            "resource_type": "article",
            "tags": "算法",
            "url": "https://example.com/2",
            "duration_or_quantity": "10分钟",
            "difficulty": "medium",
            "views": 80,
            "completions": 30,
            "rating": 4.8,
        },
    ]


class TestCollaborativeFilteringRecommender:
    """Test cases for CollaborativeFilteringRecommender"""

    def test_init(self, collaborative_recommender):
        """Test initialization"""
        assert collaborative_recommender.name == "collaborative_filtering"
        assert collaborative_recommender._item_similarity_cache == {}

    @pytest.mark.asyncio
    async def test_get_user_liked_resources(self, collaborative_recommender, mock_db):
        """Test getting user's liked resources"""
        # Mock database response - code iterates over result with for row in result
        mock_rows = [
            (1, "view", 1.0),
            (2, "complete", 3.0),
            (1, "rate", 5.0),  # Multiple interactions with same resource
        ]
        mock_db.execute = AsyncMock(return_value=mock_rows)

        liked = await collaborative_recommender._get_user_liked_resources(mock_db, user_id=1)

        assert len(liked) > 0
        # Resource 1 should have aggregated score
        resource_1 = next((r for r in liked if r["resource_id"] == 1), None)
        assert resource_1 is not None
        assert resource_1["score"] > 0

    def test_get_user_liked_resources_weights(self, collaborative_recommender):
        """Test interaction weights"""
        assert "view" in collaborative_recommender.INTERACTION_WEIGHTS
        assert "complete" in collaborative_recommender.INTERACTION_WEIGHTS
        assert collaborative_recommender.INTERACTION_WEIGHTS["complete"] > collaborative_recommender.INTERACTION_WEIGHTS["view"]

    @pytest.mark.asyncio
    async def test_get_all_resources(self, collaborative_recommender, mock_db, sample_resources):
        """Test getting all resources"""
        mock_rows = [
            (r["id"], r["name"], r["resource_type"], r["tags"], r["url"],
             r["duration_or_quantity"], r["difficulty"], r["views"], r["completions"], r["rating"])
            for r in sample_resources
        ]
        mock_db.execute = AsyncMock(return_value=mock_rows)

        resources = await collaborative_recommender._get_all_resources(mock_db)

        assert len(resources) == len(sample_resources)

    @pytest.mark.asyncio
    async def test_get_all_resources_with_exclude(self, collaborative_recommender, mock_db, sample_resources):
        """Test getting all resources with exclude IDs"""
        mock_rows = [
            (r["id"], r["name"], r["resource_type"], r["tags"], r["url"],
             r["duration_or_quantity"], r["difficulty"], r["views"], r["completions"], r["rating"])
            for r in sample_resources
        ]
        mock_db.execute = AsyncMock(return_value=mock_rows)

        resources = await collaborative_recommender._get_all_resources(mock_db, exclude_ids=[1])

        mock_db.execute.assert_called_once()

    def test_apply_filters_empty(self, collaborative_recommender, sample_resources):
        """Test applying empty filters"""
        filtered = collaborative_recommender._apply_filters(sample_resources, {})
        assert filtered == sample_resources

    def test_apply_filters_difficulty(self, collaborative_recommender, sample_resources):
        """Test applying difficulty filter"""
        filtered = collaborative_recommender._apply_filters(sample_resources, {"difficulty": "easy"})
        assert len(filtered) == 1
        assert filtered[0]["difficulty"] == "easy"

    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_build_interaction_matrix(self, collaborative_recommender, mock_db):
        """Test building user-item interaction matrix"""
        mock_rows = [
            (1, 100),  # (resource_id, user_id)
            (1, 101),
            (2, 100),
        ]
        mock_db.execute = AsyncMock(return_value=mock_rows)

        matrix = await collaborative_recommender._build_interaction_matrix(mock_db, [{"id": 1}, {"id": 2}])

        assert isinstance(matrix, dict)
        assert 1 in matrix
        assert 2 in matrix
        assert len(matrix[1]) == 2  # Two users interacted with resource 1
        assert len(matrix[2]) == 1  # One user interacted with resource 2

    def test_compute_jaccard_similarity(self, collaborative_recommender):
        """Test Jaccard similarity computation"""
        set1 = {1, 2, 3, 4}
        set2 = {3, 4, 5, 6}

        similarity = collaborative_recommender._compute_jaccard_similarity(set1, set2)

        # Jaccard = |intersection|/|union| = 2/6
        assert abs(similarity - 2/6) < 1e-9

    def test_compute_jaccard_similarity_identical(self, collaborative_recommender):
        """Test Jaccard similarity with identical sets"""
        set1 = {1, 2, 3}
        set2 = {1, 2, 3}

        similarity = collaborative_recommender._compute_jaccard_similarity(set1, set2)

        assert similarity == 1.0

    def test_compute_jaccard_similarity_empty(self, collaborative_recommender):
        """Test Jaccard similarity with empty sets"""
        set1 = set()
        set2 = {1, 2, 3}

        similarity = collaborative_recommender._compute_jaccard_similarity(set1, set2)

        assert similarity == 0.0

    @pytest.mark.asyncio
    async def test_compute_collaborative_scores(self, collaborative_recommender):
        """Test computing collaborative scores"""
        liked_resource_ids = [1, 2]
        candidate_resources = [
            {"id": 3, "name": "Resource 3"},
            {"id": 4, "name": "Resource 4"},
        ]
        interaction_matrix = {
            1: {100, 101, 102},
            2: {100, 103},
            3: {100, 101, 104},
            4: {105, 106},
        }

        recommendations = await collaborative_recommender._compute_collaborative_scores(
            liked_resource_ids,
            candidate_resources,
            interaction_matrix
        )

        # Resource 3 shares users with both liked resources, should have higher score
        assert len(recommendations) > 0

        # Check that scores are present
        for rec in recommendations:
            assert "score" in rec
            assert "reason" in rec

    def test_train(self, collaborative_recommender):
        """Test training method"""
        collaborative_recommender._item_similarity_cache = {(1, 2): 0.5}

        collaborative_recommender.train()

        # Cache should be cleared
        assert len(collaborative_recommender._item_similarity_cache) == 0

    def test_get_item_similarity(self, collaborative_recommender):
        """Test getting item similarity from cache"""
        collaborative_recommender._item_similarity_cache = {(1, 2): 0.5, (2, 3): 0.8}

        similarity = collaborative_recommender.get_item_similarity(1, 2)

        assert similarity == 0.5

    def test_get_item_similarity_not_cached(self, collaborative_recommender):
        """Test getting item similarity when not in cache"""
        similarity = collaborative_recommender.get_item_similarity(1, 2)

        assert similarity == 0.0
