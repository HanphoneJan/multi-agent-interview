"""Recommendation related Celery tasks"""
from app.tasks.celery_app import celery_app
from app.utils.log_helper import get_logger

logger = get_logger("tasks.recommendation")


@celery_app.task(bind=True, name="train_recommendation_model")
def train_recommendation_model_task(self, model_type: str = "all"):
    """
    Train recommendation models (clear caches for rebuild on next request).

    Clears in-memory similarity/embedding caches so the next API request
    will recompute. For distributed deployments, consider Redis-backed cache.

    Args:
        model_type: 'all' | 'collaborative' | 'content' | 'hybrid'

    Returns:
        Training status
    """
    try:
        if model_type in ("all", "hybrid"):
            from app.recommenders.hybrid import HybridRecommender
            rec = HybridRecommender()
            rec.train()
            logger.info("train_recommendation_model: hybrid (all) cache cleared")
        elif model_type == "collaborative":
            from app.recommenders.collaborative_filtering import CollaborativeFilteringRecommender
            CollaborativeFilteringRecommender().train()
            logger.info("train_recommendation_model: collaborative cache cleared")
        elif model_type == "content":
            from app.recommenders.content_based import ContentBasedRecommender
            ContentBasedRecommender().train()
            logger.info("train_recommendation_model: content cache cleared")
        else:
            return {"status": "skipped", "model_type": model_type, "error": "unknown model_type"}

        return {
            "status": "completed",
            "model_type": model_type,
            "metrics": {"cache_cleared": True},
        }
    except Exception as e:
        logger.error(f"train_recommendation_model failed: {e}")
        return {"status": "error", "model_type": model_type, "error": str(e)}


@celery_app.task(bind=True, name="update_user_recommendations")
def update_user_recommendations_task(self, user_id: int):
    """
    Update recommendations for a specific user.

    Args:
        user_id: ID of the user

    Returns:
        Updated recommendations
    """
    # TODO: Implement recommendation update logic
    return {
        "user_id": user_id,
        "recommendations": [
            {"resource_id": 1, "score": 0.9},
            {"resource_id": 2, "score": 0.85},
        ]
    }
