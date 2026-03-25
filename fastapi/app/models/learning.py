"""Learning resource tables (SQLAlchemy Core)"""
from sqlalchemy import Table, Column, Integer, String, Float, DateTime, ForeignKey, UniqueConstraint, Enum, func, ARRAY
from app.models.base import metadata
from app.core.constants import ResourceType, Difficulty

# Helper function to get enum values instead of names
values_callable = lambda x: [e.value for e in x]

# Resources table
resources = Table(
    "resources",
    metadata,
    Column("id", Integer, primary_key=True, index=True),
    Column("name", String(200), nullable=False),
    Column("resource_type", Enum(ResourceType, values_callable=values_callable), index=True, nullable=False),
    Column("tags", ARRAY(String(64)), nullable=False, default=list),
    Column("url", String(500), nullable=False),
    Column("duration_or_quantity", String(50), nullable=False),
    Column("difficulty", Enum(Difficulty, values_callable=values_callable), nullable=True),
    
    # Statistics
    Column("views", Integer, default=0, nullable=False),
    Column("completions", Integer, default=0, nullable=False),
    Column("rating", Float, default=0.0, nullable=False),
    Column("rating_count", Integer, default=0, nullable=False),
    
    # Timestamps
    Column("created_at", DateTime(timezone=True), server_default=func.now(), nullable=False),
    Column("updated_at", DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False),
)

# LeetCode Questions table
lc_questions = Table(
    "lc_questions",
    metadata,
    Column("id", Integer, primary_key=True, index=True),
    Column("question_id", Integer, nullable=False),
    Column("resource_id", ForeignKey("resources.id", ondelete="CASCADE"), nullable=False),
    
    Column("name", String(200), default="", nullable=False),
    Column("pass_rate", String(20), nullable=False),
    Column("solution_url", String(500), default="", nullable=False),
    Column("question_url", String(500), default="", nullable=False),
    Column("difficulty", Enum(Difficulty, values_callable=values_callable), nullable=False),
    
    # Timestamps
    Column("created_at", DateTime(timezone=True), server_default=func.now(), nullable=False),
    Column("updated_at", DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False),
    
    # Unique constraint
    UniqueConstraint('question_id', 'resource_id', name='uq_lc_question_resource'),
)

# User resource interactions table
user_resource_interactions = Table(
    "user_resource_interactions",
    metadata,
    Column("id", Integer, primary_key=True, index=True),
    Column("user_id", ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False),
    Column("resource_id", ForeignKey("resources.id", ondelete="CASCADE"), index=True, nullable=False),
    
    Column("interaction_type", String(20), index=True, nullable=False),  # view, complete, rate
    Column("value", Float, default=0.0, nullable=False),
    
    # Timestamps
    Column("created_at", DateTime(timezone=True), server_default=func.now(), nullable=False),
    Column("updated_at", DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False),
)
