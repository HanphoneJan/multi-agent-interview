"""Hybrid recommender combining multiple strategies"""
from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import HYBRID_WEIGHTS
from app.recommenders.base import BaseRecommender
from app.recommenders.rule_based import RuleBasedRecommender
from app.recommenders.content_based import ContentBasedRecommender
from app.recommenders.collaborative_filtering import CollaborativeFilteringRecommender


class HybridRecommender(BaseRecommender):
    """
    Hybrid recommender combining multiple recommenders.

    Combines results from:
    - Rule-based (50% weight): Ensures explainability and cold start support
    - Content-based (30% weight): Semantic similarity using embeddings
    - Collaborative filtering (20% weight): User behavior similarity
    """

    def __init__(
        self,
        rule_based: RuleBasedRecommender | None = None,
        content_based: ContentBasedRecommender | None = None,
        collaborative: CollaborativeFilteringRecommender | None = None,
    ):
        """
        Initialize hybrid recommender.

        Args:
            rule_based: Rule-based recommender instance
            content_based: Content-based recommender instance
            collaborative: Collaborative filtering recommender instance
        """
        super().__init__("hybrid")

        # Initialize component recommenders
        self.rule_based = rule_based or RuleBasedRecommender()
        self.content_based = content_based or ContentBasedRecommender()
        self.collaborative = collaborative or CollaborativeFilteringRecommender()
        self.weights = HYBRID_WEIGHTS

    async def recommend(
        self,
        user_id: int,
        limit: int = 10,
        filters: dict[str, Any] | None = None,
        db: AsyncSession | None = None
    ) -> list[dict[str, Any]]:
        """
        Generate hybrid recommendations.

        Combines results from multiple recommenders with weighted scores.
        """
        if db is None:
            return []

        filters = filters or {}

        # Multi-path recall
        all_recommendations = []

        # 1. Rule-based recommendations (50% weight)
        rule_recs = await self.rule_based.recommend(user_id, limit, filters, db)
        for rec in rule_recs:
            rec["weighted_score"] = rec["score"] * self.weights["rule_based"]
            rec["source"] = "rule_based"
            all_recommendations.append(rec)

        # 2. Content-based recommendations (30% weight)
        content_recs = await self.content_based.async_recommend(user_id, limit, filters, db)
        for rec in content_recs:
            rec["weighted_score"] = rec["score"] * self.weights["content_based"]
            rec["source"] = "content_based"
            all_recommendations.append(rec)

        # 3. Collaborative filtering recommendations (20% weight)
        collaborative_recs = await self.collaborative.async_recommend(user_id, limit, filters, db)
        for rec in collaborative_recs:
            rec["weighted_score"] = rec["score"] * self.weights["collaborative"]
            rec["source"] = "collaborative"
            all_recommendations.append(rec)

        # Aggregate scores by resource ID
        resource_scores: dict[int, dict[str, Any]] = {}
        for rec in all_recommendations:
            rid = rec["resource_id"]
            if rid in resource_scores:
                resource_scores[rid]["weighted_score"] += rec["weighted_score"]
                resource_scores[rid]["count"] += 1
                # Append reason if not already present
                if rec["reason"] not in resource_scores[rid]["reasons"]:
                    resource_scores[rid]["reasons"].append(rec["reason"])
                # Track sources
                if rec["source"] not in resource_scores[rid]["sources"]:
                    resource_scores[rid]["sources"].append(rec["source"])
            else:
                resource_scores[rid] = {
                    **rec,
                    "weighted_score": rec["weighted_score"],
                    "count": 1,
                    "reasons": [rec["reason"]],
                    "sources": [rec["source"]],
                }

        # Sort by weighted score (top 50)
        sorted_resources = sorted(
            resource_scores.values(),
            key=lambda x: x["weighted_score"],
            reverse=True
        )[:50]

        # Re-ranking with diversity
        diverse_recommendations = self._apply_diversity(sorted_resources)

        # Format final recommendations (top limit)
        recommendations = []
        for rec in diverse_recommendations[:limit]:
            rec_copy = rec.copy()
            rec_copy["score"] = rec_copy["weighted_score"]
            rec_copy["reason"] = "; ".join(rec_copy["reasons"])
            rec_copy["recommender"] = self.name
            # Remove internal fields
            rec_copy.pop("weighted_score", None)
            rec_copy.pop("count", None)
            rec_copy.pop("reasons", None)
            rec_copy.pop("source", None)
            rec_copy.pop("sources", None)
            recommendations.append(rec_copy)

        return recommendations

    def _apply_diversity(
        self,
        resources: list[dict[str, Any]],
        max_per_type: int = 2
    ) -> list[dict[str, Any]]:
        """
        Apply diversity to recommendations by limiting resources per type.

        Args:
            resources: List of resources sorted by score
            max_per_type: Maximum resources per resource type

        Returns:
            Diversified list of resources
        """
        seen_types: dict[str, int] = {}
        diverse_recommendations = []

        for rec in resources:
            resource_type = rec.get("resource_type", "unknown")
            type_count = seen_types.get(resource_type, 0)

            if type_count < max_per_type:
                diverse_recommendations.append(rec)
                seen_types[resource_type] = type_count + 1

        return diverse_recommendations

    def train(self):
        """Train component recommenders"""
        self.rule_based.train()
        self.content_based.train()
        self.collaborative.train()
