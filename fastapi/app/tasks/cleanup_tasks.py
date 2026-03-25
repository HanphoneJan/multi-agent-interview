"""Cleanup related Celery tasks"""
import asyncio
from datetime import datetime, timezone, timedelta

from redis import Redis
from sqlalchemy import update
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

from app.tasks.celery_app import celery_app
from app.config import get_settings
from app.models.interview import interview_sessions
from app.core.constants import (
    InterviewSessionStatus,
    SESSION_EXPIRE_MINUTES,
    CELERY_BEAT_SCHEDULE,
)
from app.utils.log_helper import get_logger

logger = get_logger("tasks.cleanup")
settings = get_settings()


async def _mark_expired_sessions(engine) -> int:
    """Mark sessions paused > 30 min as expired. Returns count."""
    async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    threshold = datetime.now(timezone.utc) - timedelta(minutes=SESSION_EXPIRE_MINUTES)

    async with async_session() as session:
        stmt = (
            update(interview_sessions)
            .where(
                interview_sessions.c.status == InterviewSessionStatus.PAUSED.value,
                interview_sessions.c.paused_at < threshold,
            )
            .values(status=InterviewSessionStatus.EXPIRED.value)
        )
        result = await session.execute(stmt)
        await session.commit()
        return result.rowcount or 0


@celery_app.task(bind=True, name="cleanup_expired_sessions")
def cleanup_expired_sessions_task(self):
    """
    Clean up expired interview sessions.
    Sessions paused for more than 30 minutes are marked as expired.

    Returns:
        Number of sessions marked as expired
    """
    try:
        from app.database import engine
        count = asyncio.run(_mark_expired_sessions(engine))
        logger.info(f"cleanup_expired_sessions: marked {count} sessions as expired")
        return {"cleaned_sessions": count, "status": "success"}
    except Exception as e:
        logger.error(f"cleanup_expired_sessions failed: {e}")
        return {"cleaned_sessions": 0, "status": "error", "error": str(e)}


@celery_app.task(bind=True, name="cleanup_temporary_files")
def cleanup_temporary_files_task(self):
    """
    Clean up temporary files.
    Placeholder for future OSS/temp file cleanup.

    Returns:
        Number of files cleaned up
    """
    # TODO: Implement OSS temp file cleanup when storage path is defined
    logger.info("cleanup_temporary_files: no temp path configured, skipped")
    return {"cleaned_files": 0, "status": "skipped"}


def _run_redis_cache_cleanup() -> dict:
    """
    Run Redis cache cleanup.
    Redis automatically removes keys with TTL; this verifies connection health.
    """
    try:
        client = Redis.from_url(settings.REDIS_URL, decode_responses=True)
        client.ping()
        client.close()
        return {"cleaned_entries": 0, "status": "success", "note": "Redis TTL handles expiry"}
    except Exception as e:
        logger.error(f"cleanup_expired_cache failed: {e}")
        return {"cleaned_entries": 0, "status": "error", "error": str(e)}


@celery_app.task(bind=True, name="cleanup_expired_cache")
def cleanup_expired_cache_task(self):
    """
    Verify Redis and optionally clean expired cache.
    Redis automatically removes keys with TTL on access.

    Returns:
        Cleanup result
    """
    return _run_redis_cache_cleanup()


# Schedule periodic tasks
celery_app.conf.beat_schedule = {
    'cleanup-expired-sessions': {
        'task': 'cleanup_expired_sessions',
        'schedule': CELERY_BEAT_SCHEDULE["cleanup_sessions_seconds"],
    },
    'cleanup-temporary-files': {
        'task': 'cleanup_temporary_files',
        'schedule': CELERY_BEAT_SCHEDULE["cleanup_files_seconds"],
    },
    'cleanup-expired-cache': {
        'task': 'cleanup_expired_cache',
        'schedule': CELERY_BEAT_SCHEDULE["cleanup_cache_seconds"],
    },
    'train-recommendation-models': {
        'task': 'train_recommendation_model',
        'schedule': CELERY_BEAT_SCHEDULE["train_model_seconds"],
    },
}
