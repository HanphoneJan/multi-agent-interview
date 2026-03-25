"""Evaluation service"""
from datetime import datetime
from typing import Optional

from sqlalchemy import select, insert, update, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.evaluation import (
    response_metadata,
    response_analysis,
    answer_evaluations,
    resume_evaluations,
    overall_interview_evaluations
)
from app.schemas.evaluation import (
    ResumeEvaluationCreate,
    OverallInterviewEvaluationCreate
)
from app.core.exceptions import NotFoundError


# ============ Answer Evaluations ============

async def get_answer_evaluation(db: AsyncSession, evaluation_id: int) -> Optional[dict]:
    """Get answer evaluation by ID"""
    result = await db.execute(
        select(answer_evaluations).where(answer_evaluations.c.id == evaluation_id)
    )
    evaluation = result.first()
    if evaluation:
        return dict(evaluation._asdict())
    return None


async def get_answer_evaluations_by_question(
    db: AsyncSession,
    question_id: int
) -> list:
    """Get answer evaluations for a question"""
    result = await db.execute(
        select(answer_evaluations).where(answer_evaluations.c.question_id == question_id)
    )
    evaluations = result.all()
    return [dict(e._asdict()) for e in evaluations]


async def create_answer_evaluation(
    db: AsyncSession,
    question_id: int,
    analysis_id: int,
    evaluation_text: str,
    score: float
) -> dict:
    """Create answer evaluation"""
    stmt = insert(answer_evaluations).values(
        question_id=question_id,
        analysis_id=analysis_id,
        evaluation_text=evaluation_text,
        score=score,
        evaluated_at=datetime.utcnow()
    ).returning(answer_evaluations.c.id)
    
    result = await db.execute(stmt)
    await db.commit()
    
    evaluation_id = result.scalar_one()
    return await get_answer_evaluation(db, evaluation_id)


# ============ Resume Evaluations ============

async def get_resume_evaluation(db: AsyncSession, user_id: int) -> Optional[dict]:
    """Get resume evaluation by user ID"""
    result = await db.execute(
        select(resume_evaluations).where(resume_evaluations.c.user_id == user_id)
    )
    evaluation = result.first()
    if evaluation:
        return dict(evaluation._asdict())
    return None


async def create_resume_evaluation(
    db: AsyncSession,
    user_id: int,
    resume_score: str,
    resume_summary: str
) -> dict:
    """Create or update resume evaluation"""
    # Check if evaluation exists
    existing = await get_resume_evaluation(db, user_id)
    
    if existing:
        # Update existing evaluation
        stmt = (
            update(resume_evaluations)
            .where(resume_evaluations.c.id == existing["id"])
            .values(
                resume_score=resume_score,
                resume_summary=resume_summary,
                updated_at=datetime.utcnow(),
            )
        )
        await db.execute(stmt)
        await db.commit()
        return await get_resume_evaluation(db, user_id)
    else:
        # Create new evaluation
        stmt = insert(resume_evaluations).values(
            user_id=user_id,
            resume_score=resume_score,
            resume_summary=resume_summary
        ).returning(resume_evaluations.c.id)
        
        result = await db.execute(stmt)
        await db.commit()

        return await get_resume_evaluation(db, user_id)


# ============ Overall Interview Evaluations ============

async def get_overall_evaluation(db: AsyncSession, session_id: int) -> Optional[dict]:
    """Get overall evaluation by session ID"""
    result = await db.execute(
        select(overall_interview_evaluations).where(
            overall_interview_evaluations.c.session_id == session_id
        )
    )
    evaluation = result.first()
    if evaluation:
        return dict(evaluation._asdict())
    return None


async def get_user_overall_evaluations(
    db: AsyncSession,
    user_id: int,
    skip: int = 0,
    limit: int = 20
) -> list:
    """Get overall evaluations for a user"""
    result = await db.execute(
        select(overall_interview_evaluations)
        .where(overall_interview_evaluations.c.user_id == user_id)
        .offset(skip)
        .limit(limit)
        .order_by(overall_interview_evaluations.c.created_at.desc())
    )
    evaluations = result.all()
    return [dict(e._asdict()) for e in evaluations]


