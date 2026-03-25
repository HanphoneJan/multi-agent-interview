"""Celery helper utilities for FastAPI integration"""
from typing import Optional
from celery import Celery
from celery.result import AsyncResult

from app.workers.celery_app import celery_app


class TaskManager:
    """Manager for handling Celery tasks"""

    def __init__(self, celery_app: Celery):
        self.celery = celery_app

    def submit_audio_task(
        self,
        audio_data_b64: str,
        session_id: str,
        user_id: int,
        audio_format: str = "wav"
    ) -> str:
        """
        Submit audio processing task

        Args:
            audio_data_b64: Base64 encoded audio data
            session_id: Interview session ID
            user_id: User ID
            audio_format: Audio format

        Returns:
            Task ID
        """
        task = self.celery.send_task(
            "app.workers.tasks.process_audio_task",
            args=[
                audio_data_b64,
                session_id,
                user_id,
                audio_format
            ],
            queue="audio"
        )
        return task.id

    def submit_video_task(
        self,
        frame_data_b64: str,
        session_id: str,
        user_id: int,
        frame_format: str = "jpeg",
        timestamp: Optional[float] = None
    ) -> str:
        """
        Submit video frame processing task

        Args:
            frame_data_b64: Base64 encoded frame data
            session_id: Interview session ID
            user_id: User ID
            frame_format: Image format
            timestamp: Frame timestamp

        Returns:
            Task ID
        """
        task = self.celery.send_task(
            "app.workers.tasks.process_video_task",
            args=[
                frame_data_b64,
                session_id,
                user_id,
                frame_format,
                timestamp
            ],
            queue="video"
        )
        return task.id

    def submit_report_task(
        self,
        session_id: str,
        user_id: int
    ) -> str:
        """
        Submit report generation task

        Args:
            session_id: Interview session ID
            user_id: User ID

        Returns:
            Task ID
        """
        task = self.celery.send_task(
            "app.workers.tasks.generate_report_task",
            args=[session_id, user_id],
            queue="reports"
        )
        return task.id

    def submit_notification_task(
        self,
        user_id: int,
        message: str,
        notification_type: str = "info"
    ) -> str:
        """
        Submit notification task

        Args:
            user_id: User ID
            message: Notification message
            notification_type: Type of notification

        Returns:
            Task ID
        """
        task = self.celery.send_task(
            "app.workers.tasks.send_notification_task",
            args=[user_id, message, notification_type],
            queue="notifications"
        )
        return task.id

    def get_task_result(self, task_id: str) -> Optional[AsyncResult]:
        """
        Get task result by task ID

        Args:
            task_id: Celery task ID

        Returns:
            AsyncResult object
        """
        return AsyncResult(task_id, app=self.celery)

    def get_task_status(self, task_id: str) -> str:
        """
        Get task status

        Args:
            task_id: Celery task ID

        Returns:
            Task status string (PENDING, STARTED, SUCCESS, FAILURE, etc.)
        """
        result = self.get_task_result(task_id)
        return result.status

    def is_task_ready(self, task_id: str) -> bool:
        """
        Check if task is ready (completed or failed)

        Args:
            task_id: Celery task ID

        Returns:
            True if task is ready
        """
        result = self.get_task_result(task_id)
        return result.ready()

    def is_task_successful(self, task_id: str) -> bool:
        """
        Check if task completed successfully

        Args:
            task_id: Celery task ID

        Returns:
            True if task succeeded
        """
        result = self.get_task_result(task_id)
        return result.successful()

    def get_task_result_value(self, task_id: str):
        """
        Get task result value

        Args:
            task_id: Celery task ID

        Returns:
            Task result value or None
        """
        result = self.get_task_result(task_id)
        if result.ready():
            return result.result
        return None

    def revoke_task(self, task_id: str, terminate: bool = False) -> bool:
        """
        Revoke (cancel) a task

        Args:
            task_id: Celery task ID
            terminate: Whether to terminate the task immediately

        Returns:
            True if task was revoked
        """
        self.celery.control.revoke(task_id, terminate=terminate)
        return True


# Global task manager instance
task_manager = TaskManager(celery_app)
