"""Career and major schemas"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


# ============ Major Schemas ============

class MajorCategoryBase(BaseModel):
    """Base major category schema"""
    code: str = Field(..., min_length=1, max_length=10)
    name: str = Field(..., min_length=1, max_length=50)
    name_en: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = None


class MajorCategoryCreate(MajorCategoryBase):
    """Major category creation schema"""
    pass


class MajorCategoryResponse(MajorCategoryBase):
    """Major category response schema"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime


class MajorSubcategoryBase(BaseModel):
    """Base major subcategory schema"""
    category_id: int
    code: str = Field(..., min_length=1, max_length=10)
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None


class MajorSubcategoryCreate(MajorSubcategoryBase):
    """Major subcategory creation schema"""
    pass


class MajorSubcategoryResponse(MajorSubcategoryBase):
    """Major subcategory response schema"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    category: Optional[MajorCategoryResponse] = None
    created_at: datetime


class MajorBase(BaseModel):
    """Base major schema"""
    subcategory_id: int
    code: str = Field(..., min_length=1, max_length=10)
    name: str = Field(..., min_length=1, max_length=100)
    degree_type: Optional[str] = Field(None, max_length=20)
    duration: Optional[int] = Field(None, ge=1, le=10)
    description: Optional[str] = None
    keywords: List[str] = Field(default_factory=list)
    is_active: bool = True


class MajorCreate(MajorBase):
    """Major creation schema"""
    pass


class MajorUpdate(BaseModel):
    """Major update schema"""
    name: Optional[str] = Field(None, max_length=100)
    degree_type: Optional[str] = Field(None, max_length=20)
    duration: Optional[int] = Field(None, ge=1, le=10)
    description: Optional[str] = None
    keywords: Optional[List[str]] = None
    is_active: Optional[bool] = None


class MajorResponse(MajorBase):
    """Major response schema"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    subcategory: Optional[MajorSubcategoryResponse] = None
    created_at: datetime
    updated_at: datetime


class MajorWithCareersResponse(MajorResponse):
    """Major response with related careers"""
    related_careers: List["CareerMatchResponse"] = Field(default_factory=list)


# ============ Career Schemas ============

class CareerCategoryBase(BaseModel):
    """Base career category schema"""
    code: str = Field(..., min_length=1, max_length=10)
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None


class CareerCategoryCreate(CareerCategoryBase):
    """Career category creation schema"""
    pass


class CareerCategoryResponse(CareerCategoryBase):
    """Career category response schema"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime


class CareerSkillBase(BaseModel):
    """Base career skill schema"""
    name: str = Field(..., min_length=1, max_length=50)
    category: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = None


class CareerSkillCreate(CareerSkillBase):
    """Career skill creation schema"""
    pass


class CareerSkillResponse(CareerSkillBase):
    """Career skill response schema"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime


class CareerSkillMappingResponse(BaseModel):
    """Career skill mapping response"""
    model_config = ConfigDict(from_attributes=True)

    skill: CareerSkillResponse
    importance: int = Field(..., ge=1, le=5)
    is_required: bool


class CareerBase(BaseModel):
    """Base career schema"""
    category_id: Optional[int] = None
    code: Optional[str] = Field(None, max_length=20)
    name: str = Field(..., min_length=1, max_length=100)
    aliases: List[str] = Field(default_factory=list)
    description: Optional[str] = None
    required_skills: List[str] = Field(default_factory=list)
    salary_range_min: Optional[int] = Field(None, ge=0)
    salary_range_max: Optional[int] = Field(None, ge=0)
    growth_path: Optional[str] = None
    work_environment: Optional[str] = None
    education_requirement: Optional[str] = Field(None, max_length=50)
    is_active: bool = True
    source: str = "manual"
    external_id: Optional[str] = Field(None, max_length=100)


class CareerCreate(CareerBase):
    """Career creation schema"""
    pass


class CareerUpdate(BaseModel):
    """Career update schema"""
    category_id: Optional[int] = None
    name: Optional[str] = Field(None, max_length=100)
    aliases: Optional[List[str]] = None
    description: Optional[str] = None
    required_skills: Optional[List[str]] = None
    salary_range_min: Optional[int] = Field(None, ge=0)
    salary_range_max: Optional[int] = Field(None, ge=0)
    growth_path: Optional[str] = None
    work_environment: Optional[str] = None
    education_requirement: Optional[str] = Field(None, max_length=50)
    is_active: Optional[bool] = None


