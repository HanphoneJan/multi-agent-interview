"""Recommendation API endpoints"""
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user_optional
from app.dependencies import get_current_user
from app.schemas.recommendation import (
    RecommendationRequest,
    RecommendationResponse,
    RecommendationListResponse,
    ReportRecommendationRequest,
    ReportRecommendationResponse,
    ReportRecommendationItem,
    PageEvaluationRequest,
    PageEvaluationResponse,
    ReportEvaluationRequest,
    ReportEvaluationResponse,
    ABTestRequest,
    ABTestResponse,
    JobRecommendationResponse,
)
from app.services.recommendation_service import recommendation_service
from app.utils.log_helper import get_logger


logger = get_logger("api.v1.recommendations")

# Create router
router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.post(
    "/personalized",
    response_model=RecommendationListResponse,
    summary="Get personalized recommendations",
    description="Get personalized learning resource recommendations based on user's evaluation scores and interaction history"
)
async def get_personalized_recommendations(
    request: RecommendationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict | None = Depends(get_current_user_optional)
):
    """
    Get personalized recommendations for the current user.

    If the user is not logged in, returns popular resources.
    """
    if not current_user:
        # Anonymous user: return popular resources
        logger.info("Anonymous user requesting recommendations, returning popular resources")
        popular = await recommendation_service._get_popular_resources(db, limit=request.limit)
        return RecommendationListResponse(
            recommendations=[_convert_to_response(r) for r in popular],
            count=len(popular),
            type="popular"
        )

    # Get personalized recommendations
    try:
        recommendations = await recommendation_service.get_recommendations_for_user(
            db=db,
            user_id=current_user["id"],
            limit=request.limit
        )

        # Apply filters
        if request.difficulty:
            recommendations = [r for r in recommendations if r.get("difficulty") == request.difficulty]
        if request.resource_type:
            recommendations = [r for r in recommendations if r.get("resource_type") == request.resource_type]

        # Convert to response format
        response_list = [_convert_to_response(r) for r in recommendations[:request.limit]]

        return RecommendationListResponse(
            recommendations=response_list,
            count=len(response_list),
            type="personalized"
        )

    except Exception as e:
        logger.error(f"Error getting personalized recommendations for user {current_user['id']}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate recommendations"
        )


@router.get(
    "/popular",
    response_model=RecommendationListResponse,
    summary="Get popular resources",
    description="Get most popular learning resources based on views and ratings"
)
async def get_popular_recommendations(
    limit: int = 10,
    difficulty: str | None = None,
    resource_type: str | None = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Get popular resources sorted by views and ratings.

    Query parameters:
    - limit: Number of resources to return (1-50, default: 10)
    - difficulty: Filter by difficulty (easy/medium/hard)
    - resource_type: Filter by resource type (question/course/video)
    """
    if limit < 1 or limit > 50:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Limit must be between 1 and 50"
        )

    try:
        # Get popular resources
        popular = await recommendation_service._get_popular_resources(db, limit=limit * 2)

        # Apply filters
        if difficulty:
            popular = [r for r in popular if r.get("difficulty") == difficulty]
        if resource_type:
            popular = [r for r in popular if r.get("resource_type") == resource_type]

        # Limit results
        popular = popular[:limit]

        return RecommendationListResponse(
            recommendations=[_convert_to_response(r) for r in popular],
            count=len(popular),
            type="popular"
        )

    except Exception as e:
        logger.error(f"Error getting popular recommendations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get popular resources"
        )


# ---------- RAG Report Recommendations ----------


@router.get(
    "/report/{session_id}",
    response_model=ReportRecommendationResponse,
    summary="Get RAG-based recommendations for interview report",
    description="基于面试评估报告的 RAG 推荐，根据薄弱领域与 LLM 生成个性化学习资源推荐及理由",
)
async def get_report_recommendations(
    session_id: int,
    limit: int = 5,
    difficulty: str | None = None,
    resource_type: str | None = None,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    获取面试报告相关的 RAG 推荐。

    根据该报告对应的面试评估结果，识别薄弱领域，结合向量检索与 LLM 生成 personalized 推荐理由。
    需登录且仅可查询本人的报告。
    """
    from app.services.evaluation_service import get_overall_evaluation
    from app.recommenders.rag_recommender import RAGRecommender

    evaluation = await get_overall_evaluation(db, session_id)
    if not evaluation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evaluation report not found",
        )
    if evaluation.get("user_id") != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot access recommendations for another user's report",
        )

    evaluation_id = evaluation["id"]
    filters = {}
    if difficulty:
        filters["difficulty"] = difficulty
    if resource_type:
        filters["resource_type"] = resource_type

    rag = RAGRecommender()
    result = await rag.async_recommend(
        db=db,
        evaluation_id=evaluation_id,
        limit=min(limit, 20),
        filters=filters or None,
    )

    items = []
    for r in result.get("recommendations", []):
        tags = r.get("tags", "")
        if isinstance(tags, list):
            tags = ", ".join(str(t) for t in tags) if tags else ""
        items.append(
            ReportRecommendationItem(
                resource_id=r.get("resource_id", 0),
                name=r.get("resource_name", ""),
                resource_type=r.get("resource_type"),
                tags=tags,
                url=r.get("url"),
                duration_or_quantity=r.get("duration_or_quantity"),
                difficulty=r.get("difficulty"),
                reason=r.get("reason", ""),
            )
        )

    return ReportRecommendationResponse(
        weak_areas=result.get("weak_areas", []),
        recommendations=items,
        overall_advice=result.get("overall_advice", ""),
    )


