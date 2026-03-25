"""Recommendation schemas"""
from typing import Optional

from pydantic import BaseModel, Field


# ---------- Evaluation Schemas ----------


class PageEvaluationRequest(BaseModel):
    """Request for page recommendation offline evaluation"""
    recommended_ids: list[int] = Field(..., description="Ordered list of recommended resource IDs")
    relevant_ids: list[int] = Field(..., description="Ground truth: resource IDs user interacted with")
    k: int = Field(10, ge=1, le=50, description="Top-K for metrics")


class PageEvaluationResponse(BaseModel):
    """Page recommendation evaluation metrics"""
    precision_at_k: float
    recall_at_k: float
    ndcg_at_k: float
    hit_rate_at_k: float
    k: int


class ReportEvaluationRequest(BaseModel):
    """Request for report recommendation evaluation"""
    recommended_resources: list[dict] = Field(
        ...,
        description="List of recommended resources with keys: resource_type, tags"
    )
    weak_dimensions: list[str] = Field(
        ...,
        description="Weak dimension names from evaluation (e.g. professional_knowledge)"
    )


class ReportEvaluationResponse(BaseModel):
    """Report recommendation evaluation metrics"""
    relevance: float
    coverage: float
    diversity: float


class ABTestRequest(BaseModel):
    """Request for A/B test computation"""
    control_metrics: list[float] = Field(..., description="Metric values for control group")
    treatment_metrics: list[float] = Field(..., description="Metric values for treatment group")


class ABTestResponse(BaseModel):
    """A/B test result"""
    control_metric: float
    treatment_metric: float
    absolute_lift: float
    relative_lift_percent: float
    is_significant: bool
    p_value: float
    confidence_interval_low: float
    confidence_interval_high: float
    control_sample_size: int
    treatment_sample_size: int


# ---------- Recommendation Schemas ----------


class RecommendationRequest(BaseModel):
    """Recommendation request schema"""
    limit: int = Field(10, ge=1, le=50, description="Number of recommendations")
    difficulty: Optional[str] = Field(None, pattern=r'^(easy|medium|hard)$')
    resource_type: Optional[str] = Field(None, pattern=r'^(question|course|video)$')


class RecommendationResponse(BaseModel):
    """Recommendation response schema"""
    resource_id: int
    name: str
    resource_type: str
    tags: list[str]
    difficulty: Optional[str]
    url: str
    duration_or_quantity: str
    score: float
    reason: str


class RecommendationListResponse(BaseModel):
    """List of recommendations response schema"""
    recommendations: list[RecommendationResponse]
    count: int
    type: str  # "personalized", "popular", "balanced"


class ReportRecommendationRequest(BaseModel):
    """Request for RAG report-based recommendations"""
    limit: int = Field(5, ge=1, le=20, description="Number of recommendations")
    difficulty: Optional[str] = Field(None, pattern=r"^(easy|medium|hard)$")
    resource_type: Optional[str] = Field(None, pattern=r"^(question|course|video)$")


class ReportRecommendationItem(BaseModel):
    """Single recommendation item for report (RAG)"""
    resource_id: int
    name: str
    resource_type: Optional[str] = None
    tags: str | list = ""
    url: Optional[str] = None
    duration_or_quantity: Optional[str] = None
    difficulty: Optional[str] = None
    reason: str = ""


class ReportRecommendationResponse(BaseModel):
    """RAG-based report recommendation response"""
    weak_areas: list[str] = Field(default_factory=list, description="薄弱领域列表")
    recommendations: list[ReportRecommendationItem] = Field(
        default_factory=list, description="推荐学习资源"
    )
    overall_advice: str = Field(default="", description="总体学习建议")


class JobRecommendationResponse(BaseModel):
    """Job recommendation response for UniApp home page"""
    jobs: list[str] = Field(default_factory=list, description="推荐岗位名称列表")
    major: str = Field(default="", description="用户专业")
