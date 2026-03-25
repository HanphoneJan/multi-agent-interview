"""Recommendation service for interview resources"""
from typing import List, Dict, Any, Optional
from collections import defaultdict
import numpy as np

from sqlalchemy import select, func, desc, and_, or_, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import (
    RECOMMENDATION_RULES,
    HYBRID_WEIGHTS,
    RECOMMENDATION_RECALL_LIMITS,
    BALANCED_RESOURCE_SCORE,
)
from app.models.learning import (
    resources, user_resource_interactions
)
from app.models.evaluation import overall_interview_evaluations
from app.utils.log_helper import get_logger

logger = get_logger("services.recommendation")


def _parse_tags(tags: Optional[str] | List[str]) -> List[str]:
    """Parse tags string to list (comma or space separated)"""
    if not tags:
        return []
    # If already a list, return as-is
    if isinstance(tags, list):
        return [str(t).strip() for t in tags if str(t).strip()]
    # If string, parse it
    return [t.strip() for t in tags.replace(",", " ").split() if t.strip()]


class RecommendationService:
    """Service for recommending learning resources"""

    RULES = RECOMMENDATION_RULES
    HYBRID_WEIGHTS = HYBRID_WEIGHTS

    def __init__(self):
        self._embedding_model = None  # sentence-transformers model
        self._resource_embeddings = None  # Cached embeddings
        self._resource_similarity_matrix = None  # Collaborative filtering

    async def get_recommendations_for_user(
        self,
        db: AsyncSession,
        user_id: int,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get personalized recommendations for a user

        Args:
            db: Database session
            user_id: User ID
            limit: Number of recommendations to return

        Returns:
            List of recommended resources with scores
        """
        try:
            # Get user's latest evaluation scores
            evaluation = await self._get_latest_evaluation(db, user_id)

            # Get user's interaction history
            interactions = await self._get_user_interactions(db, user_id)

            # Rule-based recommendations
            rule_recs = await self._rule_based_recommendations(
                db, user_id, evaluation, interactions,
                limit=RECOMMENDATION_RECALL_LIMITS["rule_based"]
            )

            # Content-based recommendations
            content_recs = await self._content_based_recommendations(
                db, user_id, interactions,
                limit=RECOMMENDATION_RECALL_LIMITS["content_based"]
            )

            # Collaborative filtering recommendations
            collab_recs = await self._collaborative_filtering_recommendations(
                db, user_id, interactions,
                limit=RECOMMENDATION_RECALL_LIMITS["collaborative"]
            )

            # Merge and rank recommendations
            merged = self._merge_recommendations(
                rule_recs, content_recs, collab_recs
            )

            # Filter out already viewed resources
            viewed_resource_ids = {i.resource_id for i in interactions}
            merged = [r for r in merged if r["id"] not in viewed_resource_ids]

            # Diversity reordering
            merged = self._diversify_recommendations(merged)

            return merged[:limit]

        except Exception as e:
            logger.error(f"Error getting recommendations for user {user_id}: {e}")
            # Fallback: return popular resources
            return await self._get_popular_resources(db, limit)

    async def _get_latest_evaluation(
        self,
        db: AsyncSession,
        user_id: int
    ) -> Optional[Dict[str, Any]]:
        """Get user's latest evaluation scores"""
        result = await db.execute(
            select(overall_interview_evaluations)
            .where(overall_interview_evaluations.c.user_id == user_id)
            .order_by(desc(overall_interview_evaluations.c.created_at))
            .limit(1)
        )
        row = result.first()

        if not row:
            return None

        return {
            "professional_knowledge": row.professional_knowledge_score,
            "logical_thinking": row.logical_thinking_score,
            "language_expression": row.language_expression_score,
            "technical_communication": row.technical_communication_score,
            "problem_solving": row.problem_solving_score,
        }

    async def _get_user_interactions(
        self,
        db: AsyncSession,
        user_id: int
    ) -> List[Any]:
        """Get user's resource interaction history"""
        result = await db.execute(
            select(user_resource_interactions)
            .where(user_resource_interactions.c.user_id == user_id)
            .order_by(desc(user_resource_interactions.c.created_at))
        )
        return result.all()

    async def _rule_based_recommendations(
        self,
        db: AsyncSession,
        user_id: int,
        evaluation: Optional[Dict[str, Any]],
        interactions: List[Any],
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Rule-based recommendations based on evaluation scores"""
        if not evaluation:
            # No evaluation data, return popular resources
            return await self._get_popular_resources(db, limit)

        recommendations = []

        # Find weak dimensions
        weak_dimensions = [
            dim for dim, threshold in {
                "professional_knowledge": self.RULES["professional_knowledge"]["threshold"],
                "logical_thinking": self.RULES["logical_thinking"]["threshold"],
                "language_expression": self.RULES["language_expression"]["threshold"],
                "technical_communication": self.RULES["technical_communication"]["threshold"],
                "problem_solving": self.RULES["problem_solving"]["threshold"],
            }.items()
            if evaluation.get(dim, 100) < threshold
        ]

        if not weak_dimensions:
            # All scores good, return balanced recommendations
            return await self._get_balanced_resources(db, limit)

        # For each weak dimension, get matching resources
        for dim in weak_dimensions:
            rule = self.RULES.get(dim)
            if not rule:
                continue

            # Query resources with matching tags
            result = await db.execute(
                select(resources)
                .where(resources.c.id.notin_([i.resource_id for i in interactions]))
                .limit(limit // len(weak_dimensions))
            )

            for row in result:
                tags = _parse_tags(row.tags)
                # Calculate tag match score
                match_score = sum(1 for tag in rule["tags"] if tag in tags)
                if match_score > 0:
                    recommendations.append({
                        "id": row.id,
                        "name": row.name,
                        "tags": tags,
                        "difficulty": row.difficulty,
                        "resource_type": row.resource_type,
                        "duration_or_quantity": row.duration_or_quantity,
                        "url": row.url,
                        "rule_score": match_score / len(rule["tags"]),
                        "content_score": 0,
                        "collab_score": 0,
                    })

        # Sort by rule score
        recommendations.sort(key=lambda x: x["rule_score"], reverse=True)

        return recommendations[:limit]

    async def _content_based_recommendations(
        self,
        db: AsyncSession,
        user_id: int,
        interactions: List[Any],
        limit: int = 30
    ) -> List[Dict[str, Any]]:
        """Content-based recommendations using similarity"""
        if not interactions:
            return await self._get_popular_resources(db, limit)

        # Get user's viewed resources
        viewed_ids = [i.resource_id for i in interactions[:20]]  # Last 20 interactions

        if not viewed_ids:
            return await self._get_popular_resources(db, limit)

        # Simple content-based: recommend similar resources by tags and type
        # In production, use sentence-transformers for semantic similarity
        result = await db.execute(
            select(resources)
            .where(
                and_(
                    resources.c.id.notin_(viewed_ids),
                    resources.c.resource_type.in_(
                        [r.resource_type for r in interactions[:10]]
                    )
                )
            )
            .order_by(desc(resources.c.views))
            .limit(limit * 2)  # Get more for re-ranking
        )

        recommendations = []
        for row in result:
            # Calculate tag similarity with viewed resources
            similarity = self._calculate_tag_similarity(
                row.tags,
                [i.tags for i in interactions[:10] if i.tags]
            )

            recommendations.append({
                "id": row.id,
                "name": row.name,
                "tags": _parse_tags(row.tags),
                "difficulty": row.difficulty,
                "resource_type": row.resource_type,
                "duration_or_quantity": row.duration_or_quantity,
                "url": row.url,
                "rule_score": 0,
                "content_score": similarity,
                "collab_score": 0,
            })

        # Sort by content similarity
        recommendations.sort(key=lambda x: x["content_score"], reverse=True)

        return recommendations[:limit]

    def _calculate_tag_similarity(
        self,
        tags1: Optional[List[str]],
        tags_list: List[Optional[List[str]]]
    ) -> float:
        """Calculate tag similarity using Jaccard index"""
        if not tags1:
            return 0.0

        set1 = set(tags1)
        similarities = []

        for tags2 in tags_list:
            if not tags2:
                continue
            set2 = set(tags2)
            intersection = len(set1 & set2)
            union = len(set1 | set2)
            if union > 0:
                similarities.append(intersection / union)

        return max(similarities) if similarities else 0.0

    async def _collaborative_filtering_recommendations(
        self,
        db: AsyncSession,
        user_id: int,
        interactions: List[Any],
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Collaborative filtering recommendations"""
        if not interactions:
            return []

        # Get similar users based on resource interactions
        viewed_ids = [i.resource_id for i in interactions]

        # Find users who also viewed these resources
        result = await db.execute(
            select(
                user_resource_interactions.c.user_id,
                func.count(user_resource_interactions.c.resource_id).label('count')
            )
            .where(
                and_(
                    user_resource_interactions.c.user_id != user_id,
                    user_resource_interactions.c.resource_id.in_(viewed_ids)
                )
            )
            .group_by(user_resource_interactions.c.user_id)
            .order_by(desc('count'))
            .limit(20)
        )

        similar_user_ids = [row.user_id for row in result]

        if not similar_user_ids:
            return []

        # Get resources viewed by similar users
        result = await db.execute(
            select(resources)
            .join(
                user_resource_interactions,
                resources.c.id == user_resource_interactions.c.resource_id
            )
            .where(
                and_(
                    user_resource_interactions.c.user_id.in_(similar_user_ids),
                    resources.c.id.notin_(viewed_ids)
                )
            )
            .group_by(resources.c.id)
            .order_by(desc(func.count(user_resource_interactions.c.user_id)))
            .limit(limit * 2)
        )

        recommendations = []
        for row in result:
            recommendations.append({
                "id": row.id,
                "name": row.name,
                "tags": _parse_tags(row.tags),
                "difficulty": row.difficulty,
                "resource_type": row.resource_type,
                "duration_or_quantity": row.duration_or_quantity,
                "url": row.url,
                "rule_score": 0,
                "content_score": 0,
                "collab_score": 1.0,  # Normalized score
            })

        return recommendations[:limit]

    def _merge_recommendations(
        self,
        rule_recs: List[Dict[str, Any]],
        content_recs: List[Dict[str, Any]],
        collab_recs: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Merge recommendations from different sources"""
        # Build index by resource id
        merged_index = {}

        for rec in rule_recs:
            merged_index[rec["id"]] = rec.copy()

        # Add content-based scores
        for rec in content_recs:
            if rec["id"] in merged_index:
                merged_index[rec["id"]]["content_score"] = rec["content_score"]
            else:
                merged_index[rec["id"]] = rec.copy()

        # Add collaborative scores
        for rec in collab_recs:
            if rec["id"] in merged_index:
                merged_index[rec["id"]]["collab_score"] = rec["collab_score"]
            else:
                merged_index[rec["id"]] = rec.copy()

        # Calculate weighted score
        weights = self.HYBRID_WEIGHTS
        for rec_id, rec in merged_index.items():
            rec["final_score"] = (
                weights["rule_based"] * rec["rule_score"] +
                weights["content_based"] * rec["content_score"] +
                weights["collaborative"] * rec["collab_score"]
            )

        # Sort by final score
        merged = list(merged_index.values())
        merged.sort(key=lambda x: x["final_score"], reverse=True)

        return merged

    def _diversify_recommendations(
        self,
        recommendations: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Diversify recommendations by resource type"""
        # Group by resource type
        type_groups = defaultdict(list)
        for rec in recommendations:
            type_groups[rec.get("resource_type", "unknown")].append(rec)

        # Reorder to ensure diversity
        diversified = []
        max_per_type = max(2, len(recommendations) // 5)  # Max 20% per type

        while len(diversified) < len(recommendations):
            added = False
            for rec_type in type_groups.keys():
                if len(diversified) >= len(recommendations):
                    break
                if len(type_groups[rec_type]) > 0 and \
                   sum(1 for r in diversified if r.get("resource_type") == rec_type) < max_per_type:
                    diversified.append(type_groups[rec_type].pop(0))
                    added = True

            if not added:
                # Add remaining items
                for group in type_groups.values():
                    if group:
                        diversified.extend(group)
                        break

        return diversified

    async def _get_popular_resources(
        self,
        db: AsyncSession,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get popular resources as fallback"""
        result = await db.execute(
            select(resources)
            .order_by(desc(resources.c.views))
            .limit(limit)
        )

        recommendations = []
        for row in result:
            recommendations.append({
                "id": row.id,
                "name": row.name,
                "tags": _parse_tags(row.tags),
                "difficulty": row.difficulty,
                "resource_type": row.resource_type,
                "duration_or_quantity": row.duration_or_quantity,
                "url": row.url,
                "rule_score": 0,
                "content_score": 0,
                "collab_score": 0,
                "final_score": 0,
            })

        return recommendations

    async def _get_balanced_resources(
        self,
        db: AsyncSession,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get balanced resources (mix of different types)"""
        result = await db.execute(
            select(resources)
            .order_by(desc(resources.c.rating))
            .limit(limit)
        )

        recommendations = []
        for row in result:
            recommendations.append({
                "id": row.id,
                "name": row.name,
                "tags": _parse_tags(row.tags),
                "difficulty": row.difficulty,
                "resource_type": row.resource_type,
                "duration_or_quantity": row.duration_or_quantity,
                "url": row.url,
                "rule_score": BALANCED_RESOURCE_SCORE,
                "content_score": BALANCED_RESOURCE_SCORE,
                "collab_score": BALANCED_RESOURCE_SCORE,
                "final_score": BALANCED_RESOURCE_SCORE,
            })

        return recommendations

    async def record_interaction(
        self,
        db: AsyncSession,
        user_id: int,
        resource_id: int,
        interaction_type: str,
        value: Optional[float] = None
    ):
        """
        Record user-resource interaction

        Args:
            db: Database session
            user_id: User ID
            resource_id: Resource ID
            interaction_type: view/complete/rate
            value: Interaction value (duration/completion rate/rating)
        """
        from sqlalchemy import insert
        from datetime import datetime, timezone

        await db.execute(
            insert(user_resource_interactions).values(
                user_id=user_id,
                resource_id=resource_id,
                interaction_type=interaction_type,
                value=value or 1.0,
                created_at=datetime.now(timezone.utc)
            )
        )

        # Update resource stats
        if interaction_type == "view":
            await db.execute(
                resources.update()
                .where(resources.c.id == resource_id)
                .values(views=resources.c.views + 1)
            )
        elif interaction_type == "complete":
            await db.execute(
                resources.update()
                .where(resources.c.id == resource_id)
                .values(completions=resources.c.completions + 1)
            )
        elif interaction_type == "rate":
            # Recalculate average rating
            pass  # Need more complex logic for averaging

        await db.commit()


# Global recommendation service instance
recommendation_service = RecommendationService()