# ---------- Evaluation Endpoints ----------


@router.post(
    "/evaluation/page",
    response_model=PageEvaluationResponse,
    summary="Evaluate page recommendation metrics",
    description="Compute Precision@K, Recall@K, NDCG@K, HitRate@K for page recommendations"
)
async def evaluate_page_recommendations(request: PageEvaluationRequest):
    """Compute offline metrics for page recommendations."""
    from app.recommenders.evaluation.metrics import compute_page_recommendation_metrics

    metrics = compute_page_recommendation_metrics(
        recommended=request.recommended_ids,
        relevant=set(request.relevant_ids),
        k=request.k,
    )
    return PageEvaluationResponse(
        precision_at_k=metrics["precision_at_k"],
        recall_at_k=metrics["recall_at_k"],
        ndcg_at_k=metrics["ndcg_at_k"],
        hit_rate_at_k=metrics["hit_rate_at_k"],
        k=metrics["k"],
    )


@router.post(
    "/evaluation/report",
    response_model=ReportEvaluationResponse,
    summary="Evaluate report recommendation metrics",
    description="Compute relevance, coverage, diversity for interview report recommendations"
)
async def evaluate_report_recommendations(request: ReportEvaluationRequest):
    """Compute offline metrics for report recommendations."""
    from app.recommenders.evaluation.report_metrics import compute_report_recommendation_metrics

    metrics = compute_report_recommendation_metrics(
        recommended_resources=request.recommended_resources,
        weak_dimensions=request.weak_dimensions,
    )
    return ReportEvaluationResponse(
        relevance=metrics["relevance"],
        coverage=metrics["coverage"],
        diversity=metrics["diversity"],
    )


@router.post(
    "/evaluation/ab-test",
    response_model=ABTestResponse,
    summary="Compute A/B test result",
    description="Statistical significance for control vs treatment recommendation metrics"
)
async def compute_ab_test(request: ABTestRequest):
    """Compute A/B test result with p-value and confidence interval."""
    from app.recommenders.evaluation.ab_test import compute_ab_test_result, ABTestConfig

    result = compute_ab_test_result(
        control_metrics=request.control_metrics,
        treatment_metrics=request.treatment_metrics,
        config=ABTestConfig(),
    )
    return ABTestResponse(
        control_metric=result.control_metric,
        treatment_metric=result.treatment_metric,
        absolute_lift=result.absolute_lift,
        relative_lift_percent=result.relative_lift_percent,
        is_significant=result.is_significant,
        p_value=result.p_value,
        confidence_interval_low=result.confidence_interval_low,
        confidence_interval_high=result.confidence_interval_high,
        control_sample_size=result.control_sample_size,
        treatment_sample_size=result.treatment_sample_size,
    )


# ---------- Helper ----------


def _convert_to_response(rec: dict) -> RecommendationResponse:
    """Convert internal recommendation format to API response"""
    return RecommendationResponse(
        resource_id=rec["id"],
        name=rec["name"],
        resource_type=rec["resource_type"],
        tags=rec.get("tags", []),
        difficulty=rec.get("difficulty"),
        url=rec["url"],
        duration_or_quantity=str(rec.get("duration_or_quantity", "")),
        score=rec.get("final_score", rec.get("score", 0)),
        reason=rec.get("reason", "Recommended for you")
    )


# ---------- Career Suggestion Endpoint (UniApp Compatible) ----------


class CareerSuggestionRequest(BaseModel):
    """Career suggestion request"""
    major: str | None = None
    learning_stage: str | None = None
    interests: list[str] | None = None
    skills: list[str] | None = None


class CareerSuggestionResponse(BaseModel):
    """Career suggestion response"""
    suggestions: list[dict]
    advice: str



