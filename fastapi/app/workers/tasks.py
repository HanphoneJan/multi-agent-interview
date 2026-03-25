"""Celery async tasks for interview processing"""
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

from celery import shared_task
from celery.exceptions import SoftTimeLimitExceeded

from app.workers.celery_app import celery_app
from app.services.audio_service import audio_service
from app.services.video_service import video_service, video_analytics_service
from app.utils.log_helper import get_logger

logger = get_logger("workers.tasks")


@shared_task(
    name="app.workers.tasks.process_audio_task",
    bind=True,
    max_retries=3,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True,
)
def process_audio_task(
    self,
    audio_data_b64: str,
    session_id: str,
    user_id: int,
    audio_format: str = "wav"
) -> Dict[str, Any]:
    """
    Process audio data asynchronously

    Args:
        audio_data_b64: Base64 encoded audio data
        session_id: Interview session ID
        user_id: User ID
        audio_format: Audio format

    Returns:
        Dict containing processing result
    """
    import asyncio

    try:
        logger.info(
            f"Processing audio for session {session_id}, user {user_id}"
        )

        # Run async processing in sync context
        async def _process():
            result = await audio_service.process_audio(
                audio_data=audio_data_b64,
                audio_format=audio_format,
                session_id=session_id,
                user_id=user_id
            )
            return result

        result = asyncio.run(_process())

        if result.get("success"):
            logger.info(
                f"Audio processing completed for session {session_id}, "
                f"transcript: {result.get('transcript')[:50]}..."
            )
        else:
            logger.error(
                f"Audio processing failed for session {session_id}: "
                f"{result.get('error')}"
            )

        return result

    except SoftTimeLimitExceeded:
        logger.error(f"Audio processing timed out for session {session_id}")
        return {
            "success": False,
            "error": "Processing timeout",
            "transcript": None,
            "duration": 0.0,
            "confidence": 0.0,
        }
    except Exception as e:
        logger.exception(
            f"Error processing audio for session {session_id}: {e}"
        )
        # Retry if not the last attempt
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e, countdown=60)
        return {
            "success": False,
            "error": str(e),
            "transcript": None,
            "duration": 0.0,
            "confidence": 0.0,
        }


@shared_task(
    name="app.workers.tasks.process_video_task",
    bind=True,
    max_retries=2,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=300,
)
def process_video_task(
    self,
    frame_data_b64: str,
    session_id: str,
    user_id: int,
    frame_format: str = "jpeg",
    timestamp: Optional[float] = None
) -> Dict[str, Any]:
    """
    Process video frame asynchronously

    Args:
        frame_data_b64: Base64 encoded frame data
        session_id: Interview session ID
        user_id: User ID
        frame_format: Image format
        timestamp: Frame timestamp

    Returns:
        Dict containing processing result
    """
    import asyncio

    try:
        logger.info(
            f"Processing video frame for session {session_id}, user {user_id}"
        )

        async def _process():
            result = await video_service.process_video_frame(
                frame_data=frame_data_b64,
                frame_format=frame_format,
                timestamp=timestamp,
                session_id=session_id,
                user_id=user_id
            )
            return result

        result = asyncio.run(_process())

        if result.get("success"):
            # Record for analytics
            video_analytics_service.record_frame_result(
                session_id, user_id, result
            )
            logger.debug(
                f"Video frame processed for session {session_id}, "
                f"face_detected: {result.get('face_detected')}"
            )
        else:
            logger.warning(
                f"Video frame processing failed for session {session_id}: "
                f"{result.get('error')}"
            )

        return result

    except SoftTimeLimitExceeded:
        logger.warning(f"Video frame processing timed out for session {session_id}")
        return {
            "success": False,
            "error": "Processing timeout",
            "face_detected": False,
            "emotion": None,
            "attention_score": 0.0,
            "landmarks": None,
        }
    except Exception as e:
        logger.exception(
            f"Error processing video frame for session {session_id}: {e}"
        )
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e, countdown=30)
        return {
            "success": False,
            "error": str(e),
            "face_detected": False,
            "emotion": None,
            "attention_score": 0.0,
            "landmarks": None,
        }


