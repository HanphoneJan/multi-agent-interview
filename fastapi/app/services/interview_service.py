"""Interview service"""
from typing import Optional, List

from sqlalchemy import select, insert, update, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.interview import (
    interview_scenarios,
    interview_sessions,
    interview_questions
)
from app.schemas.interview import (
    InterviewScenarioCreate,
    InterviewScenarioUpdate,
    InterviewSessionCreate,
    InterviewSessionUpdate,
    InterviewQuestionCreate
)
from app.core.constants import InterviewSessionStatus
from app.core.exceptions import NotFoundError, ValidationError


# ============ Scenario Management ============

async def get_scenarios(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100,
    technology_field: Optional[str] = None
) -> List[dict]:
    """Get interview scenarios list"""
    query = select(interview_scenarios)
    
    if technology_field:
        query = query.where(interview_scenarios.c.technology_field == technology_field)
    
    query = query.offset(skip).limit(limit).order_by(interview_scenarios.c.created_at.desc())
    
    result = await db.execute(query)
    scenarios = result.all()
    return [dict(s._asdict()) for s in scenarios]


async def get_scenario_by_id(db: AsyncSession, scenario_id: int) -> Optional[dict]:
    """Get scenario by ID"""
    result = await db.execute(
        select(interview_scenarios).where(interview_scenarios.c.id == scenario_id)
    )
    scenario = result.first()
    if scenario:
        return dict(scenario._asdict())
    return None


async def create_scenario(
    db: AsyncSession,
    scenario_data: InterviewScenarioCreate
) -> dict:
    """Create interview scenario"""
    stmt = insert(interview_scenarios).values(
        name=scenario_data.name,
        technology_field=scenario_data.technology_field,
        description=scenario_data.description,
        requirements=scenario_data.requirements,
        is_realtime=scenario_data.is_realtime
    ).returning(interview_scenarios.c.id)
    
    result = await db.execute(stmt)
    await db.commit()
    
    scenario_id = result.scalar_one()
    return await get_scenario_by_id(db, scenario_id)


async def update_scenario(
    db: AsyncSession,
    scenario_id: int,
    scenario_data: InterviewScenarioUpdate
) -> Optional[dict]:
    """Update interview scenario"""
    # Check if scenario exists
    scenario = await get_scenario_by_id(db, scenario_id)
    if not scenario:
        raise NotFoundError("Interview scenario not found")
    
    # Build update values
    update_values = {}
    for key, value in scenario_data.model_dump(exclude_unset=True).items():
        update_values[key] = value
    
    if not update_values:
        return scenario
    
    # Update scenario
    await db.execute(
        update(interview_scenarios)
        .where(interview_scenarios.c.id == scenario_id)
        .values(**update_values)
    )
    await db.commit()
    
    return await get_scenario_by_id(db, scenario_id)


async def delete_scenario(db: AsyncSession, scenario_id: int) -> bool:
    """Delete interview scenario"""
    # Check if scenario exists
    scenario = await get_scenario_by_id(db, scenario_id)
    if not scenario:
        raise NotFoundError("Interview scenario not found")
    
    # Check if scenario has active sessions
    result = await db.execute(
        select(func.count()).select_from(interview_sessions)
        .where(interview_sessions.c.scenario_id == scenario_id)
    )
    session_count = result.scalar_one()
    
    if session_count > 0:
        raise ValidationError("Cannot delete scenario with existing sessions")
    
    # Delete scenario (cascade will delete related records)
    await db.execute(
        interview_scenarios.delete().where(interview_scenarios.c.id == scenario_id)
    )
    await db.commit()
    
    return True


# ============ Session Management ============

