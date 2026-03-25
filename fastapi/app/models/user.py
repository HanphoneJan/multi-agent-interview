"""User tables (SQLAlchemy Core)"""
from sqlalchemy import Table, Column, Integer, String, Text, Boolean, DateTime, JSON, Enum as SQLEnum
from app.models.base import metadata

# Users table
users = Table(
    "users",
    metadata,
    Column("id", Integer, primary_key=True, index=True),

    # Authentication fields
    Column("username", String(150), unique=True, index=True, nullable=False),
    Column("email", String(255), unique=True, index=True, nullable=True),
    Column("hashed_password", String(255), nullable=True),

    # WeChat fields
    Column("wechat_open_id", String(28), unique=True, nullable=True, index=True),
    Column("wechat_union_id", String(29), unique=True, nullable=True, index=True),

    # Phone
    Column("phone", String(11), unique=True, nullable=True, index=True),

    # Profile
    Column("name", String(40), default="", nullable=False),
    Column("avatar_url", String(500), nullable=True),
    Column("gender", SQLEnum("M", "F", "O", name="gender"), default="O", nullable=False),
    Column("age", Integer, nullable=True),

    # Education
    Column("major", String(100), default="", nullable=False),
    Column("university", String(100), default="", nullable=False),
    Column("learning_stage", SQLEnum(
        "FRESHMAN_1", "FRESHMAN_2", "SOPHOMORE_1", "SOPHOMORE_2",
        "JUNIOR_1", "JUNIOR_2", "SENIOR_1", "SENIOR_2",
        "GRADUATE_STUDENT", "JOB_SEEKER", "EMPLOYED", "OTHER",
        name="learningstage"
    ), nullable=True),

    # Location
    Column("province", String(50), nullable=True),
    Column("city", String(50), nullable=True),
    Column("district", String(50), nullable=True),
    Column("address", String(200), nullable=True),

    # Personal info
    Column("ethnicity", String(50), nullable=True),

    # Email verification
    Column("is_email_verified", Boolean, default=True, nullable=False),

    # Django compatibility fields
    Column("is_active", Boolean, default=True, nullable=False),
    Column("is_staff", Boolean, default=False, nullable=False),
    Column("is_superuser", Boolean, default=False, nullable=False),
    Column("last_login", DateTime, nullable=True),

    # Interviewer customization settings (JSON)
    Column("interviewer_settings", JSON, nullable=True),

    # Timestamps
    Column("created_at", DateTime(timezone=True), server_default="now()", nullable=False),
    Column("updated_at", DateTime(timezone=True), server_default="now()", nullable=False),
)
