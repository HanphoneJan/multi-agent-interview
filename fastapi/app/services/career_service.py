"""Career service layer for database operations"""
from typing import Optional, List
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.career import (
    major_categories, major_subcategories, majors, major_career_mappings,
    career_categories, careers, career_skills, career_skill_mappings,
    job_platforms, external_jobs,
)


# ============ Major Services ============

async def get_major_categories(db: AsyncSession) -> List[dict]:
    """Get all major categories"""
    result = await db.execute(
        select(major_categories).order_by(major_categories.c.code)
    )
    return [dict(row._mapping) for row in result]


async def get_major_category_by_code(db: AsyncSession, code: str) -> Optional[dict]:
    """Get major category by code"""
    result = await db.execute(
        select(major_categories).where(major_categories.c.code == code)
    )
    row = result.first()
    return dict(row._mapping) if row else None


async def get_major_subcategories(
    db: AsyncSession,
    category_id: Optional[int] = None
) -> List[dict]:
    """Get major subcategories, optionally filtered by category"""
    query = select(major_subcategories)
    if category_id:
        query = query.where(major_subcategories.c.category_id == category_id)
    query = query.order_by(major_subcategories.c.code)
    result = await db.execute(query)
    return [dict(row._mapping) for row in result]


async def get_majors(
    db: AsyncSession,
    subcategory_id: Optional[int] = None,
    keyword: Optional[str] = None,
    limit: int = 100,
    offset: int = 0
) -> List[dict]:
    """Get majors with optional filters"""
    query = select(majors)

    if subcategory_id:
        query = query.where(majors.c.subcategory_id == subcategory_id)

    if keyword:
        search = f"%{keyword}%"
        # For PostgreSQL array, we use array_to_string to search in keywords
        from sqlalchemy import text
        query = query.where(
            or_(
                majors.c.name.ilike(search),
                majors.c.code.ilike(search),
                text("array_to_string(majors.keywords, ',') ILIKE :search").bindparams(search=search)
            )
        )

    query = query.order_by(majors.c.code).limit(limit).offset(offset)
    result = await db.execute(query)
    return [dict(row._mapping) for row in result]


async def get_major_by_id(db: AsyncSession, major_id: int) -> Optional[dict]:
    """Get major by ID"""
    result = await db.execute(
        select(majors).where(majors.c.id == major_id)
    )
    row = result.first()
    return dict(row._mapping) if row else None


async def get_major_by_code(db: AsyncSession, code: str) -> Optional[dict]:
    """Get major by code"""
    result = await db.execute(
        select(majors).where(majors.c.code == code)
    )
    row = result.first()
    return dict(row._mapping) if row else None


async def search_majors(db: AsyncSession, query_str: str, limit: int = 10) -> List[dict]:
    """Search majors by keyword"""
    search = f"%{query_str}%"
    # For PostgreSQL array, we use array_to_string to search in keywords
    from sqlalchemy import text
    result = await db.execute(
        select(majors).where(
            or_(
                majors.c.name.ilike(search),
                majors.c.code.ilike(search),
                text("array_to_string(majors.keywords, ',') ILIKE :search").bindparams(search=search)
            )
        ).limit(limit)
    )
    return [dict(row._mapping) for row in result]


# ============ Career Services ============

async def get_career_categories(db: AsyncSession) -> List[dict]:
    """Get all career categories"""
    result = await db.execute(
        select(career_categories).order_by(career_categories.c.code)
    )
    return [dict(row._mapping) for row in result]


