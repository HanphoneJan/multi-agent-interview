"""Interview API endpoints"""
import math
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.schemas.interview import (
    InterviewScenarioCreate,
    InterviewScenarioUpdate,
    InterviewScenarioResponse,
    InterviewSessionCreate,
    InterviewSessionUpdate,
    InterviewSessionResponse,
    InterviewQuestionCreate,
    InterviewQuestionResponse
)
from app.schemas.common import MessageResponse, PaginatedResponse
from app.schemas.evaluation import OverallInterviewEvaluationCreate
from app.services.interview_service import (
    get_scenarios,
    get_scenario_by_id,
    create_scenario,
    update_scenario,
    delete_scenario,
    get_session_by_id,
    get_user_sessions,
    create_session,
    update_session,
    pause_session,
    resume_session,
    end_session,
    cancel_session,
    get_session_questions,
    create_question
)
from app.services.evaluation_service import upsert_overall_evaluation
from app.core.exceptions import NotFoundError, ValidationError
from typing import Annotated

router = APIRouter(prefix="/interviews", tags=["Interviews"])


def _normalize_score(value: Optional[float], fallback: int = 0) -> int:
    """Clamp a possibly empty score into the report's 0-100 integer range."""
    try:
        return max(0, min(100, int(round(float(value)))))
    except (TypeError, ValueError):
        return fallback


def _build_video_evaluation_payload(
    session_id: int,
    user_id: int,
    analysis_result
) -> OverallInterviewEvaluationCreate:
    """Map recorded-video analysis results into the existing report schema."""
    overall_score = _normalize_score(analysis_result.overall_score)
    professional_knowledge = _normalize_score(analysis_result.professional_knowledge_score, overall_score)
    language_expression = _normalize_score(analysis_result.language_expression_score, overall_score)
    logical_thinking = _normalize_score(analysis_result.logical_thinking_score, overall_score)
    communication_skills = _normalize_score(analysis_result.communication_skills_score, overall_score)
    overall_impression = _normalize_score(analysis_result.overall_impression_score, overall_score)

    skill_match = round((professional_knowledge + communication_skills + overall_impression) / 3)
    stress_response = round((logical_thinking + overall_impression) / 2)
    personality = overall_impression
    motivation = round((overall_score + overall_impression) / 2)
    value = round((professional_knowledge + overall_impression) / 2)

    overall_evaluation = "\n".join(
        part for part in [
            f"整体印象：{analysis_result.overall_impression}".strip(),
            f"语言表达：{analysis_result.language_expression}".strip(),
            f"逻辑思维：{analysis_result.logical_thinking}".strip(),
            f"专业知识：{analysis_result.professional_knowledge}".strip(),
            f"沟通能力：{analysis_result.communication_skills}".strip(),
        ]
        if part
    )

    help_text = "\n".join(
        part for part in [
            "优势：" + "；".join(analysis_result.strengths) if analysis_result.strengths else "",
            "待改进：" + "；".join(analysis_result.weaknesses) if analysis_result.weaknesses else "",
            f"建议：{analysis_result.suggestions}".strip() if analysis_result.suggestions else "",
        ]
        if part
    )

    return OverallInterviewEvaluationCreate(
        session_id=session_id,
        user_id=user_id,
        overall_evaluation=overall_evaluation or "已完成视频分析，请结合详细指标查看表现。",
        help=help_text or "已完成视频分析，但未提取到足够的结构化改进建议。",
        recommendation=analysis_result.suggestions or "建议结合完整面试问答继续复盘本次表现。",
        overall_score=overall_score,
        professional_knowledge=professional_knowledge,
        skill_match=skill_match,
        language_expression=language_expression,
        logical_thinking=logical_thinking,
        stress_response=stress_response,
        personality=personality,
        motivation=motivation,
        value=value,
    )


# ============ Scenario Management ============

