"""Idempotent database seeding from the archived Django snapshot."""
import asyncio
import os
import re
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Iterable

from sqlalchemy import text


PROJECT_ROOT = Path(__file__).resolve().parents[2]
FASTAPI_ROOT = PROJECT_ROOT / "fastapi"
ARCHIVE_SQL_PATH = PROJECT_ROOT / "archive" / "django" / "interview_2026-02-13_pgsql_data.sql"

sys.path.insert(0, str(FASTAPI_ROOT))

from app.core.security import get_password_hash  # noqa: E402
from app.database import async_session_factory  # noqa: E402


NULL_MARKER = r"\N"
VALID_RESOURCE_TYPES = {"question", "course", "video"}
VALID_DIFFICULTIES = {"easy", "medium", "hard"}
VALID_LEARNING_STAGES = {
    "FRESHMAN_1",
    "FRESHMAN_2",
    "SOPHOMORE_1",
    "SOPHOMORE_2",
    "JUNIOR_1",
    "JUNIOR_2",
    "SENIOR_1",
    "SENIOR_2",
    "GRADUATE_STUDENT",
    "JOB_SEEKER",
    "EMPLOYED",
    "OTHER",
}

IMPORTED_USER_PASSWORD = os.getenv("SEED_IMPORTED_USER_PASSWORD", "Seed123456")
STABLE_TEST_USERS = [
    {
        "username": "test_new",
        "email": "test_new@example.com",
        "password": "Test123456",
        "phone": "13800138001",
        "name": "Seed User New",
        "major": "Computer Science",
        "university": "Seed University",
        "gender": "O",
        "is_staff": False,
        "is_superuser": False,
    },
    {
        "username": "test_exp",
        "email": "test_exp@example.com",
        "password": "Test123456",
        "phone": "13800138002",
        "name": "Seed User Experienced",
        "major": "Software Engineering",
        "university": "Seed University",
        "gender": "O",
        "is_staff": False,
        "is_superuser": False,
    },
    {
        "username": "admin",
        "email": "admin@example.com",
        "password": "Admin123456",
        "phone": "13800138003",
        "name": "Seed Admin",
        "major": "Information Technology",
        "university": "Seed University",
        "gender": "O",
        "is_staff": True,
        "is_superuser": True,
    },
]


def load_copy_rows(sql_path: Path, table_name: str) -> list[list[str]]:
    content = sql_path.read_text(encoding="utf-8")
    pattern = re.compile(
        rf"^COPY public\.{re.escape(table_name)} \([^)]+\) FROM stdin;\r?\n(.*?)\r?\n\\\.$",
        re.MULTILINE | re.DOTALL,
    )
    match = pattern.search(content)
    if not match:
        return []

    rows: list[list[str]] = []
    for line in match.group(1).splitlines():
        if line.strip():
            rows.append(line.split("\t"))
    return rows


def normalize_null(value: str | None) -> str | None:
    if value in (None, "", NULL_MARKER):
        return None
    return value


def parse_timestamp(value: str | None, *, with_timezone: bool) -> datetime | None:
    raw = normalize_null(value)
    if raw is None:
        return None

    normalized = raw.replace("+08", "+08:00") if raw.endswith("+08") else raw
    parsed = datetime.fromisoformat(normalized)

    if with_timezone:
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=UTC)
        return parsed.astimezone(UTC)

    if parsed.tzinfo is None:
        return parsed
    return parsed.astimezone(UTC).replace(tzinfo=None)


def normalize_tags(raw_tags: str | None) -> list[str]:
    raw = normalize_null(raw_tags)
    if raw is None:
        return []

    trimmed = raw.strip("{}")
    if not trimmed:
        return []

    parts = [
        part.strip().strip('"').strip("'")
        for part in re.split(r"[、,，;/|]+", trimmed)
        if part.strip()
    ]
    seen: set[str] = set()
    normalized: list[str] = []
    for part in parts:
        if part not in seen:
            seen.add(part)
            normalized.append(part)
    return normalized