async def get_careers(
    db: AsyncSession,
    category_id: Optional[int] = None,
    keyword: Optional[str] = None,
    limit: int = 100,
    offset: int = 0
) -> List[dict]:
    """Get careers with optional filters"""
    query = select(careers).where(careers.c.is_active == True)

    if category_id:
        query = query.where(careers.c.category_id == category_id)

    if keyword:
        search = f"%{keyword}%"
        # For PostgreSQL array, we use array_to_string to search in aliases
        from sqlalchemy import text
        query = query.where(
            or_(
                careers.c.name.ilike(search),
                text("array_to_string(careers.aliases, ',') ILIKE :search").bindparams(search=search),
                careers.c.description.ilike(search)
            )
        )

    query = query.order_by(careers.c.name).limit(limit).offset(offset)
    result = await db.execute(query)
    return [dict(row._mapping) for row in result]


async def get_career_by_id(db: AsyncSession, career_id: int) -> Optional[dict]:
    """Get career by ID"""
    result = await db.execute(
        select(careers).where(
            and_(careers.c.id == career_id, careers.c.is_active == True)
        )
    )
    row = result.first()
    return dict(row._mapping) if row else None


async def get_career_by_code(db: AsyncSession, code: str) -> Optional[dict]:
    """Get career by code"""
    result = await db.execute(
        select(careers).where(
            and_(careers.c.code == code, careers.c.is_active == True)
        )
    )
    row = result.first()
    return dict(row._mapping) if row else None


async def get_career_skills(db: AsyncSession, career_id: int) -> List[dict]:
    """Get skills for a career"""
    result = await db.execute(
        select(
            career_skills.c.id,
            career_skills.c.name,
            career_skills.c.category,
            career_skill_mappings.c.importance,
            career_skill_mappings.c.is_required
        )
        .join(
            career_skill_mappings,
            career_skills.c.id == career_skill_mappings.c.skill_id
        )
        .where(career_skill_mappings.c.career_id == career_id)
        .order_by(career_skill_mappings.c.importance.desc())
    )
    return [dict(row._mapping) for row in result]


async def search_careers(db: AsyncSession, query_str: str, limit: int = 10) -> List[dict]:
    """Search careers by keyword"""
    if not query_str or not query_str.strip():
        return []

    search = f"%{query_str}%"
    from sqlalchemy import text
    result = await db.execute(
        select(careers).where(
            and_(
                careers.c.is_active == True,
                or_(
                    careers.c.name.ilike(search),
                    text("array_to_string(careers.aliases, ',') ILIKE :search").bindparams(search=search),
                    careers.c.description.ilike(search)
                )
            )
        ).limit(limit)
    )
    return [dict(row._mapping) for row in result]


# ============ Major-Career Mapping Services ============

async def get_careers_by_major(
    db: AsyncSession,
    major_id: int,
    min_match_score: int = 0
) -> List[dict]:
    """Get careers related to a major"""
    result = await db.execute(
        select(
            careers,
            major_career_mappings.c.match_score,
            major_career_mappings.c.is_primary
        )
        .join(
            major_career_mappings,
            careers.c.id == major_career_mappings.c.career_id
        )
        .where(
            and_(
                major_career_mappings.c.major_id == major_id,
                major_career_mappings.c.match_score >= min_match_score,
                careers.c.is_active == True
            )
        )
        .order_by(major_career_mappings.c.match_score.desc())
    )

    careers_list = []
    for row in result:
        data = dict(row._mapping)
        career_data = {k: v for k, v in data.items() if not k.startswith('match_') and k != 'is_primary'}
        career_data['match_score'] = data.get('match_score', 0)
        career_data['is_primary'] = data.get('is_primary', False)
        careers_list.append(career_data)

    return careers_list


async def get_majors_by_career(
    db: AsyncSession,
    career_id: int,
    min_match_score: int = 0
) -> List[dict]:
    """Get majors related to a career"""
    result = await db.execute(
        select(
            majors,
            major_career_mappings.c.match_score,
            major_career_mappings.c.is_primary
        )
        .join(
            major_career_mappings,
            majors.c.id == major_career_mappings.c.major_id
        )
        .where(
            and_(
                major_career_mappings.c.career_id == career_id,
                major_career_mappings.c.match_score >= min_match_score
            )
        )
        .order_by(major_career_mappings.c.match_score.desc())
    )

    majors_list = []
    for row in result:
        data = dict(row._mapping)
        major_data = {k: v for k, v in data.items() if not k.startswith('match_') and k != 'is_primary'}
        major_data['match_score'] = data.get('match_score', 0)
        major_data['is_primary'] = data.get('is_primary', False)
        majors_list.append(major_data)

    return majors_list


