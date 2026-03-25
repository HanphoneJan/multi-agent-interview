"""Collaborative filtering recommender using item-based approach"""
from typing import Any

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.learning import resources, user_resource_interactions
from app.recommenders.base import BaseRecommender
from app.utils.log_helper import get_logger

logger = get_logger("recommenders.collaborative")


class CollaborativeFilteringRecommender(BaseRecommender):
    """
    Item-based collaborative filtering recommender.

    Recommends resources based on user interactions:
    - Find resources similar to user's liked resources
    - Uses Jaccard similarity for item-item similarity
    """

    # Interaction weights
    INTERACTION_WEIGHTS = {
        "view": 1.0,
        "complete": 3.0,
        "rate": 5.0,  # Assuming rate interaction has value as rating
    }

    def __init__(self):
        """Initialize collaborative filtering recommender"""
        super().__init__("collaborative_filtering")
        self._item_similarity_cache: dict[tuple[int, int], float] = {}

    def recommend(
        self,
        user_id: int,
        limit: int = 10,
        filters: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        """
        Generate collaborative filtering recommendations.

        Args:
            user_id: ID of the user
            limit: Maximum number of recommendations
            filters: Optional filters (difficulty, resource_type, etc.)

        Returns:
            List of recommendations with collaborative scores
        """
        raise NotImplementedError("Use async version: async_recommend")

    async def async_recommend(
        self,
        db: AsyncSession,
        user_id: int,
        limit: int = 10,
        filters: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        """
        Generate collaborative filtering recommendations.

        Args:
            db: Database session
            user_id: ID of the user
            limit: Maximum number of recommendations
            filters: Optional filters (difficulty, resource_type, etc.)

        Returns:
            List of recommendations with collaborative scores
        """
        filters = filters or {}

        # Step 1: Get user's positively interacted resources
        liked_resources = await self._get_user_liked_resources(db, user_id)
        if not liked_resources:
            logger.info(f"No positive interactions for user {user_id}, skipping collaborative filtering")
            return []

        liked_resource_ids = [r["resource_id"] for r in liked_resources]

        # Step 2: Get all resources (excluding user's liked ones)
        all_resources = await self._get_all_resources(db, exclude_ids=liked_resource_ids)
        if not all_resources:
            logger.info("No resources available for recommendation")
            return []

        # Step 3: Apply filters
        filtered_resources = self._apply_filters(all_resources, filters)
        if not filtered_resources:
            logger.info("No resources match the filters")
            return []

        # Step 4: Build user-item interaction matrix
        interaction_matrix = await self._build_interaction_matrix(db, all_resources)

        # Step 5: Compute item similarities and scores
        recommendations = await self._compute_collaborative_scores(
            liked_resource_ids,
            filtered_resources,
            interaction_matrix
        )

        # Step 6: Sort and return top-k
        recommendations.sort(key=lambda x: x["score"], reverse=True)
        return recommendations[:limit]

    async def _get_user_liked_resources(
        self,
        db: AsyncSession,
        user_id: int
    ) -> list[dict[str, Any]]:
        """
        Get user's positively interacted resources.

        Args:
            db: Database session
            user_id: User ID

        Returns:
            List of positively interacted resources with scores
        """
        query = (
            select(
                user_resource_interactions.c.resource_id,
                user_resource_interactions.c.interaction_type,
                user_resource_interactions.c.value
            )
            .where(user_resource_interactions.c.user_id == user_id)
        )

        result = await db.execute(query)

        # Score interactions based on type and value
        scored_resources = {}
        for row in result:
            resource_id = row[0]
            interaction_type = row[1]
            value = row[2]

            weight = self.INTERACTION_WEIGHTS.get(interaction_type, 0.1)
            score = weight * value

            if resource_id not in scored_resources:
                scored_resources[resource_id] = 0
            scored_resources[resource_id] += score

        # Filter out resources with low scores
        return [
            {"resource_id": rid, "score": score}
            for rid, score in scored_resources.items()
            if score > 0
        ]

    async def _get_all_resources(
        self,
        db: AsyncSession,
        exclude_ids: list[int] | None = None
    ) -> list[dict[str, Any]]:
        """
        Get all resources from database.

        Args:
            db: Database session
            exclude_ids: Resource IDs to exclude

        Returns:
            List of resource dicts
        """
        query = select(resources)

        if exclude_ids:
            query = query.where(resources.c.id.notin_(exclude_ids))

        result = await db.execute(query)
        return [
            {
                "id": row[0],
                "name": row[1],
                "resource_type": row[2],
                "tags": row[3],
                "url": row[4],
                "duration_or_quantity": row[5],
                "difficulty": row[6],
                "views": row[7],
                "completions": row[8],
                "rating": row[9],
            }
            for row in result
        ]

    def _apply_filters(
        self,
        resources: list[dict[str, Any]],
        filters: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """
        Apply filters to resources.

        Args:
            resources: List of resources
            filters: Filter dict

        Returns:
            Filtered list of resources
        """
        if not filters:
            return resources

        filtered = []

        for resource in resources:
            # Difficulty filter
            if "difficulty" in filters and filters["difficulty"]:
                if resource.get("difficulty") != filters["difficulty"]:
                    continue

            # Resource type filter
            if "resource_type" in filters and filters["resource_type"]:
                if resource.get("resource_type") != filters["resource_type"]:
                    continue

            filtered.append(resource)

        return filtered

    async def _build_interaction_matrix(
        self,
        db: AsyncSession,
        resources: list[dict[str, Any]]
    ) -> dict[int, set[int]]:
        """
        Build user-item interaction matrix.

        Returns:
            Dict mapping resource_id -> set of user_ids who interacted with it
        """
        resource_ids = [r["id"] for r in resources]

        if not resource_ids:
            return {}

        query = (
            select(
                user_resource_interactions.c.resource_id,
                user_resource_interactions.c.user_id
            )
            .where(user_resource_interactions.c.resource_id.in_(resource_ids))
        )

        result = await db.execute(query)

        # Build resource -> users mapping
        interaction_matrix: dict[int, set[int]] = {}
        for resource_id in resource_ids:
            interaction_matrix[resource_id] = set()

        for row in result:
            resource_id = row[0]
            user_id = row[1]
            if resource_id in interaction_matrix:
                interaction_matrix[resource_id].add(user_id)

        return interaction_matrix

    def _compute_jaccard_similarity(
        self,
        set1: set[int],
        set2: set[int]
    ) -> float:
        """
        Compute Jaccard similarity between two sets.

        Args:
            set1: First set
            set2: Second set

        Returns:
            Jaccard similarity score (0-1)
        """
        if not set1 or not set2:
            return 0.0

        intersection = len(set1 & set2)
        union = len(set1 | set2)

        return intersection / union if union > 0 else 0.0

    async def _compute_collaborative_scores(
        self,
        liked_resource_ids: list[int],
        candidate_resources: list[dict[str, Any]],
        interaction_matrix: dict[int, set[int]]
    ) -> list[dict[str, Any]]:
        """
        Compute collaborative filtering scores for candidate resources.

        Args:
            liked_resource_ids: User's liked resource IDs
            candidate_resources: List of candidate resources
            interaction_matrix: Resource -> users mapping

        Returns:
            List of resources with collaborative scores
        """
        recommendations = []

        for candidate in candidate_resources:
            candidate_id = candidate["id"]

            # Skip if candidate not in interaction matrix
            if candidate_id not in interaction_matrix:
                continue

            candidate_users = interaction_matrix[candidate_id]

            # Compute similarity with each liked resource
            total_similarity = 0.0
            count = 0

            for liked_id in liked_resource_ids:
                if liked_id in interaction_matrix:
                    liked_users = interaction_matrix[liked_id]
                    similarity = self._compute_jaccard_similarity(candidate_users, liked_users)

                    # Cache similarity
                    self._item_similarity_cache[(liked_id, candidate_id)] = similarity

                    total_similarity += similarity
                    count += 1

            # Average similarity as collaborative score
            score = total_similarity / count if count > 0 else 0.0

            candidate["score"] = score
            candidate["reason"] = f"用户行为相似度: {score:.2f}"

            if score > 0:
                recommendations.append(candidate)

        return recommendations

    def train(self):
        """
        Train the recommendation model.

        For collaborative filtering, this updates the similarity cache.
        In production, this should be called periodically to recompute similarities.
        """
        logger.info("Collaborative filtering: Clearing similarity cache")
        self._item_similarity_cache.clear()

    def get_item_similarity(
        self,
        item1_id: int,
        item2_id: int
    ) -> float:
        """
        Get similarity between two items.

        Args:
            item1_id: First item ID
            item2_id: Second item ID

        Returns:
            Jaccard similarity score
        """
        key = (item1_id, item2_id)
        return self._item_similarity_cache.get(key, 0.0)