async def create_overall_evaluation(
    db: AsyncSession,
    evaluation_data: OverallInterviewEvaluationCreate
) -> dict:
    """Create overall interview evaluation"""
    stmt = insert(overall_interview_evaluations).values(
        session_id=evaluation_data.session_id,
        user_id=evaluation_data.user_id,
        overall_evaluation=evaluation_data.overall_evaluation,
        help=evaluation_data.help,
        recommendation=evaluation_data.recommendation,
        overall_score=evaluation_data.overall_score,
        professional_knowledge=evaluation_data.professional_knowledge,
        skill_match=evaluation_data.skill_match,
        language_expression=evaluation_data.language_expression,
        logical_thinking=evaluation_data.logical_thinking,
        stress_response=evaluation_data.stress_response,
        personality=evaluation_data.personality,
        motivation=evaluation_data.motivation,
        value=evaluation_data.value
    ).returning(overall_interview_evaluations.c.id)
    
    result = await db.execute(stmt)
    await db.commit()
    
    evaluation_id = result.scalar_one()
    return await get_overall_evaluation(db, evaluation_data.session_id)


async def upsert_overall_evaluation(
    db: AsyncSession,
    evaluation_data: OverallInterviewEvaluationCreate
) -> dict:
    """Create or update overall interview evaluation by session ID."""
    existing = await get_overall_evaluation(db, evaluation_data.session_id)

    payload = {
        "user_id": evaluation_data.user_id,
        "overall_evaluation": evaluation_data.overall_evaluation,
        "help": evaluation_data.help,
        "recommendation": evaluation_data.recommendation,
        "overall_score": evaluation_data.overall_score,
        "professional_knowledge": evaluation_data.professional_knowledge,
        "skill_match": evaluation_data.skill_match,
        "language_expression": evaluation_data.language_expression,
        "logical_thinking": evaluation_data.logical_thinking,
        "stress_response": evaluation_data.stress_response,
        "personality": evaluation_data.personality,
        "motivation": evaluation_data.motivation,
        "value": evaluation_data.value,
    }

    if existing:
        await db.execute(
            update(overall_interview_evaluations)
            .where(overall_interview_evaluations.c.session_id == evaluation_data.session_id)
            .values(updated_at=datetime.utcnow(), **payload)
        )
        await db.commit()
        return await get_overall_evaluation(db, evaluation_data.session_id)

    return await create_overall_evaluation(db, evaluation_data)


# ============ Response Analysis ============

async def create_response_analysis(
    db: AsyncSession,
    question_id: int,
    speech_text: str,
    audio_duration: Optional[float] = None,
    facial_expression: str = "",
    body_language: str = ""
) -> dict:
    """Create response metadata and analysis"""
    # Create metadata
    metadata_stmt = insert(response_metadata).values(
        question_id=question_id,
        audio_duration=audio_duration,
        upload_timestamp=datetime.utcnow()
    ).returning(response_metadata.c.id)
    
    result = await db.execute(metadata_stmt)
    metadata_id = result.scalar_one()
    
    # Create analysis
    analysis_stmt = insert(response_analysis).values(
        metadata_id=metadata_id,
        speech_text=speech_text,
        facial_expression=facial_expression,
        body_language=body_language,
        analysis_timestamp=datetime.utcnow()
    ).returning(response_analysis.c.id)
    
    result = await db.execute(analysis_stmt)
    await db.commit()
    
    analysis_id = result.scalar_one()
    
    # Return combined result
    result = await db.execute(
        select(
            response_analysis,
            response_metadata.c.audio_duration,
            response_metadata.c.video_duration
        )
        .select_from(response_analysis)
        .join(response_metadata, response_analysis.c.metadata_id == response_metadata.c.id)
        .where(response_analysis.c.id == analysis_id)
    )
    row = result.first()
    
    return {
        "id": row.id,
        "metadata_id": metadata_id,
        "speech_text": row.speech_text,
        "facial_expression": row.facial_expression,
        "body_language": row.body_language,
        "audio_duration": row.audio_duration,
        "video_duration": row.video_duration,
        "analysis_timestamp": row.analysis_timestamp,
        "created_at": row.created_at
    }


async def get_response_analysis(db: AsyncSession, analysis_id: int) -> Optional[dict]:
    """Get response analysis by ID"""
    result = await db.execute(
        select(response_analysis).where(response_analysis.c.id == analysis_id)
    )
    analysis = result.first()
    if analysis:
        return dict(analysis._asdict())
    return None
