"""Career and major API endpoints"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user_optional, get_current_user
from app.schemas.career import (
    MajorCategoryResponse,
    MajorSubcategoryResponse,
    MajorResponse,
    MajorWithCareersResponse,
    CareerCategoryResponse,
    CareerResponse,
    CareerDetailResponse,
    CareerMatchResponse,
    JobPlatformResponse,
    ExternalJobResponse,
    JobSearchResponse,
    JobSearchQuery,
)
from app.schemas.common import PaginatedResponse
from app.services import career_service

router = APIRouter(prefix="/career", tags=["career"])


# ============ Major Endpoints ============

@router.get("/majors/categories", response_model=list[MajorCategoryResponse])
async def list_major_categories(
    db: AsyncSession = Depends(get_db)
):
    """Get all major categories (e.g., 哲学, 经济学, 工学)"""
    categories = await career_service.get_major_categories(db)
    return categories


@router.get("/majors/subcategories", response_model=list[MajorSubcategoryResponse])
async def list_major_subcategories(
    category_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db)
):
    """Get major subcategories, optionally filtered by category"""
    subcategories = await career_service.get_major_subcategories(db, category_id)
    return subcategories


@router.get("/majors", response_model=PaginatedResponse[MajorResponse])
async def list_majors(
    subcategory_id: Optional[int] = None,
    keyword: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """Get majors with optional filters"""
    offset = (page - 1) * page_size
    majors = await career_service.get_majors(
        db, subcategory_id=subcategory_id, keyword=keyword,
        limit=page_size, offset=offset
    )

    # Get total count (simplified, could be optimized)
    all_majors = await career_service.get_majors(
        db, subcategory_id=subcategory_id, keyword=keyword, limit=10000
    )
    total = len(all_majors)

    return {
        "items": majors,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size
    }


@router.get("/majors/search", response_model=list[MajorResponse])
async def search_majors(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db)
):
    """Search majors by keyword"""
    majors = await career_service.search_majors(db, q, limit)
    return majors


@router.get("/majors/{major_id}", response_model=MajorWithCareersResponse)
async def get_major(
    major_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get major details by ID with related careers"""
    major = await career_service.get_major_by_id(db, major_id)
    if not major:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Major not found"
        )

    # Get related careers
    related_careers = await career_service.get_careers_by_major(db, major_id)
    major["related_careers"] = [
        CareerMatchResponse(
            career=career,
            match_score=career.get("match_score", 80),
            is_primary=career.get("is_primary", False)
        ) for career in related_careers
    ]

    return major


@router.get("/majors/{major_id}/careers", response_model=list[CareerMatchResponse])
async def get_major_careers(
    major_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get careers related to a major"""
    major = await career_service.get_major_by_id(db, major_id)
    if not major:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Major not found"
        )

    careers = await career_service.get_careers_by_major(db, major_id)
    return [
        CareerMatchResponse(
            career=career,
            match_score=career.get("match_score", 80),
            is_primary=career.get("is_primary", False)
        ) for career in careers
    ]


# ============ Career Endpoints ============

@router.get("/categories", response_model=list[CareerCategoryResponse])
async def list_career_categories(
    db: AsyncSession = Depends(get_db)
):
    """Get all career categories"""
    categories = await career_service.get_career_categories(db)
    return categories


@router.get("/jobs", response_model=PaginatedResponse[CareerResponse])
async def list_careers(
    category_id: Optional[int] = None,
    keyword: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """Get careers with optional filters"""
    offset = (page - 1) * page_size
    career_list = await career_service.get_careers(
        db, category_id=category_id, keyword=keyword,
        limit=page_size, offset=offset
    )

    # Get total count
    all_careers = await career_service.get_careers(
        db, category_id=category_id, keyword=keyword, limit=10000
    )
    total = len(all_careers)

    return {
        "items": career_list,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size
    }


@router.get("/jobs/search", response_model=list[CareerResponse])
async def search_careers(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db)
):
    """Search careers by keyword"""
    career_list = await career_service.search_careers(db, q, limit)
    return career_list


@router.get("/jobs/{career_id}", response_model=CareerDetailResponse)
async def get_career(
    career_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get career details by ID with skills and related majors"""
    career = await career_service.get_career_by_id(db, career_id)
    if not career:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Career not found"
        )

    # Get skills
    skills = await career_service.get_career_skills(db, career_id)
    career["skills"] = skills

    # Get related majors
    related_majors = await career_service.get_majors_by_career(db, career_id)
    from app.schemas.career import MajorMatchResponse
    career["related_majors"] = [
        MajorMatchResponse(
            major=major,
            match_score=major.get("match_score", 80),
            is_primary=major.get("is_primary", False)
        ) for major in related_majors
    ]

    return career