async def get_session_by_id(db: AsyncSession, session_id: int) -> Optional[dict]:
    """Get session by ID with scenario info"""
    result = await db.execute(
        select(
            interview_sessions,
            interview_scenarios.c.name.label("scenario_name"),
            interview_scenarios.c.technology_field.label("scenario_technology_field"),
            interview_scenarios.c.description.label("scenario_description"),
            interview_scenarios.c.requirements.label("scenario_requirements"),
            interview_scenarios.c.is_realtime.label("scenario_is_realtime"),
        )
        .select_from(interview_sessions)
        .join(
            interview_scenarios,
            interview_sessions.c.scenario_id == interview_scenarios.c.id
        )
        .where(interview_sessions.c.id == session_id)
    )
    row = result.first()
    
    if not row:
        return None
    
    session_dict = dict(row._asdict())
    
    # Build nested scenario object, keep scenario_id for response schema
    scenario_id = session_dict.pop("scenario_id")
    scenario_dict = {
        "id": scenario_id,
        "name": session_dict.pop("scenario_name"),
        "technology_field": session_dict.pop("scenario_technology_field"),
        "description": session_dict.pop("scenario_description"),
        "requirements": session_dict.pop("scenario_requirements"),
        "is_realtime": session_dict.pop("scenario_is_realtime"),
        "created_at": session_dict.get("created_at"),
        "updated_at": session_dict.get("updated_at"),
    }

    session_dict["scenario_id"] = scenario_id
    session_dict["scenario"] = scenario_dict
    return session_dict


async def get_user_sessions(
    db: AsyncSession,
    user_id: int,
    skip: int = 0,
    limit: int = 20
) -> List[dict]:
    """Get user's interview sessions with scenario info"""
    result = await db.execute(
        select(
            interview_sessions,
            interview_scenarios.c.name.label("scenario_name"),
            interview_scenarios.c.technology_field.label("scenario_technology_field"),
            interview_scenarios.c.description.label("scenario_description"),
            interview_scenarios.c.requirements.label("scenario_requirements"),
            interview_scenarios.c.is_realtime.label("scenario_is_realtime"),
        )
        .select_from(interview_sessions)
        .join(
            interview_scenarios,
            interview_sessions.c.scenario_id == interview_scenarios.c.id
        )
        .where(interview_sessions.c.user_id == user_id)
        .offset(skip)
        .limit(limit)
        .order_by(interview_sessions.c.created_at.desc())
    )
    rows = result.all()

    sessions = []
    for row in rows:
        session_dict = dict(row._asdict())

        # Build nested scenario object
        scenario_id = session_dict.pop("scenario_id")
        scenario_dict = {
            "id": scenario_id,
            "name": session_dict.pop("scenario_name"),
            "technology_field": session_dict.pop("scenario_technology_field"),
            "description": session_dict.pop("scenario_description"),
            "requirements": session_dict.pop("scenario_requirements"),
            "is_realtime": session_dict.pop("scenario_is_realtime"),
            "created_at": session_dict.get("created_at"),
            "updated_at": session_dict.get("updated_at"),
        }

        session_dict["scenario_id"] = scenario_id
        session_dict["scenario"] = scenario_dict
        sessions.append(session_dict)

    return sessions


async def create_session(
    db: AsyncSession,
    user_id: int,
    session_data: InterviewSessionCreate
) -> dict:
    """Create interview session"""
    # Check if scenario exists
    scenario = await get_scenario_by_id(db, session_data.scenario_id)
    if not scenario:
        raise NotFoundError("Interview scenario not found")
    
    stmt = insert(interview_sessions).values(
        user_id=user_id,
        scenario_id=session_data.scenario_id,
        start_time=func.now(),  # 使用数据库时间，与 created_at 保持一致
        status="created",  # PostgreSQL interviewsessionstatus 枚举值
        total_questions=0,
        is_finished=False
    ).returning(interview_sessions.c.id)
    
    result = await db.execute(stmt)
    await db.commit()
    
    session_id = result.scalar_one()
    return await get_session_by_id(db, session_id)


async def update_session(
    db: AsyncSession,
    session_id: int,
    session_data: InterviewSessionUpdate
) -> Optional[dict]:
    """Update interview session"""
    # Check if session exists
    session = await get_session_by_id(db, session_id)
    if not session:
        raise NotFoundError("Interview session not found")
    
    # Build update values
    update_values = {}
    for key, value in session_data.model_dump(exclude_unset=True).items():
        if isinstance(value, InterviewSessionStatus):
            update_values[key] = value.value
        else:
            update_values[key] = value
    
    if not update_values:
        return session
    
    # Update session
    await db.execute(
        update(interview_sessions)
        .where(interview_sessions.c.id == session_id)
        .values(**update_values)
    )
    await db.commit()
    
    return await get_session_by_id(db, session_id)