def should_import_legacy_user(row: list[str]) -> bool:
    username = normalize_null(row[4]) or ""
    email = normalize_null(row[10])
    phone = normalize_null(row[11])
    is_active = row[8] == "t"

    if not is_active:
        return False
    if not email and not phone:
        return False
    if username.startswith("wx_") and not phone:
        return False
    return True


def chunked(rows: list[dict], size: int = 200) -> Iterable[list[dict]]:
    for index in range(0, len(rows), size):
        yield rows[index:index + size]


async def seed_interview_scenarios() -> int:
    rows = load_copy_rows(ARCHIVE_SQL_PATH, "interview_manager_interviewscenario")
    payload = []
    for row in rows:
        payload.append(
            {
                "id": int(row[0]),
                "name": row[1],
                "technology_field": row[2],
                "description": row[3],
                "requirements": normalize_null(row[4]) or "",
                "is_realtime": row[5] == "t",
            }
        )

    if not payload:
        return 0

    stmt = text(
        """
        INSERT INTO interview_scenarios (
            id, name, technology_field, description, requirements, is_realtime, created_at, updated_at
        ) VALUES (
            :id, :name, :technology_field, :description, :requirements, :is_realtime, now(), now()
        )
        ON CONFLICT (id) DO UPDATE SET
            name = EXCLUDED.name,
            technology_field = EXCLUDED.technology_field,
            description = EXCLUDED.description,
            requirements = EXCLUDED.requirements,
            is_realtime = EXCLUDED.is_realtime,
            updated_at = now()
        """
    )

    async with async_session_factory() as session:
        for batch in chunked(payload):
            await session.execute(stmt, batch)
        await session.commit()

    return len(payload)


async def seed_resources() -> int:
    rows = load_copy_rows(ARCHIVE_SQL_PATH, "learning_manager_resource")
    payload = []
    for row in rows:
        resource_type = (normalize_null(row[2]) or "course").lower()
        if resource_type not in VALID_RESOURCE_TYPES:
            resource_type = "course"

        difficulty = normalize_null(row[6])
        difficulty = difficulty.lower() if difficulty else None
        if difficulty not in VALID_DIFFICULTIES:
            difficulty = "medium"

        payload.append(
            {
                "id": int(row[0]),
                "name": row[1],
                "resource_type": resource_type,
                "tags": normalize_tags(row[3]),
                "url": normalize_null(row[4]) or "",
                "duration_or_quantity": normalize_null(row[5]) or "",
                "difficulty": difficulty,
                "created_at": parse_timestamp(row[7], with_timezone=True) or datetime.now(UTC),
                "updated_at": parse_timestamp(row[8], with_timezone=True) or datetime.now(UTC),
            }
        )

    if not payload:
        return 0

    stmt = text(
        """
        INSERT INTO resources (
            id, name, resource_type, tags, url, duration_or_quantity, difficulty,
            views, completions, rating, rating_count, created_at, updated_at
        ) VALUES (
            :id, :name, :resource_type, :tags, :url, :duration_or_quantity, :difficulty,
            0, 0, 0, 0, :created_at, :updated_at
        )
        ON CONFLICT (id) DO UPDATE SET
            name = EXCLUDED.name,
            resource_type = EXCLUDED.resource_type,
            tags = EXCLUDED.tags,
            url = EXCLUDED.url,
            duration_or_quantity = EXCLUDED.duration_or_quantity,
            difficulty = EXCLUDED.difficulty,
            updated_at = EXCLUDED.updated_at
        """
    )

    async with async_session_factory() as session:
        for batch in chunked(payload):
            await session.execute(stmt, batch)
        await session.commit()

    return len(payload)