class CareerResponse(CareerBase):
    """Career response schema"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    category: Optional[CareerCategoryResponse] = None
    created_at: datetime
    updated_at: datetime


class CareerDetailResponse(CareerResponse):
    """Career response with skills"""
    skills: List[CareerSkillMappingResponse] = Field(default_factory=list)
    related_majors: List["MajorMatchResponse"] = Field(default_factory=list)


class CareerMatchResponse(BaseModel):
    """Career with match score"""
    career: CareerResponse
    match_score: int = Field(..., ge=0, le=100)
    is_primary: bool


class MajorMatchResponse(BaseModel):
    """Major with match score"""
    major: MajorResponse
    match_score: int = Field(..., ge=0, le=100)
    is_primary: bool


# ============ Job Platform Schemas ============

class JobPlatformBase(BaseModel):
    """Base job platform schema"""
    name: str = Field(..., min_length=1, max_length=50)
    code: str = Field(..., min_length=1, max_length=20)
    api_endpoint: Optional[str] = Field(None, max_length=500)
    is_active: bool = True
    rate_limit: int = Field(100, ge=1)


class JobPlatformCreate(JobPlatformBase):
    """Job platform creation schema"""
    api_key: Optional[str] = Field(None, max_length=255)


class JobPlatformResponse(JobPlatformBase):
    """Job platform response schema"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    last_sync_at: Optional[datetime] = None
    created_at: datetime


# ============ External Job Schemas ============

class ExternalJobBase(BaseModel):
    """Base external job schema"""
    platform_id: int
    external_id: str = Field(..., max_length=100)
    title: str = Field(..., min_length=1, max_length=200)
    company_name: Optional[str] = Field(None, max_length=200)
    salary_min: Optional[int] = Field(None, ge=0)
    salary_max: Optional[int] = Field(None, ge=0)
    salary_months: Optional[int] = Field(None, ge=12, le=24)
    city: Optional[str] = Field(None, max_length=50)
    district: Optional[str] = Field(None, max_length=50)
    address: Optional[str] = None
    education_requirement: Optional[str] = Field(None, max_length=50)
    experience_requirement: Optional[str] = Field(None, max_length=50)
    job_description: Optional[str] = None
    job_tags: List[str] = Field(default_factory=list)
    skills_required: List[str] = Field(default_factory=list)
    apply_url: Optional[str] = None
    publish_date: Optional[datetime] = None
    is_active: bool = True


class ExternalJobCreate(ExternalJobBase):
    """External job creation schema"""
    raw_data: Optional[dict] = None


class ExternalJobResponse(ExternalJobBase):
    """External job response schema"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    platform: Optional[JobPlatformResponse] = None
    created_at: datetime
    updated_at: datetime


class ExternalJobWithCareerResponse(ExternalJobResponse):
    """External job with career mapping"""
    matched_careers: List["JobCareerMappingResponse"] = Field(default_factory=list)


class JobCareerMappingResponse(BaseModel):
    """Job career mapping response"""
    model_config = ConfigDict(from_attributes=True)

    career: CareerResponse
    match_score: int = Field(..., ge=0, le=100)
    is_verified: bool


class JobSearchQuery(BaseModel):
    """Job search query schema"""
    keyword: Optional[str] = None
    city: Optional[str] = None
    career_id: Optional[int] = None
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    education: Optional[str] = None
    experience: Optional[str] = None
    platforms: List[str] = Field(default_factory=list)
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)


class JobSearchResponse(BaseModel):
    """Job search response schema"""
    items: List[ExternalJobResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
    aggregations: Optional[dict] = None


# ============ Career Planning Schemas ============

class UserCareerPreferenceBase(BaseModel):
    """Base user career preference schema"""
    preferred_careers: List[int] = Field(default_factory=list)
    preferred_cities: List[str] = Field(default_factory=list)
    salary_expectation_min: Optional[int] = None
    salary_expectation_max: Optional[int] = None
    work_preference: Optional[str] = Field(None, pattern=r"^(remote|hybrid|onsite)$")


class UserCareerPreferenceCreate(UserCareerPreferenceBase):
    """User career preference creation schema"""
    pass


class UserCareerPreferenceUpdate(UserCareerPreferenceBase):
    """User career preference update schema"""
    preferred_careers: Optional[List[int]] = None
    preferred_cities: Optional[List[str]] = None


class UserCareerPreferenceResponse(UserCareerPreferenceBase):
    """User career preference response schema"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    updated_at: datetime
    created_at: datetime


