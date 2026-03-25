"""Evaluation tables (SQLAlchemy Core)"""
from sqlalchemy import Table, Column, Integer, String, Text, Float, DateTime, ForeignKey, UniqueConstraint
from app.models.base import metadata

# Response metadata table
response_metadata = Table(
    "response_metadata",
    metadata,
    Column("id", Integer, primary_key=True, index=True),
    Column("question_id", ForeignKey("interview_questions.id", ondelete="CASCADE"), unique=True, nullable=False),
    
    Column("audio_duration", Float, nullable=True),
    Column("video_duration", Float, nullable=True),
    Column("upload_timestamp", DateTime, nullable=False),
    
    # Timestamps
    Column("created_at", DateTime(timezone=True), server_default="now()", nullable=False),
    Column("updated_at", DateTime(timezone=True), server_default="now()", onupdate="now()", nullable=False),
)

# Response analysis table
response_analysis = Table(
    "response_analysis",
    metadata,
    Column("id", Integer, primary_key=True, index=True),
    Column("metadata_id", ForeignKey("response_metadata.id", ondelete="CASCADE"), unique=True, nullable=False),
    
    Column("speech_text", Text, nullable=False),
    Column("facial_expression", Text, default="", nullable=False),
    Column("body_language", Text, default="", nullable=False),
    Column("analysis_timestamp", DateTime, nullable=False),
    
    # Timestamps
    Column("created_at", DateTime(timezone=True), server_default="now()", nullable=False),
    Column("updated_at", DateTime(timezone=True), server_default="now()", onupdate="now()", nullable=False),
)

# Answer evaluations table
answer_evaluations = Table(
    "answer_evaluations",
    metadata,
    Column("id", Integer, primary_key=True, index=True),
    Column("question_id", ForeignKey("interview_questions.id", ondelete="CASCADE"), nullable=False),
    Column("analysis_id", ForeignKey("response_analysis.id", ondelete="CASCADE"), nullable=False),
    
    Column("evaluation_text", Text, nullable=False),
    Column("score", Float, default=0.0, nullable=False),
    Column("evaluated_at", DateTime, nullable=False),
    
    # Timestamps
    Column("created_at", DateTime(timezone=True), server_default="now()", nullable=False),
    Column("updated_at", DateTime(timezone=True), server_default="now()", onupdate="now()", nullable=False),
)

# Resume evaluations table
resume_evaluations = Table(
    "resume_evaluations",
    metadata,
    Column("id", Integer, primary_key=True, index=True),
    Column("user_id", ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False),
    
    Column("resume_score", String(100), default='0', nullable=False),
    Column("resume_summary", Text, nullable=True),
    
    # Timestamps
    Column("created_at", DateTime(timezone=True), server_default="now()", nullable=False),
    Column("updated_at", DateTime(timezone=True), server_default="now()", onupdate="now()", nullable=False),
)

# Overall interview evaluations table
overall_interview_evaluations = Table(
    "overall_interview_evaluations",
    metadata,
    Column("id", Integer, primary_key=True, index=True),
    Column("session_id", ForeignKey("interview_sessions.id", ondelete="CASCADE"), unique=True, nullable=False),
    Column("user_id", ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False),
    
    Column("overall_evaluation", Text, nullable=False),
    Column("help", Text, nullable=False),
    Column("recommendation", Text, default="", nullable=False),
    
    # Score fields (stored as integers for numeric calculations)
    Column("overall_score", Integer, default=0, nullable=False),
    Column("professional_knowledge", Integer, default=0, nullable=False),
    Column("skill_match", Integer, default=0, nullable=False),
    Column("language_expression", Integer, default=0, nullable=False),
    Column("logical_thinking", Integer, default=0, nullable=False),
    Column("stress_response", Integer, default=0, nullable=False),
    Column("personality", Integer, default=0, nullable=False),
    Column("motivation", Integer, default=0, nullable=False),
    Column("value", Integer, default=0, nullable=False),
    
    # Timestamps
    Column("created_at", DateTime(timezone=True), server_default="now()", nullable=False),
    Column("updated_at", DateTime(timezone=True), server_default="now()", onupdate="now()", nullable=False),
)