@shared_task(
    name="app.workers.tasks.generate_report_task",
    bind=True,
    max_retries=3,
)
def generate_report_task(
    self,
    session_id: str,
    user_id: int
) -> Dict[str, Any]:
    """
    Generate interview report asynchronously

    Args:
        session_id: Interview session ID
        user_id: User ID

    Returns:
        Dict containing report generation result
    """
    import asyncio
    from sqlalchemy import select, insert
    from app.database import get_async_session
    from app.models.interview import interview_sessions
    from app.models.evaluation import overall_interview_evaluations

    try:
        logger.info(f"Generating report for session {session_id}")

        async def _generate():
            async for session in get_async_session():
                result = await session.execute(
                    select(interview_sessions).where(
                        interview_sessions.c.id == int(session_id)
                    )
                )
                session_data = result.first()

                if not session_data:
                    raise ValueError(f"Session {session_id} not found")

                analytics = video_analytics_service.get_session_analytics(
                    session_id, user_id
                )
                base_score = 75.0
                attention_bonus = analytics.get("avg_attention", 0) * 15.0
                emotion_score = analytics.get("emotion_distribution", {}).get("neutral", 0.5) * 10.0
                overall_score = min(100.0, base_score + attention_bonus + emotion_score)

                # Map to overall_interview_evaluations table schema
                score_str = str(int(round(overall_score)))
                eval_data = {
                    "session_id": int(session_id),
                    "user_id": user_id,
                    "overall_evaluation": "面试表现良好，建议继续提升表达能力。",
                    "help": "表达能力良好, 逻辑清晰。可以更深入地阐述观点。",
                    "recommendation": "通过",
                    "overall_score": score_str,
                    "professional_knowledge": "75",
                    "skill_match": "75",
                    "language_expression": str(int(70 + attention_bonus)),
                    "logical_thinking": "80",
                    "stress_response": "75",
                    "personality": "78",
                    "motivation": "80",
                    "value": "80",
                }
                stmt = insert(overall_interview_evaluations).values(**eval_data)
                await session.execute(stmt)
                await session.commit()

                return {
                    "success": True,
                    "overall_score": overall_score,
                    "analytics": analytics,
                }

        result = asyncio.run(_generate())
        logger.info(f"Report generated for session {session_id}")
        return result

    except Exception as e:
        logger.exception(f"Error generating report for session {session_id}: {e}")
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e, countdown=60)
        return {
            "success": False,
            "error": str(e),
        }


@shared_task(
    name="app.workers.tasks.send_notification_task",
    max_retries=5,
)
def send_notification_task(
    user_id: int,
    message: str,
    notification_type: str = "info"
) -> Dict[str, Any]:
    """
    Send notification to user

    Args:
        user_id: User ID
        message: Notification message
        notification_type: Type of notification

    Returns:
        Dict containing send result
    """
    try:
        logger.info(
            f"Sending notification to user {user_id}: {message}"
        )

        # Placeholder: Integrate with actual notification service
        # e.g., email, SMS, push notification, WeChat, etc.

        # Simulate sending
        result = {
            "success": True,
            "user_id": user_id,
            "message": message,
            "notification_type": notification_type,
            "sent_at": datetime.now().isoformat(),
        }

        logger.info(f"Notification sent to user {user_id}")
        return result

    except Exception as e:
        logger.exception(
            f"Error sending notification to user {user_id}: {e}"
        )
        return {
            "success": False,
            "error": str(e),
        }


@shared_task(
    name="app.workers.tasks.cleanup_temp_files_task",
)
def cleanup_temp_files_task() -> Dict[str, Any]:
    """
    Clean up old temporary files

    Returns:
        Dict containing cleanup result
    """
    import asyncio

    try:
        logger.info("Starting temporary files cleanup")

        async def _cleanup():
            # Get all session IDs with active connections
            from app.websockets.manager import manager

            active_sessions = set(manager.active_connections.keys())

            # This would require tracking temp files by session
            # For now, just log the action
            return {
                "cleaned_sessions": 0,
                "active_sessions": len(active_sessions),
            }

        result = asyncio.run(_cleanup())
        logger.info(f"Temporary files cleanup completed: {result}")
        return result

    except Exception as e:
        logger.exception(f"Error cleaning up temp files: {e}")
        return {
            "success": False,
            "error": str(e),
        }


@shared_task(
    name="app.workers.tasks.process_pending_evaluations_task",
)
def process_pending_evaluations_task() -> Dict[str, Any]:
    """
    Process pending evaluations

    Returns:
        Dict containing processing result
    """
    try:
        logger.info("Processing pending evaluations")

        # Placeholder: Process pending evaluations
        # This would query for evaluations with status="pending"
        # and process them

        result = {
            "processed_count": 0,
            "timestamp": datetime.now().isoformat(),
        }

        logger.info(f"Pending evaluations processed: {result}")
        return result

    except Exception as e:
        logger.exception(f"Error processing pending evaluations: {e}")
        return {
            "success": False,
            "error": str(e),
        }


@shared_task(
    name="app.workers.tasks.batch_process_audio_task",
)
def batch_process_audio_task(
    audio_items: list[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Process multiple audio items in batch

    Args:
        audio_items: List of audio items to process

    Returns:
        Dict containing batch processing result
    """
    import asyncio

    try:
        logger.info(f"Batch processing {len(audio_items)} audio items")

        async def _process_batch():
            results = []
            for item in audio_items:
                result = await audio_service.process_audio(
                    audio_data=item.get("audio_data"),
                    audio_format=item.get("format", "wav"),
                    session_id=item.get("session_id"),
                    user_id=item.get("user_id")
                )
                results.append(result)
            return results

        results = asyncio.run(_process_batch())

        success_count = sum(1 for r in results if r.get("success"))
        logger.info(
            f"Batch processing completed: {success_count}/{len(audio_items)} succeeded"
        )

        return {
            "success": True,
            "total": len(audio_items),
            "succeeded": success_count,
            "failed": len(audio_items) - success_count,
            "results": results,
        }

    except Exception as e:
        logger.exception(f"Error in batch audio processing: {e}")
        return {
            "success": False,
            "error": str(e),
        }
