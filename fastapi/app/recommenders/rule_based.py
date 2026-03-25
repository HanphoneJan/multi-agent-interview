"""Rule-based recommender using SQLAlchemy Core"""
from typing import List, Dict, Any, Optional, Union
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import RECOMMENDATION_RULES
from app.recommenders.base import BaseRecommender
from app.models.learning import resources
from app.models.evaluation import overall_interview_evaluations


def _parse_tags(tags: Optional[Union[str, List[str]]]) -> List[str]:
    """Parse tags string to list (comma or space separated)"""
    if not tags:
        return []
    # If already a list, return as-is
    if isinstance(tags, list):
        return [str(t).strip() for t in tags if str(t).strip()]
    # If string, parse it
    return [t.strip() for t in tags.replace(",", " ").split() if t.strip()]


class RuleBasedRecommender(BaseRecommender):
    """Rule-based recommendation system"""

    def __init__(self):
        super().__init__("rule_based")
        self.rules = RECOMMENDATION_RULES

    async def recommend(
        self,
        user_id: int,
        limit: int = 10,
        filters: Dict[str, Any] | None = None,
        db: AsyncSession | None = None
    ) -> List[Dict[str, Any]]:
        """
        Generate recommendations based on user's evaluation scores.

        Args:
            user_id: ID of the user
            limit: Number of recommendations
            filters: Optional filters (difficulty, resource_type)
            db: Database session

        Returns:
            List of recommendations
        """
        if db is None:
            return []

        # Get user's latest evaluation
        query = (
            select(overall_interview_evaluations)
            .where(overall_interview_evaluations.c.user_id == user_id)
            .order_by(overall_interview_evaluations.c.created_at.desc())
            .limit(1)
        )
        result = await db.execute(query)
        row = result.first()

        if not row:
            return await self._get_popular_resources(db, limit, filters)

        # Build evaluation dict from row (Core returns Row)
        eval_row = row._mapping if hasattr(row, "_mapping") else row
        evaluation = {col.key: eval_row[col] for col in overall_interview_evaluations.c}

        # Identify weak areas
        weak_areas = []
        for dimension, rule in self.rules.items():
            try:
                val = evaluation.get(dimension, "0")
                score = float(val) if val else 0
                if score < rule["threshold"]:
                    weak_areas.append(dimension)
            except (ValueError, TypeError):
                continue

        if not weak_areas:
            return await self._get_popular_resources(db, limit, filters)

        # Collect tags from weak areas
        tags = []
        for area in weak_areas:
            tags.extend(self.rules[area]["tags"])

        # Query resources with matching tags
        query = select(resources)
        if filters and filters.get("difficulty"):
            query = query.where(resources.c.difficulty == filters["difficulty"])
        if filters and filters.get("resource_type"):
            query = query.where(resources.c.resource_type == filters["resource_type"])
        conditions = [resources.c.tags.like(f"%{tag}%") for tag in tags]
        query = query.where(or_(*conditions))
        query = query.order_by(resources.c.rating.desc()).limit(limit)

        result = await db.execute(query)
        rows = result.fetchall()

        recommendations = []
        for r in rows:
            rec = r._mapping if hasattr(r, "_mapping") else r
            resource_type = rec["resource_type"]
            rt_val = resource_type.value if hasattr(resource_type, "value") else str(resource_type)
            diff = rec.get("difficulty")
            diff_val = diff.value if diff and hasattr(diff, "value") else str(diff) if diff else None
            recommendations.append({
                "resource_id": rec["id"],
                "name": rec["name"],
                "resource_type": rt_val,
                "tags": _parse_tags(rec.get("tags", "")),
                "difficulty": diff_val,
                "url": rec["url"],
                "duration_or_quantity": rec.get("duration_or_quantity", ""),
                "score": float(rec.get("rating", 0)),
                "reason": f"Based on your {', '.join(weak_areas)} scores",
                "recommender": self.name,
            })

        return recommendations

    async def _get_popular_resources(
        self,
        db: AsyncSession,
        limit: int,
        filters: Dict[str, Any] | None = None
    ) -> List[Dict[str, Any]]:
        """Get popular resources as fallback"""
        query = select(resources)
        if filters and filters.get("difficulty"):
            query = query.where(resources.c.difficulty == filters["difficulty"])
        if filters and filters.get("resource_type"):
            query = query.where(resources.c.resource_type == filters["resource_type"])
        query = query.order_by(resources.c.views.desc(), resources.c.rating.desc()).limit(limit)

        result = await db.execute(query)
        rows = result.fetchall()

        recommendations = []
        for r in rows:
            rec = r._mapping if hasattr(r, "_mapping") else r
            resource_type = rec["resource_type"]
            rt_val = resource_type.value if hasattr(resource_type, "value") else str(resource_type)
            diff = rec.get("difficulty")
            diff_val = diff.value if diff and hasattr(diff, "value") else str(diff) if diff else None
            recommendations.append({
                "resource_id": rec["id"],
                "name": rec["name"],
                "resource_type": rt_val,
                "tags": _parse_tags(rec.get("tags", "")),
                "difficulty": diff_val,
                "url": rec["url"],
                "duration_or_quantity": rec.get("duration_or_quantity", ""),
                "score": float(rec.get("rating", 0)),
                "reason": "Popular resource",
                "recommender": self.name,
            })

        return recommendations

    def train(self):
        """Rule-based recommender doesn't require training"""
        pass