async def seed_lc_questions() -> int:
    rows = load_copy_rows(ARCHIVE_SQL_PATH, "learning_manager_question")
    payload = []
    for row in rows:
        difficulty = (normalize_null(row[7]) or "medium").lower()
        if difficulty not in VALID_DIFFICULTIES:
            difficulty = "medium"

        resource_id = normalize_null(row[4])
        if resource_id is None:
            continue

        payload.append(
            {
                "id": int(row[0]),
                "question_id": int(row[1]),
                "pass_rate": normalize_null(row[2]) or "",
                "solution_url": normalize_null(row[3]) or "",
                "resource_id": int(resource_id),
                "question_url": normalize_null(row[5]) or "",
                "name": normalize_null(row[6]) or "",
                "difficulty": difficulty,
            }
        )

    if not payload:
        return 0

    stmt = text(
        """
        INSERT INTO lc_questions (
            id, question_id, resource_id, name, pass_rate, solution_url, question_url,
            difficulty, created_at, updated_at
        ) VALUES (
            :id, :question_id, :resource_id, :name, :pass_rate, :solution_url, :question_url,
            :difficulty, now(), now()
        )
        ON CONFLICT (id) DO UPDATE SET
            question_id = EXCLUDED.question_id,
            resource_id = EXCLUDED.resource_id,
            name = EXCLUDED.name,
            pass_rate = EXCLUDED.pass_rate,
            solution_url = EXCLUDED.solution_url,
            question_url = EXCLUDED.question_url,
            difficulty = EXCLUDED.difficulty,
            updated_at = now()
        """
    )

    async with async_session_factory() as session:
        for batch in chunked(payload):
            await session.execute(stmt, batch)
        await session.commit()

    return len(payload)


async def seed_legacy_users() -> int:
    rows = load_copy_rows(ARCHIVE_SQL_PATH, "user_manager_user")
    default_password_hash = get_password_hash(IMPORTED_USER_PASSWORD)
    payload = []

    for row in rows:
        if not should_import_legacy_user(row):
            continue

        username = normalize_null(row[4]) or f"legacy_user_{row[0]}"
        email = normalize_null(row[10])
        phone = normalize_null(row[11])
        learning_stage = normalize_null(row[23])
        if learning_stage and learning_stage not in VALID_LEARNING_STAGES:
            learning_stage = "OTHER"

        payload.append(
            {
                "id": int(row[0]),
                "username": username,
                "email": email,
                "phone": phone,
                "hashed_password": default_password_hash,
                "name": normalize_null(row[14]) or normalize_null(row[5]) or username,
                "gender": normalize_null(row[15]) if normalize_null(row[15]) in {"M", "F", "O"} else "O",
                "age": int(row[22]) if normalize_null(row[22]) else None,
                "ethnicity": normalize_null(row[16]),
                "university": normalize_null(row[13]) or "",
                "major": normalize_null(row[12]) or "",
                "province": normalize_null(row[17]),
                "city": normalize_null(row[18]),
                "district": normalize_null(row[19]),
                "address": normalize_null(row[20]),
                "learning_stage": learning_stage,
                "avatar_url": normalize_null(row[26]),
                "wechat_open_id": normalize_null(row[24]),
                "wechat_union_id": normalize_null(row[25]),
                "is_active": row[8] == "t",
                "is_staff": row[7] == "t",
                "is_superuser": row[3] == "t",
                "is_email_verified": row[21] == "t",
                "last_login": parse_timestamp(row[2], with_timezone=False),
                "created_at": parse_timestamp(row[9], with_timezone=True) or datetime.now(UTC),
            }
        )

    if not payload:
        return 0

    stmt = text(
        """
        INSERT INTO users (
            id, username, email, phone, hashed_password, name, gender, age, ethnicity,
            university, major, province, city, district, address, learning_stage,
            avatar_url, wechat_open_id, wechat_union_id, is_active, is_staff,
            is_superuser, is_email_verified, last_login, created_at, updated_at
        ) VALUES (
            :id, :username, :email, :phone, :hashed_password, :name, :gender, :age, :ethnicity,
            :university, :major, :province, :city, :district, :address, :learning_stage,
            :avatar_url, :wechat_open_id, :wechat_union_id, :is_active, :is_staff,
            :is_superuser, :is_email_verified, :last_login, :created_at, now()
        )
        ON CONFLICT (id) DO UPDATE SET
            username = EXCLUDED.username,
            email = EXCLUDED.email,
            phone = EXCLUDED.phone,
            hashed_password = EXCLUDED.hashed_password,
            name = EXCLUDED.name,
            gender = EXCLUDED.gender,
            age = EXCLUDED.age,
            ethnicity = EXCLUDED.ethnicity,
            university = EXCLUDED.university,
            major = EXCLUDED.major,
            province = EXCLUDED.province,
            city = EXCLUDED.city,
            district = EXCLUDED.district,
            address = EXCLUDED.address,
            learning_stage = EXCLUDED.learning_stage,
            avatar_url = EXCLUDED.avatar_url,
            wechat_open_id = EXCLUDED.wechat_open_id,
            wechat_union_id = EXCLUDED.wechat_union_id,
            is_active = EXCLUDED.is_active,
            is_staff = EXCLUDED.is_staff,
            is_superuser = EXCLUDED.is_superuser,
            is_email_verified = EXCLUDED.is_email_verified,
            last_login = EXCLUDED.last_login,
            updated_at = now()
        """
    )

    async with async_session_factory() as session:
        for batch in chunked(payload):
            await session.execute(stmt, batch)
        await session.commit()

    return len(payload)