async def get_career_suggestions_by_major(
    db: AsyncSession,
    major_name: str,
    limit: int = 4
) -> List[dict]:
    """Get career suggestions based on major name (fuzzy match)"""
    major_name = (major_name or "").strip()
    if not major_name:
        return []

    # First try to find exact match
    major = await get_major_by_code(db, major_name)

    if not major:
        # Try fuzzy search
        majors_list = await search_majors(db, major_name, limit=1)
        if majors_list:
            major = majors_list[0]

    if major:
        return await get_careers_by_major(db, major['id'])

    # Fallback: search careers by keyword
    return await search_careers(db, major_name, limit=limit)


# ============ Job Platform Services ============

async def get_job_platforms(db: AsyncSession, only_active: bool = True) -> List[dict]:
    """Get job platforms"""
    query = select(job_platforms)
    if only_active:
        query = query.where(job_platforms.c.is_active == True)
    result = await db.execute(query)
    return [dict(row._mapping) for row in result]


async def get_job_platform_by_code(db: AsyncSession, code: str) -> Optional[dict]:
    """Get job platform by code"""
    result = await db.execute(
        select(job_platforms).where(job_platforms.c.code == code)
    )
    row = result.first()
    return dict(row._mapping) if row else None


# ============ External Job Services ============

async def search_external_jobs(
    db: AsyncSession,
    keyword: Optional[str] = None,
    city: Optional[str] = None,
    career_id: Optional[int] = None,
    salary_min: Optional[int] = None,
    salary_max: Optional[int] = None,
    education: Optional[str] = None,
    limit: int = 20,
    offset: int = 0
) -> tuple[List[dict], int]:
    """Search external jobs with filters"""
    query = select(external_jobs).where(external_jobs.c.is_active == True)
    count_query = select(func.count()).select_from(external_jobs).where(external_jobs.c.is_active == True)

    if keyword:
        search = f"%{keyword}%"
        keyword_filter = or_(
            external_jobs.c.title.ilike(search),
            external_jobs.c.job_description.ilike(search),
            external_jobs.c.skills_required.ilike(search)
        )
        query = query.where(keyword_filter)
        count_query = count_query.where(keyword_filter)

    if city:
        city_filter = or_(
            external_jobs.c.city == city,
            external_jobs.c.city.ilike(f"%{city}%")
        )
        query = query.where(city_filter)
        count_query = count_query.where(city_filter)

    if career_id:
        # This would need job_career_mappings table
        pass

    if salary_min:
        query = query.where(external_jobs.c.salary_min >= salary_min)
        count_query = count_query.where(external_jobs.c.salary_min >= salary_min)

    if salary_max:
        query = query.where(external_jobs.c.salary_max <= salary_max)
        count_query = count_query.where(external_jobs.c.salary_max <= salary_max)

    if education:
        query = query.where(external_jobs.c.education_requirement.ilike(f"%{education}%"))
        count_query = count_query.where(external_jobs.c.education_requirement.ilike(f"%{education}%"))

    # Get total count
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Get results
    query = query.order_by(external_jobs.c.publish_date.desc()).limit(limit).offset(offset)
    result = await db.execute(query)
    jobs = [dict(row._mapping) for row in result]

    return jobs, total


async def get_external_job_by_id(db: AsyncSession, job_id: int) -> Optional[dict]:
    """Get external job by ID"""
    result = await db.execute(
        select(external_jobs).where(external_jobs.c.id == job_id)
    )
    row = result.first()
    return dict(row._mapping) if row else None
