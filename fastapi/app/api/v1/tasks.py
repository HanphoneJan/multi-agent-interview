"""API endpoints for managing Celery tasks"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Optional, Dict, Any
from pydantic import BaseModel

from app.dependencies import get_current_user
from app.workers.task_manager import task_manager

router = APIRouter()


class TaskStatusResponse(BaseModel):
    """Task status response model"""
    task_id: str
    status: str
    ready: bool
    successful: Optional[bool] = None
    result: Optional[Any] = None


class TaskSubmissionRequest(BaseModel):
    """Task submission request model"""
    audio_data: Optional[str] = None
    session_id: str
    user_id: int
    audio_format: Optional[str] = "wav"


@router.get("/tasks/{task_id}/status", response_model=TaskStatusResponse)
async def get_task_status(
    task_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get the status of a Celery task.

    This endpoint allows you to check the progress and result of async tasks.
    """
    status_result = task_manager.get_task_status(task_id)
    is_ready = task_manager.is_task_ready(task_id)

    if is_ready:
        is_successful = task_manager.is_task_successful(task_id)
        result_value = task_manager.get_task_result_value(task_id)
    else:
        is_successful = None
        result_value = None

    return TaskStatusResponse(
        task_id=task_id,
        status=status_result,
        ready=is_ready,
        successful=is_successful,
        result=result_value
    )


@router.post("/tasks/audio/process")
async def submit_audio_task(
    request: TaskSubmissionRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Submit an audio processing task to the Celery worker.

    The task will be processed asynchronously in the background.
    """
    if not request.audio_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="audio_data is required"
        )

    task_id = task_manager.submit_audio_task(
        audio_data_b64=request.audio_data,
        session_id=request.session_id,
        user_id=request.user_id,
        audio_format=request.audio_format or "wav"
    )

    return {
        "success": True,
        "task_id": task_id,
        "message": "Audio processing task submitted"
    }


@router.post("/tasks/reports/generate")
async def submit_report_task(
    session_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Submit a report generation task to the Celery worker.

    The task will generate an interview evaluation report asynchronously.
    """
    task_id = task_manager.submit_report_task(
        session_id=session_id,
        user_id=current_user.get("user_id")
    )

    return {
        "success": True,
        "task_id": task_id,
        "message": "Report generation task submitted"
    }


@router.delete("/tasks/{task_id}")
async def revoke_task(
    task_id: str,
    terminate: bool = False,
    current_user: dict = Depends(get_current_user)
):
    """
    Revoke (cancel) a Celery task.

    Args:
        task_id: The ID of the task to revoke
        terminate: If True, terminate the task immediately; otherwise, let it finish gracefully
    """
    task_manager.revoke_task(task_id, terminate=terminate)

    return {
        "success": True,
        "task_id": task_id,
        "message": f"Task revoked (terminate={terminate})"
    }


@router.get("/tasks/{task_id}/result")
async def get_task_result(
    task_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get the result of a completed task.

    Returns the task result if the task has completed, otherwise returns an error.
    """
    result = task_manager.get_task_result_value(task_id)

    if result is None:
        # Task not ready
        task_status = task_manager.get_task_status(task_id)
        raise HTTPException(
            status_code=status.HTTP_202_ACCEPTED,
            detail=f"Task not yet completed. Current status: {task_status}"
        )

    return {
        "success": True,
        "task_id": task_id,
        "result": result
    }