class CareerPlanMilestone(BaseModel):
    """Career plan milestone schema"""
    title: str
    description: Optional[str] = None
    deadline: Optional[datetime] = None
    completed: bool = False
    completed_at: Optional[datetime] = None


class CareerPlanBase(BaseModel):
    """Base career plan schema"""
    title: Optional[str] = Field(None, max_length=200)
    target_career_id: Optional[int] = None
    current_stage: Optional[str] = Field(None, max_length=50)
    target_stage: Optional[str] = Field(None, max_length=50)
    timeline_months: Optional[int] = Field(None, ge=1, le=120)
    milestones: List[CareerPlanMilestone] = Field(default_factory=list)
    skills_gap: List[str] = Field(default_factory=list)
    learning_resources: List[int] = Field(default_factory=list)
    ai_suggestions: Optional[str] = None
    is_active: bool = True


class CareerPlanCreate(CareerPlanBase):
    """Career plan creation schema"""
    pass


class CareerPlanUpdate(BaseModel):
    """Career plan update schema"""
    title: Optional[str] = Field(None, max_length=200)
    target_career_id: Optional[int] = None
    current_stage: Optional[str] = Field(None, max_length=50)
    target_stage: Optional[str] = Field(None, max_length=50)
    timeline_months: Optional[int] = Field(None, ge=1, le=120)
    milestones: Optional[List[CareerPlanMilestone]] = None
    skills_gap: Optional[List[str]] = None
    learning_resources: Optional[List[int]] = None
    ai_suggestions: Optional[str] = None
    is_active: Optional[bool] = None


class CareerPlanResponse(CareerPlanBase):
    """Career plan response schema"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    target_career: Optional[CareerResponse] = None
    created_at: datetime
    updated_at: datetime


# ============ Career Suggestion Schemas ============

class CareerSuggestionRequest(BaseModel):
    """Career suggestion request schema"""
    major_id: Optional[int] = None
    preferred_careers: List[int] = Field(default_factory=list)
    preferred_cities: List[str] = Field(default_factory=list)
    salary_expectation_min: Optional[int] = None
    salary_expectation_max: Optional[int] = None
    learning_stage: Optional[str] = None
    skills: List[str] = Field(default_factory=list)


class CareerSalaryForecast(BaseModel):
    """Career salary forecast schema"""
    entry: str  # 入行薪资
    year_1: str
    year_3: str
    year_5: str
    year_10: str


class CareerSuggestionItem(BaseModel):
    """Single career suggestion item"""
    career: CareerResponse
    match_score: int
    match_reason: str
    salary_forecast: CareerSalaryForecast
    recommended_skills: List[str]
    learning_path: List[str]


class MarketInsights(BaseModel):
    """Market insights schema"""
    hot_careers: List[CareerResponse]
    salary_trends: dict
    skills_in_demand: List[str]
    demand_by_city: dict


class CareerSuggestionResponse(BaseModel):
    """Career suggestion response schema"""
    suggestions: List[CareerSuggestionItem]
    market_insights: MarketInsights
    ai_advice: str


# ============ Salary Statistics Schemas ============

class SalaryStatistics(BaseModel):
    """Salary statistics schema"""
    entry_level: dict  # {"min": 8000, "max": 15000, "avg": 11000, "median": 10000}
    mid_level: dict
    senior_level: dict


class CareerSalaryStatisticsResponse(BaseModel):
    """Career salary statistics response"""
    career: CareerResponse
    overall: SalaryStatistics
    by_city: dict  # {"北京": {"avg": 25000}, "上海": {"avg": 23000}}
    by_company_size: dict
    trend: str  # up/down/stable


# Forward references
MajorWithCareersResponse.model_rebuild()
CareerDetailResponse.model_rebuild()
ExternalJobWithCareerResponse.model_rebuild()
