"""Interview tables (SQLAlchemy Core)"""
from sqlalchemy import Table, Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Enum, func
from app.models.base import metadata
from app.core.constants import InterviewSessionStatus

# Interview scenarios table
interview_scenarios = Table(
    "interview_scenarios",
    metadata,
    Column("id", Integer, primary_key=True, index=True),
    Column("name", String(200), nullable=False),
    Column("technology_field", String(200), default="通用", nullable=False),
    Column("description", Text, default="", nullable=False),
    Column("requirements", Text, default="", nullable=False),
    Column("is_realtime", Boolean, default=True, nullable=False),
    
    # Timestamps
    Column("created_at", DateTime(timezone=True), server_default="now()", nullable=False),
    Column("updated_at", DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False),
)

# Interview sessions table
interview_sessions = Table(
    "interview_sessions",
    metadata,
    Column("id", Integer, primary_key=True, index=True),
    Column("user_id", ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False),
    Column("scenario_id", ForeignKey("interview_scenarios.id", ondelete="CASCADE"), nullable=False),
    
    Column("start_time", DateTime(timezone=True), nullable=False),
    Column("end_time", DateTime(timezone=True), nullable=True),
    
    Column("total_questions", Integer, default=0, nullable=False),
    Column("is_finished", Boolean, default=False, nullable=False),
    
    Column(
        "status",
        Enum(
            InterviewSessionStatus,
            values_callable=lambda x: [e.value for e in x],
            name="interviewsessionstatus",
        ),
        nullable=False,
    ),
    
    # Cache fields
    Column("_scenario_description_cache", String(500), nullable=True),
    
    # Pause/Resume support
    Column("paused_at", DateTime(timezone=True), nullable=True),
    Column("resumed_at", DateTime(timezone=True), nullable=True),

    # Video recording for non-realtime interview
    Column("video_url", String(500), nullable=True),

    # Timestamps
    Column("created_at", DateTime(timezone=True), server_default=func.now(), nullable=False),
    Column("updated_at", DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False),
)

# Interview questions table
interview_questions = Table(
    "interview_questions",
    metadata,
    Column("id", Integer, primary_key=True, index=True),
    Column("session_id", ForeignKey("interview_sessions.id", ondelete="CASCADE"), index=True, nullable=False),
    Column("question_text", Text, nullable=False),
    Column("question_number", Integer, nullable=False),
    
    # Timestamps
    Column("created_at", DateTime(timezone=True), server_default=func.now(), nullable=False),
    Column("updated_at", DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False),
)