@router.get("/scenarios", response_model=PaginatedResponse[InterviewScenarioResponse])
async def list_scenarios(
    skip: int = 0,
    limit: int = 100,
    technology_field: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Get interview scenarios list"""
    scenarios = await get_scenarios(db, skip, limit, technology_field)
    total = len(scenarios)
    page = (skip // limit) + 1 if limit > 0 else 1
    page_size = limit if limit > 0 else total
    total_pages = max(1, math.ceil(total / page_size)) if page_size > 0 else 1
    return {
        "items": scenarios,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    }


@router.get("/scenarios/{scenario_id}", response_model=InterviewScenarioResponse)
async def get_scenario(
    scenario_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get scenario by ID"""
    scenario = await get_scenario_by_id(db, scenario_id)
    if not scenario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Interview scenario not found"
        )
    return scenario


@router.post("/scenarios", response_model=InterviewScenarioResponse, status_code=status.HTTP_201_CREATED)
async def create_interview_scenario(
    scenario_data: InterviewScenarioCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create interview scenario"""
    try:
        scenario = await create_scenario(db, scenario_data)
        return scenario
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put("/scenarios/{scenario_id}", response_model=InterviewScenarioResponse)
async def update_interview_scenario(
    scenario_id: int,
    scenario_data: InterviewScenarioUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update interview scenario"""
    try:
        scenario = await update_scenario(db, scenario_id, scenario_data)
        return scenario
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/scenarios/{scenario_id}", response_model=MessageResponse)
async def delete_interview_scenario(
    scenario_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Delete interview scenario"""
    try:
        await delete_scenario(db, scenario_id)
        return {"message": "Scenario deleted successfully"}
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# ============ Session Management ============

@router.get("/sessions/{session_id}", response_model=InterviewSessionResponse)
async def get_interview_session(
    session_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get interview session by ID"""
    session = await get_session_by_id(db, session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Interview session not found"
        )
    return session


@router.get("/sessions", response_model=PaginatedResponse[InterviewSessionResponse])
async def list_user_sessions(
    skip: int = 0,
    limit: int = 20,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get current user's interview sessions"""
    sessions = await get_user_sessions(db, current_user["id"], skip, limit)
    total = len(sessions)
    page = (skip // limit) + 1 if limit > 0 else 1
    page_size = limit if limit > 0 else total
    total_pages = max(1, math.ceil(total / page_size)) if page_size > 0 else 1
    return {
        "items": sessions,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    }


@router.post("/sessions", response_model=InterviewSessionResponse, status_code=status.HTTP_201_CREATED)
async def create_interview_session(
    session_data: InterviewSessionCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create interview session"""
    try:
        session = await create_session(db, current_user["id"], session_data)
        return session
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.put("/sessions/{session_id}", response_model=InterviewSessionResponse)
async def update_interview_session(
    session_id: int,
    session_data: InterviewSessionUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update interview session"""
    try:
        session = await update_session(db, session_id, session_data)
        return session
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.put("/sessions/{session_id}/pause", response_model=InterviewSessionResponse)
async def pause_interview_session(
    session_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Pause interview session"""
    try:
        session = await pause_session(db, session_id)
        return session
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put("/sessions/{session_id}/resume", response_model=InterviewSessionResponse)
async def resume_interview_session(
    session_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Resume interview session"""
    try:
        session = await resume_session(db, session_id)
        return session
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/sessions/{session_id}/end", response_model=InterviewSessionResponse)
async def end_interview_session(
    session_id: int,
    db: AsyncSession = Depends(get_db)
):
    """End interview session"""
    try:
        session = await end_session(db, session_id)
        return session
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/sessions/{session_id}/cancel", response_model=InterviewSessionResponse)
async def cancel_interview_session(
    session_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Cancel interview session"""
    try:
        session = await cancel_session(db, session_id)
        return session
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# ============ Question Management ============

@router.get("/sessions/{session_id}/questions", response_model=list[InterviewQuestionResponse])
async def list_session_questions(
    session_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get questions for a session"""
    # Check if session exists
    session = await get_session_by_id(db, session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Interview session not found"
        )
    
    questions = await get_session_questions(db, session_id)
    return questions


@router.post("/sessions/{session_id}/questions", response_model=InterviewQuestionResponse, status_code=status.HTTP_201_CREATED)
async def create_interview_question(
    session_id: int,
    question_data: InterviewQuestionCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create interview question"""
    try:
        question = await create_question(db, session_id, question_data)
        return question
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get("/user-data")
async def get_user_interview_data(
    current_user: Annotated[dict, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db)
):
    """
    Get user interview data summary (compatible with uniapp)

    Returns aggregated interview data for the current user including:
    - Total sessions count
    - Completed sessions count
    - Recent sessions
    - Evaluation reports summary
    """
    from sqlalchemy import select, func
    from app.models.interview import interview_sessions, interview_scenarios
    from app.models.evaluation import overall_interview_evaluations

    user_id = current_user["id"]

    # Get total sessions count
    total_result = await db.execute(
        select(func.count(interview_sessions.c.id))
        .where(interview_sessions.c.user_id == user_id)
    )
    total_sessions = total_result.scalar() or 0

    # Get completed sessions count
    completed_result = await db.execute(
        select(func.count(interview_sessions.c.id))
        .where(
            (interview_sessions.c.user_id == user_id) &
            (interview_sessions.c.is_finished == True)
        )
    )
    completed_sessions = completed_result.scalar() or 0

    # Get recent sessions with scenario info
    sessions_result = await db.execute(
        select(
            interview_sessions.c.id,
            interview_sessions.c.start_time,
            interview_sessions.c.end_time,
            interview_sessions.c.status,
            interview_sessions.c.is_finished,
            interview_scenarios.c.name.label("scenario_name"),
            interview_scenarios.c.technology_field
        )
        .join(
            interview_scenarios,
            interview_sessions.c.scenario_id == interview_scenarios.c.id
        )
        .where(interview_sessions.c.user_id == user_id)
        .order_by(interview_sessions.c.start_time.desc())
        .limit(10)
    )
    recent_sessions = [
        {
            "id": row.id,
            "start_time": row.start_time.isoformat() if row.start_time else None,
            "end_time": row.end_time.isoformat() if row.end_time else None,
            "status": row.status,
            "is_finished": row.is_finished,
            "scenario_name": row.scenario_name,
            "technology_field": row.technology_field
        }
        for row in sessions_result.fetchall()
    ]

    # Get evaluation summary
    eval_result = await db.execute(
        select(
            func.count(overall_interview_evaluations.c.id).label("total_evaluations"),
            func.avg(overall_interview_evaluations.c.overall_score).label("avg_score")
        )
        .where(overall_interview_evaluations.c.user_id == user_id)
    )
    eval_row = eval_result.first()

    return {
        "user_id": user_id,
        "total_sessions": total_sessions,
        "completed_sessions": completed_sessions,
        "completion_rate": round(completed_sessions / total_sessions * 100, 2) if total_sessions > 0 else 0,
        "recent_sessions": recent_sessions,
        "total_evaluations": eval_row.total_evaluations or 0,
        "average_score": round(float(eval_row.avg_score), 2) if eval_row.avg_score else None
    }


# ============ Video Upload for Non-Realtime Interview ============

# Allowed video formats
ALLOWED_VIDEO_EXTENSIONS = {".webm", ".mp4", ".mov", ".avi"}
MAX_VIDEO_SIZE = 500 * 1024 * 1024  # 500MB


@router.post("/sessions/{session_id}/video", response_model=MessageResponse)
async def upload_interview_video(
    session_id: int,
    file: UploadFile = File(..., description="Interview video file (WEBM, MP4, MOV, AVI)"),
    current_user: Annotated[dict, Depends(get_current_user)] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Upload interview video for a session (non-realtime interview)

    - **session_id**: Interview session ID
    - **file**: Video file to upload (max 500MB)

    The video will be saved to local storage and the path will be saved to the session.
    """
    from sqlalchemy import select, update
    from app.models.interview import interview_sessions
    import os
    import uuid

    user_id = current_user["id"]

    # Verify session exists and belongs to user
    result = await db.execute(
        select(interview_sessions)
        .where(
            (interview_sessions.c.id == session_id) &
            (interview_sessions.c.user_id == user_id)
        )
    )
    session = result.first()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Interview session not found"
        )

    # Validate file extension
    filename = file.filename or ""
    ext = filename.lower().rsplit(".", 1)[-1] if "." in filename else ""
    if f".{ext}" not in ALLOWED_VIDEO_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type: .{ext}. Allowed: {', '.join(ALLOWED_VIDEO_EXTENSIONS)}"
        )

    # Read and validate file content
    try:
        file_content = await file.read()
        if len(file_content) > MAX_VIDEO_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File too large. Max size: {MAX_VIDEO_SIZE / 1024 / 1024}MB"
            )
        if len(file_content) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Empty file"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to read file: {str(e)}"
        )

    # Save to local storage
    try:
        # Create upload directory
        base_dir = os.path.dirname(
            os.path.dirname(
                os.path.dirname(
                    os.path.dirname(__file__)
                )
            )
        )
        upload_dir = os.path.join(base_dir, "uploads", "interviews", str(session_id))
        os.makedirs(upload_dir, exist_ok=True)

        # Generate unique filename
        unique_filename = f"{uuid.uuid4().hex}_{session_id}.{ext}"
        file_path = os.path.join(upload_dir, unique_filename)

        # Write file
        with open(file_path, "wb") as f:
            f.write(file_content)

        # Generate URL path (relative, for API to serve)
        video_url = f"/uploads/interviews/{session_id}/{unique_filename}"

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save video: {str(e)}"
        )

    # Update session with video URL
    await db.execute(
        update(interview_sessions)
        .where(interview_sessions.c.id == session_id)
        .values(video_url=video_url)
    )
    await db.commit()

    return MessageResponse(
        message="Video uploaded successfully",
        data={
            "session_id": session_id,
            "video_url": video_url,
            "filename": unique_filename,
            "size": len(file_content)
        }
    )


@router.post("/sessions/{session_id}/analyze-video", response_model=MessageResponse)
async def analyze_interview_video(
    session_id: int,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db)
):
    """
    Analyze interview video using Qwen-VL (non-realtime interview)

    This endpoint triggers video analysis after the interview is completed.
    The analysis results will be saved to the evaluation report.

    - **session_id**: Interview session ID
    """
    from sqlalchemy import select
    from app.core.llm_context import get_messages
    from app.models.interview import interview_sessions, interview_scenarios
    from app.services.qwen_vl_service import get_qwen_vl_service

    user_id = current_user["id"]

    # Get session info
    result = await db.execute(
        select(
            interview_sessions,
            interview_scenarios.c.name.label("scenario_name"),
            interview_scenarios.c.description.label("scenario_description")
        )
        .select_from(interview_sessions)
        .join(
            interview_scenarios,
            interview_sessions.c.scenario_id == interview_scenarios.c.id,
            isouter=True
        )
        .where(
            (interview_sessions.c.id == session_id) &
            (interview_sessions.c.user_id == user_id)
        )
    )
    row = result.first()

    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Interview session not found"
        )

    session_data = dict(row._asdict())
    video_url = session_data.get("video_url")

    if not video_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No video uploaded for this session"
        )

    # Get conversation history
    conversation_history = await get_messages(str(session_id))

    # Call Qwen-VL service
    qwen_vl = get_qwen_vl_service()
    scenario_name = session_data.get("scenario_name") or "技术面试"

    try:
        analysis_result = await qwen_vl.analyze_interview_video(
            video_url=video_url,
            scenario_name=scenario_name,
            conversation_history=conversation_history
        )

        evaluation_payload = _build_video_evaluation_payload(
            session_id=session_id,
            user_id=user_id,
            analysis_result=analysis_result,
        )
        evaluation_report = await upsert_overall_evaluation(db, evaluation_payload)

        return MessageResponse(
            message="Video analysis completed",
            data={
                "session_id": session_id,
                "report_id": evaluation_report["id"],
                "overall_score": analysis_result.overall_score,
                "language_expression": analysis_result.language_expression,
                "logical_thinking": analysis_result.logical_thinking,
                "professional_knowledge": analysis_result.professional_knowledge,
                "communication_skills": analysis_result.communication_skills,
                "overall_impression": analysis_result.overall_impression,
                "strengths": analysis_result.strengths,
                "weaknesses": analysis_result.weaknesses,
                "suggestions": analysis_result.suggestions,
                "evaluation_report": evaluation_report,
            }
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Video analysis failed: {str(e)}"
        )