def _generate_career_advice(user_data: dict, careers: list) -> str:
    """Generate personalized career advice based on user data"""
    major = user_data.get("major", "")
    university = user_data.get("university", "")
    learning_stage = user_data.get("learning_stage", "")

    # Build advice based on learning stage
    stage_advice = {
        "FRESHMAN_1": "大一阶段建议打好基础课程，探索不同方向，培养学习习惯。",
        "FRESHMAN_2": "大一下学期可以开始接触专业相关的基础技能，寻找兴趣方向。",
        "SOPHOMORE_1": "大二上学期建议深入学习专业课程，开始准备相关项目经验。",
        "SOPHOMORE_2": "大二下学期应积极参与实习或项目，积累实践经验。",
        "JUNIOR_1": "大三上学期是技能提升的关键期，建议针对性准备求职技能。",
        "JUNIOR_2": "大三下学期可以开始寻找暑期实习，积累工作经验。",
        "SENIOR_1": "大四上学期是秋招关键期，建议全力准备求职。",
        "SENIOR_2": "大四下学期关注春招补录机会，同时完成毕业论文。",
        "GRADUATE_STUDENT": "研究生阶段建议深入专业领域，积累研究或项目经验。",
        "JOB_SEEKER": "求职阶段建议针对性提升面试技巧，积极投递简历。",
        "EMPLOYED": "在职阶段建议持续学习，关注行业发展，规划职业路径。",
    }

    advice_parts = []

    if major:
        advice_parts.append(f"基于你的专业背景（{major}），")

    if learning_stage and learning_stage in stage_advice:
        advice_parts.append(stage_advice[learning_stage])
    else:
        advice_parts.append("建议你结合自身优势选择适合的职业方向。")

    # Add career-specific advice
    if careers:
        top_career = careers[0]["career"]
        advice_parts.append(f"推荐的「{top_career}」方向与你的专业背景匹配度较高，")
        advice_parts.append(f"核心技能要求：{', '.join(careers[0]['required_skills'][:3])}。")

    advice_parts.append("建议多参与实际项目实践，建立作品集，并持续关注行业动态。")

    return "".join(advice_parts)


@router.post(
    "/career",
    response_model=CareerSuggestionResponse,
    summary="Get career suggestions",
    description="基于用户专业、学习阶段提供职业规划建议 (兼容 uniapp)",
)
async def get_career_suggestions(
    request: CareerSuggestionRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    获取职业规划建议。

    基于用户的专业、学习阶段，从职业数据库中推荐适合的职业方向和学习路径。
    """
    from app.services import career_service

    # Use user data from database or request
    user_data = {
        "major": request.major or current_user.get("major", ""),
        "university": current_user.get("university", ""),
        "learning_stage": request.learning_stage or current_user.get("learning_stage", ""),
    }

    # Get career suggestions from database
    suggestions_data = await career_service.get_career_suggestions_by_major(
        db, user_data["major"], limit=4
    )

    # Format suggestions
    suggestions = []
    for career in suggestions_data:
        salary_range = "薪资面议"
        if career.get("salary_range_min") and career.get("salary_range_max"):
            salary_range = f"{career['salary_range_min']//1000}K-{career['salary_range_max']//1000}K"

        suggestions.append({
            "career": career["name"],
            "description": career.get("description", ""),
            "required_skills": career.get("required_skills", []),
            "salary_range": salary_range,
            "growth_path": career.get("growth_path", ""),
        })

    # Use default if no suggestions found
    if not suggestions:
        suggestions = _get_default_career_suggestions()

    # Generate personalized advice
    advice = _generate_career_advice(user_data, suggestions)

    return CareerSuggestionResponse(
        suggestions=suggestions,
        advice=advice
    )


def _get_default_career_suggestions() -> list:
    """Get default career suggestions when no matches found"""
    return [
        {
            "career": "产品经理",
            "description": "负责产品规划和需求分析，协调技术、设计和业务团队",
            "required_skills": ["需求分析", "产品设计", "数据分析", "沟通协调", "项目管理"],
            "salary_range": "12K-50K",
            "growth_path": "产品助理 → 产品经理 → 高级经理 → 产品VP"
        },
        {
            "career": "数据分析师",
            "description": "通过数据分析支持业务决策，挖掘数据价值",
            "required_skills": ["SQL", "Excel", "数据可视化", "统计分析", "业务理解"],
            "salary_range": "10K-30K",
            "growth_path": "数据分析师 → 高级分析师 → 分析经理 → 数据总监"
        },
        {
            "career": "后端开发工程师",
            "description": "负责服务器端应用程序的设计和开发",
            "required_skills": ["Java/Python/Go", "MySQL/PostgreSQL", "Redis", "消息队列", "微服务"],
            "salary_range": "15K-45K",
            "growth_path": "初级工程师 → 中级工程师 → 高级工程师 → 架构师"
        },
    ]


# ---------- Job Recommendation Endpoint (UniApp Compatible) ----------


@router.get(
    "/jobs",
    response_model=JobRecommendationResponse,
    summary="Get job recommendations by major",
    description="根据用户专业返回推荐的岗位名称列表 (兼容 uniapp 首页)",
)
async def get_job_recommendations(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    获取推荐岗位列表。

    基于用户的专业信息，返回推荐的岗位名称列表，用于首页展示。
    需要用户登录。
    """
    from app.services import career_service

    # 获取用户专业
    major = current_user.get("major", "")

    # Get career suggestions from database
    careers = await career_service.get_career_suggestions_by_major(
        db, major, limit=4
    )

    # Extract career names
    if careers:
        jobs = [career["name"] for career in careers[:4]]
    else:
        # Default fallback
        jobs = ["产品经理", "数据分析师", "后端开发工程师", "前端开发工程师"]

    return JobRecommendationResponse(
        jobs=jobs,
        major=major
    )