async def pause_session(db: AsyncSession, session_id: int) -> Optional[dict]:
    """Pause interview session"""
    session = await get_session_by_id(db, session_id)
    if not session:
        raise NotFoundError("Interview session not found")

    # Allow pause from CREATED or IN_PROGRESS status
    if session["status"] not in [InterviewSessionStatus.CREATED, InterviewSessionStatus.IN_PROGRESS]:
        raise ValidationError("Can only pause a created or in-progress session")
    
    await db.execute(
        update(interview_sessions)
        .where(interview_sessions.c.id == session_id)
        .values(
            status=InterviewSessionStatus.PAUSED.value,
            paused_at=func.now()
        )
    )
    await db.commit()
    
    return await get_session_by_id(db, session_id)


async def resume_session(db: AsyncSession, session_id: int) -> Optional[dict]:
    """Resume interview session"""
    session = await get_session_by_id(db, session_id)
    if not session:
        raise NotFoundError("Interview session not found")
    
    if session["status"] != InterviewSessionStatus.PAUSED:
        raise ValidationError("Can only resume a paused session")
    
    await db.execute(
        update(interview_sessions)
        .where(interview_sessions.c.id == session_id)
        .values(
            status=InterviewSessionStatus.IN_PROGRESS.value,
            resumed_at=func.now()
        )
    )
    await db.commit()
    
    return await get_session_by_id(db, session_id)


async def end_session(db: AsyncSession, session_id: int) -> Optional[dict]:
    """End interview session"""
    session = await get_session_by_id(db, session_id)
    if not session:
        raise NotFoundError("Interview session not found")
    
    if session["status"] in [InterviewSessionStatus.COMPLETED, InterviewSessionStatus.CANCELLED]:
        raise ValidationError("Session already ended")
    
    await db.execute(
        update(interview_sessions)
        .where(interview_sessions.c.id == session_id)
        .values(
            status=InterviewSessionStatus.COMPLETED.value,
            end_time=func.now(),
            is_finished=True
        )
    )
    await db.commit()
    
    return await get_session_by_id(db, session_id)


async def cancel_session(db: AsyncSession, session_id: int) -> Optional[dict]:
    """Cancel interview session"""
    session = await get_session_by_id(db, session_id)
    if not session:
        raise NotFoundError("Interview session not found")
    
    if session["status"] in [InterviewSessionStatus.COMPLETED, InterviewSessionStatus.CANCELLED]:
        raise ValidationError("Session already ended")
    
    await db.execute(
        update(interview_sessions)
        .where(interview_sessions.c.id == session_id)
        .values(
            status=InterviewSessionStatus.CANCELLED.value,
            end_time=func.now()
        )
    )
    await db.commit()

    return await get_session_by_id(db, session_id)


# ============ Question Management ============

def _question_row_to_dict(row) -> dict:
    """Convert question row to dict, adding asked_at from created_at."""
    d = dict(row._asdict()) if hasattr(row, "_asdict") else dict(row)
    if "asked_at" not in d and "created_at" in d:
        d["asked_at"] = d["created_at"]
    return d


async def get_session_questions(
    db: AsyncSession,
    session_id: int
) -> List[dict]:
    """Get questions for a session"""
    result = await db.execute(
        select(interview_questions)
        .where(interview_questions.c.session_id == session_id)
        .order_by(interview_questions.c.question_number)
    )
    questions = result.all()
    return [_question_row_to_dict(q) for q in questions]


async def create_question(
    db: AsyncSession,
    session_id: int,
    question_data: InterviewQuestionCreate
) -> dict:
    """Create interview question"""
    # Check if session exists
    session = await get_session_by_id(db, session_id)
    if not session:
        raise NotFoundError("Interview session not found")
    
    stmt = insert(interview_questions).values(
        session_id=session_id,
        question_text=question_data.question_text,
        question_number=question_data.question_number
    ).returning(interview_questions.c.id)
    
    result = await db.execute(stmt)
    
    # Update total questions count
    await db.execute(
        update(interview_sessions)
        .where(interview_sessions.c.id == session_id)
        .values(total_questions=interview_sessions.c.total_questions + 1)
    )
    
    await db.commit()
    
    question_id = result.scalar_one()
    
    # Get the created question
    result = await db.execute(
        select(interview_questions).where(interview_questions.c.id == question_id)
    )
    question = result.first()
    return _question_row_to_dict(question)
