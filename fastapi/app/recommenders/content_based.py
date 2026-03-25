"""Content-based recommender using embeddings"""
from typing import Any

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.learning import resources, user_resource_interactions
from app.recommenders.base import BaseRecommender
from app.recommenders.embedding_service import EmbeddingService
from app.utils.log_helper import get_logger

logger = get_logger("recommenders.content_based")


class ContentBasedRecommender(BaseRecommender):
    """
    Content-based recommender using text embeddings.

    Recommends resources similar to user's past interactions based on:
    - Resource names, descriptions, and tags
    - Semantic similarity using sentence-transformers
    """

    def __init__(self, embedding_service: EmbeddingService | None = None):
        """
        Initialize content-based recommender.

        Args:
            embedding_service: EmbeddingService instance for computing similarities
        """
        super().__init__("content_based")
        self.embedding_service = embedding_service or EmbeddingService()
        self._resource_cache: dict[int, dict[str, Any]] = {}
        self._embedding_cache: dict[int, list[float]] = {}

    def recommend(
        self,
        user_id: int,
        limit: int = 10,
        filters: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        """
        Generate content-based recommendations for a user.

        Args:
            user_id: ID of the user
            limit: Maximum number of recommendations
            filters: Optional filters (difficulty, resource_type, etc.)

        Returns:
            List of recommendations with content scores
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
        Generate content-based recommendations for a user.

        Args:
            db: Database session
            user_id: ID of the user
            limit: Maximum number of recommendations
            filters: Optional filters (difficulty, resource_type, etc.)

        Returns:
            List of recommendations with content scores
        """
        filters = filters or {}

        # Step 1: Get user's past interactions
        user_interactions = await self._get_user_interactions(db, user_id)
        if not user_interactions:
            logger.info(f"No interactions found for user {user_id}, skipping content-based")
            return []

        # Step 2: Get resources the user has interacted with
        interacted_resource_ids = [r["resource_id"] for r in user_interactions]

        # Step 3: Build user interest vector from interacted resources
        user_interest_embedding = await self._build_user_interest_embedding(db, interacted_resource_ids)
        if user_interest_embedding is None:
            logger.warning(f"Could not build user interest embedding for user {user_id}")
            return []

        # Step 4: Get all resources (excluding interacted ones)
        all_resources = await self._get_all_resources(db, exclude_ids=interacted_resource_ids)
        if not all_resources:
            logger.info("No resources available for recommendation")
            return []

        # Step 5: Apply filters
        filtered_resources = self._apply_filters(all_resources, filters)
        if not filtered_resources:
            logger.info("No resources match the filters")
            return []

        # Step 6: Compute similarity scores
        recommendations = await self._compute_similarities(
            user_interest_embedding,
            filtered_resources
        )

        # Step 7: Sort and return top-k
        recommendations.sort(key=lambda x: x["score"], reverse=True)
        return recommendations[:limit]

    async def _get_user_interactions(
        self,
        db: AsyncSession,
        user_id: int
    ) -> list[dict[str, Any]]:
        """
        Get user's resource interaction history.

        Args:
            db: Database session
            user_id: User ID

        Returns:
            List of interaction records
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
        return [{"resource_id": row[0], "type": row[1], "value": row[2]} for row in result]

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

    async def _build_user_interest_embedding(
        self,
        db: AsyncSession,
        resource_ids: list[int]
    ) -> list[float] | None:
        """
        Build user interest vector from interacted resources.

        Args:
            db: Database session
            resource_ids: List of resource IDs the user interacted with

        Returns:
            Average embedding vector of user's interests
        """
        if not resource_ids:
            return None

        # Get resource details
        query = select(resources).where(resources.c.id.in_(resource_ids))
        result = await db.execute(query)

        resource_texts = []
        for row in result:
            resource = {
                "name": row[1],
                "tags": row[3],
                "difficulty": row[6],
                "resource_type": row[2],
            }
            text = self.embedding_service.build_resource_text(resource)
            resource_texts.append(text)

        if not resource_texts:
            return None

        # Compute embeddings for all resources
        embeddings = self.embedding_service.get_embeddings_batch(resource_texts)

        # Average the embeddings
        import numpy as np
        avg_embedding = np.mean(embeddings, axis=0)
        return avg_embedding.tolist()

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

    async def _compute_similarities(
        self,
        query_embedding: list[float],
        resources: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """
        Compute similarity scores between query and resources.

        Args:
            query_embedding: Query embedding vector
            resources: List of resource dicts

        Returns:
            List of resources with similarity scores
        """
        # Build text and compute embeddings for all resources
        resource_texts = [
            self.embedding_service.build_resource_text(r)
            for r in resources
        ]

        # Compute similarities in batch
        similarities = self.embedding_service.compute_similarities(
            query_embedding,
            self.embedding_service.get_embeddings_batch(resource_texts)
        )

        # Add scores to resources
        for i, resource in enumerate(resources):
            resource["score"] = similarities[i]
            resource["reason"] = f"内容相似度: {similarities[i]:.2f}"

        return resources

    def train(self):
        """
        Train the recommendation model.

        For content-based recommendation, this is mainly a no-op
        since we use pre-trained embeddings.
        """
        logger.info("Content-based recommender: Training not needed (using pre-trained embeddings)")

    def get_resource_embedding(self, resource: dict[str, Any]) -> list[float]:
        """
        Get or compute embedding for a resource.

        Args:
            resource: Resource dict

        Returns:
            Embedding vector
        """
        resource_id = resource.get("id")

        # Check cache
        if resource_id in self._embedding_cache:
            return self._embedding_cache[resource_id]

        # Compute embedding
        text = self.embedding_service.build_resource_text(resource)
        embedding = self.embedding_service.get_embedding(text)

        # Cache result
        if resource_id:
            self._resource_cache[resource_id] = resource
            self._embedding_cache[resource_id] = embedding

        return embedding
