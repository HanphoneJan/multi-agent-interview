"""Add recommendation support tables

Revision ID: 1f5d8d2b6e4a
Revises: 79c3cf47db92
Create Date: 2026-03-20 12:00:00.000000+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "1f5d8d2b6e4a"
down_revision: Union[str, None] = "79c3cf47db92"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "user_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.String(length=64), nullable=False),
        sa.Column("resource_id", sa.String(length=64), nullable=False),
        sa.Column("event_type", sa.String(length=32), nullable=False),
        sa.Column("session_id", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.CheckConstraint(
            "event_type IN ('view', 'click', 'complete', 'rate', 'share')",
            name="ck_user_events_event_type",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("user_events", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_user_events_id"), ["id"], unique=False)
        batch_op.create_index("idx_user_events_resource", ["resource_id", "created_at"], unique=False)
        batch_op.create_index("idx_user_events_time", ["created_at"], unique=False)
        batch_op.create_index("idx_user_events_type_time", ["event_type", "created_at"], unique=False)
        batch_op.create_index("idx_user_events_user_time", ["user_id", "created_at"], unique=False)

    op.create_table(
        "user_profiles",
        sa.Column("user_id", sa.String(length=64), nullable=False),
        sa.Column("preferred_difficulty", sa.String(length=16), nullable=True),
        sa.Column("preferred_types", sa.ARRAY(sa.String(length=32)), nullable=True),
        sa.Column("learning_stage", sa.String(length=32), nullable=True),
        sa.Column("total_views", sa.Integer(), server_default="0", nullable=False),
        sa.Column("total_completes", sa.Integer(), server_default="0", nullable=False),
        sa.Column("avg_rating", sa.Float(), server_default="0", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint(
            "preferred_difficulty IN ('easy', 'medium', 'hard')",
            name="ck_user_profiles_preferred_difficulty",
        ),
        sa.PrimaryKeyConstraint("user_id"),
    )
    with op.batch_alter_table("user_profiles", schema=None) as batch_op:
        batch_op.create_index("idx_user_profiles_updated", ["updated_at"], unique=False)

    op.create_table(
        "item_similarities",
        sa.Column("item_id", sa.String(length=64), nullable=False),
        sa.Column("similar_item_id", sa.String(length=64), nullable=False),
        sa.Column("similarity_score", sa.Float(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint(
            "similarity_score >= 0 AND similarity_score <= 1",
            name="ck_item_similarities_score",
        ),
        sa.PrimaryKeyConstraint("item_id", "similar_item_id"),
    )
    with op.batch_alter_table("item_similarities", schema=None) as batch_op:
        batch_op.create_index("idx_item_sim_score", ["item_id", "similarity_score"], unique=False)
        batch_op.create_index("idx_item_sim_updated", ["updated_at"], unique=False)

    op.create_table(
        "user_offline_features",
        sa.Column("user_id", sa.String(length=64), nullable=False),
        sa.Column("feature_vector", sa.ARRAY(sa.Float()), nullable=True),
        sa.Column("preferred_tags", sa.ARRAY(sa.String(length=64)), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("user_id"),
    )
    with op.batch_alter_table("user_offline_features", schema=None) as batch_op:
        batch_op.create_index("idx_user_offline_features_updated", ["updated_at"], unique=False)

    op.create_table(
        "model_versions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("model_type", sa.String(length=32), nullable=False),
        sa.Column("version", sa.String(length=32), nullable=False),
        sa.Column("file_path", sa.String(length=500), nullable=False),
        sa.Column("metrics", sa.JSON(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("length(model_type) > 0", name="ck_model_versions_model_type_not_empty"),
        sa.CheckConstraint("length(version) > 0", name="ck_model_versions_version_not_empty"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("model_type", "version", name="uq_model_versions_model_type_version"),
    )
    with op.batch_alter_table("model_versions", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_model_versions_id"), ["id"], unique=False)
        batch_op.create_index("idx_model_versions_active", ["is_active"], unique=False)
        batch_op.create_index("idx_model_versions_type", ["model_type"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("model_versions", schema=None) as batch_op:
        batch_op.drop_index("idx_model_versions_type")
        batch_op.drop_index("idx_model_versions_active")
        batch_op.drop_index(batch_op.f("ix_model_versions_id"))
    op.drop_table("model_versions")

    with op.batch_alter_table("user_offline_features", schema=None) as batch_op:
        batch_op.drop_index("idx_user_offline_features_updated")
    op.drop_table("user_offline_features")

    with op.batch_alter_table("item_similarities", schema=None) as batch_op:
        batch_op.drop_index("idx_item_sim_updated")
        batch_op.drop_index("idx_item_sim_score")
    op.drop_table("item_similarities")

    with op.batch_alter_table("user_profiles", schema=None) as batch_op:
        batch_op.drop_index("idx_user_profiles_updated")
    op.drop_table("user_profiles")

    with op.batch_alter_table("user_events", schema=None) as batch_op:
        batch_op.drop_index("idx_user_events_user_time")
        batch_op.drop_index("idx_user_events_type_time")
        batch_op.drop_index("idx_user_events_time")
        batch_op.drop_index("idx_user_events_resource")
        batch_op.drop_index(batch_op.f("ix_user_events_id"))
    op.drop_table("user_events")
