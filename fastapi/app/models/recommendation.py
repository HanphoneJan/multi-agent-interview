"""Recommendation support tables (SQLAlchemy Core)."""
from sqlalchemy import (
    ARRAY,
    JSON,
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    Float,
    Index,
    Integer,
    String,
    Table,
    Text,
    func,
)

from app.models.base import metadata


user_events = Table(
    "user_events",
    metadata,
    Column("id", Integer, primary_key=True, index=True),
    Column("user_id", String(64), nullable=False),
    Column("resource_id", String(64), nullable=False),
    Column(
        "event_type",
        String(32),
        CheckConstraint(
            "event_type IN ('view', 'click', 'complete', 'rate', 'share')",
            name="ck_user_events_event_type",
        ),
        nullable=False,
    ),
    Column("session_id", String(64), nullable=True),
    Column("created_at", DateTime(timezone=True), server_default=func.now(), nullable=False),
    Column("metadata", JSON, nullable=True),
)

Index("idx_user_events_user_time", user_events.c.user_id, user_events.c.created_at.desc())
Index("idx_user_events_time", user_events.c.created_at.desc())
Index("idx_user_events_type_time", user_events.c.event_type, user_events.c.created_at)
Index("idx_user_events_resource", user_events.c.resource_id, user_events.c.created_at.desc())


user_profiles = Table(
    "user_profiles",
    metadata,
    Column("user_id", String(64), primary_key=True),
    Column(
        "preferred_difficulty",
        String(16),
        CheckConstraint(
            "preferred_difficulty IN ('easy', 'medium', 'hard')",
            name="ck_user_profiles_preferred_difficulty",
        ),
        nullable=True,
    ),
    Column("preferred_types", ARRAY(String(32)), nullable=True),
    Column("learning_stage", String(32), nullable=True),
    Column("total_views", Integer, nullable=False, server_default="0"),
    Column("total_completes", Integer, nullable=False, server_default="0"),
    Column("avg_rating", Float, nullable=False, server_default="0"),
    Column("created_at", DateTime(timezone=True), server_default=func.now(), nullable=False),
    Column("updated_at", DateTime(timezone=True), server_default=func.now(), nullable=False),
)

Index("idx_user_profiles_updated", user_profiles.c.updated_at)


item_similarities = Table(
    "item_similarities",
    metadata,
    Column("item_id", String(64), primary_key=True),
    Column("similar_item_id", String(64), primary_key=True),
    Column(
        "similarity_score",
        Float,
        CheckConstraint(
            "similarity_score >= 0 AND similarity_score <= 1",
            name="ck_item_similarities_score",
        ),
        nullable=False,
    ),
    Column("updated_at", DateTime(timezone=True), server_default=func.now(), nullable=False),
)

Index("idx_item_sim_score", item_similarities.c.item_id, item_similarities.c.similarity_score.desc())
Index("idx_item_sim_updated", item_similarities.c.updated_at)


user_offline_features = Table(
    "user_offline_features",
    metadata,
    Column("user_id", String(64), primary_key=True),
    Column("feature_vector", ARRAY(Float), nullable=True),
    Column("preferred_tags", ARRAY(String(64)), nullable=True),
    Column("updated_at", DateTime(timezone=True), server_default=func.now(), nullable=False),
)

Index("idx_user_offline_features_updated", user_offline_features.c.updated_at)


model_versions = Table(
    "model_versions",
    metadata,
    Column("id", Integer, primary_key=True, index=True),
    Column("model_type", String(32), nullable=False),
    Column("version", String(32), nullable=False),
    Column("file_path", String(500), nullable=False),
    Column("metrics", JSON, nullable=True),
    Column("is_active", Boolean, nullable=False, server_default="false"),
    Column("created_at", DateTime(timezone=True), server_default=func.now(), nullable=False),
    CheckConstraint("length(model_type) > 0", name="ck_model_versions_model_type_not_empty"),
    CheckConstraint("length(version) > 0", name="ck_model_versions_version_not_empty"),
)

Index("idx_model_versions_type", model_versions.c.model_type)
Index("idx_model_versions_active", model_versions.c.is_active)