@router.get("/jobs/{career_id}/majors", response_model=list[dict])
async def get_career_majors(
    career_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get majors related to a career"""
    career = await career_service.get_career_by_id(db, career_id)
    if not career:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Career not found"
        )

    majors = await career_service.get_majors_by_career(db, career_id)
    return majors


# ============ Job Platform Endpoints ============

@router.get("/platforms", response_model=list[JobPlatformResponse])
async def list_job_platforms(
    db: AsyncSession = Depends(get_db)
):
    """Get all job platforms"""
    platforms = await career_service.get_job_platforms(db)
    return platforms


# ============ Career Salary Statistics ============

@router.get("/jobs/{career_id}/salary-stats")
async def get_career_salary_statistics(
    career_id: int,
    city: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    获取职业薪资统计

    基于外部岗位数据计算该职业的薪资水平
    """
    # Verify career exists
    career = await career_service.get_career_by_id(db, career_id)
    if not career:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Career not found"
        )

    from app.services.job_platform_service import job_platform_service

    stats = await job_platform_service.get_salary_statistics(
        db, career_id, city
    )

    return {
        "career_id": career_id,
        "career_name": career["name"],
        "city": city,
        **stats
    }


# ============ External Job Endpoints ============

@router.get("/external-jobs/search")
async def search_external_jobs(
    keyword: str = Query(..., min_length=1, description="Search keyword"),
    city: Optional[str] = Query(None, description="City name"),
    platforms: Optional[str] = Query(None, description="Comma-separated platform codes (e.g., zhaopin,boss)"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """
    Search external jobs from multiple platforms

    Supports searching both local cached jobs and external platforms.
    """
    from app.services.job_platform_service import job_platform_service

    # Parse platforms
    platform_list = None
    if platforms:
        platform_list = [p.strip() for p in platforms.split(",")]

    jobs = await job_platform_service.search_jobs(
        db,
        keyword=keyword,
        city=city,
        platforms=platform_list,
        page=page,
        page_size=page_size
    )

    return {
        "items": jobs,
        "total": len(jobs),
        "page": page,
        "page_size": page_size,
        "keyword": keyword,
        "city": city
    }


@router.post("/external-jobs/sync")
async def sync_external_jobs(
    platform: str = Query(..., description="Platform code (e.g., zhaopin)"),
    keyword: Optional[str] = Query(None, description="Keyword to sync, or sync default keywords if not provided"),
    max_jobs: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db)
):
    """
    Sync jobs from external platform to local database

    This endpoint triggers a background sync operation.
    Requires admin privileges in production.
    """
    from app.services.job_platform_service import job_platform_service

    try:
        synced_count = await job_platform_service.sync_jobs(
            db, platform, keyword, max_jobs
        )
        return {
            "success": True,
            "platform": platform,
            "synced_count": synced_count,
            "keyword": keyword
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Sync failed: {str(e)}"
        )


@router.get("/external-jobs/{job_id}", response_model=ExternalJobResponse)
async def get_external_job(
    job_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get external job details by ID"""
    job = await career_service.get_external_job_by_id(db, job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    return job


# ============ Career Suggestion Endpoints ============

@router.get("/suggestions", response_model=list[dict])
async def get_career_suggestions(
    major: Optional[str] = None,
    limit: int = Query(4, ge=1, le=10),
    current_user: Optional[dict] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """
    Get career suggestions based on major.

    If major is not provided, uses the current user's major.
    """
    # Use user's major if not provided
    if not major and current_user:
        major = current_user.get("major", "")

    if not major:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Major is required"
        )

    suggestions = await career_service.get_career_suggestions_by_major(
        db, major, limit
    )

    # Format response
    result = []
    for career in suggestions[:limit]:
        salary_range = "薪资面议"
        if career.get("salary_range_min") and career.get("salary_range_max"):
            salary_range = f"{career['salary_range_min']//1000}K-{career['salary_range_max']//1000}K"

        result.append({
            "career": career["name"],
            "description": career.get("description", ""),
            "required_skills": career.get("required_skills", []),
            "salary_range": salary_range,
            "growth_path": career.get("growth_path", ""),
            "match_score": career.get("match_score", 80)
        })

    return result