async def ensure_stable_test_users() -> int:
    payload = []
    for user in STABLE_TEST_USERS:
        payload.append(
            {
                **user,
                "hashed_password": get_password_hash(user["password"]),
            }
        )

    stmt = text(
        """
        INSERT INTO users (
            username, email, phone, hashed_password, name, gender, major, university,
            is_email_verified, is_active, is_staff, is_superuser, created_at, updated_at
        ) VALUES (
            :username, :email, :phone, :hashed_password, :name, :gender, :major, :university,
            true, true, :is_staff, :is_superuser, now(), now()
        )
        ON CONFLICT (email) DO UPDATE SET
            username = EXCLUDED.username,
            phone = EXCLUDED.phone,
            hashed_password = EXCLUDED.hashed_password,
            name = EXCLUDED.name,
            gender = EXCLUDED.gender,
            major = EXCLUDED.major,
            university = EXCLUDED.university,
            is_email_verified = true,
            is_active = true,
            is_staff = EXCLUDED.is_staff,
            is_superuser = EXCLUDED.is_superuser,
            updated_at = now()
        """
    )

    async with async_session_factory() as session:
        await session.execute(stmt, payload)
        await session.commit()

    return len(payload)


async def reset_sequences() -> None:
    tables = [
        "users",
        "interview_scenarios",
        "resources",
        "lc_questions",
        "user_events",
        "model_versions",
    ]

    async with async_session_factory() as session:
        for table_name in tables:
            await session.execute(
                text(
                    f"""
                    SELECT setval(
                        pg_get_serial_sequence('{table_name}', 'id'),
                        COALESCE((SELECT MAX(id) FROM {table_name}), 1),
                        (SELECT COUNT(*) > 0 FROM {table_name})
                    )
                    """
                )
            )
        await session.commit()


async def main() -> None:
    if not ARCHIVE_SQL_PATH.exists():
        raise FileNotFoundError(f"Archive SQL not found: {ARCHIVE_SQL_PATH}")

    scenario_count = await seed_interview_scenarios()
    resource_count = await seed_resources()
    question_count = await seed_lc_questions()
    legacy_user_count = await seed_legacy_users()
    await reset_sequences()
    stable_user_count = await ensure_stable_test_users()
    await reset_sequences()

    print("Database seed complete")
    print(f"- interview_scenarios: {scenario_count}")
    print(f"- resources: {resource_count}")
    print(f"- lc_questions: {question_count}")
    print(f"- legacy_users: {legacy_user_count}")
    print(f"- stable_test_users: {stable_user_count}")
    print(f"- imported legacy user password: {IMPORTED_USER_PASSWORD}")
    print("- test_new@example.com / Test123456")
    print("- test_exp@example.com / Test123456")
    print("- admin@example.com / Admin123456")


if __name__ == "__main__":
    asyncio.run(main())
