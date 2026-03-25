"""Celery worker application configuration"""
import os
from celery import Celery
from app.config import get_settings

settings = get_settings()

# Redis URL for Celery broker and backend
# Use REDIS_URL for both broker and backend
CELERY_BROKER_URL = settings.REDIS_URL
CELERY_RESULT_BACKEND = settings.REDIS_URL

# Create Celery app
celery_app = Celery(
    "interview_agent",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
    include=[
        "app.workers.tasks",
    ]
)

# Configure Celery
celery_app.conf.update(
    # Task settings
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes

    # Worker settings
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=50,

    # Result backend settings
    result_expires=3600,  # 1 hour
    result_extended=True,

    # Task routing (optional)
    task_routes={
        "app.workers.tasks.process_audio_task": {"queue": "audio"},
        "app.workers.tasks.process_video_task": {"queue": "video"},
        "app.workers.tasks.generate_report_task": {"queue": "reports"},
        "app.workers.tasks.send_notification_task": {"queue": "notifications"},
    },

    # Task execution settings
    task_acks_late=True,
    worker_disable_rate_limits=False,

    # Retry settings
    task_default_retry_delay=60,
    task_max_retries=3,

    # Task compression
    task_compression="gzip",
    result_compression="gzip",
)

# Optional: Set up beat scheduler for periodic tasks
celery_app.conf.beat_schedule = {
    # Clean up old temporary files every hour
    "cleanup-temp-files": {
        "task": "app.workers.tasks.cleanup_temp_files_task",
        "schedule": 3600.0,  # 1 hour
    },
    # Process pending evaluations every 5 minutes
    "process-pending-evaluations": {
        "task": "app.workers.tasks.process_pending_evaluations_task",
        "schedule": 300.0,  # 5 minutes
    },
}

if __name__ == "__main__":
    celery_app.start()
