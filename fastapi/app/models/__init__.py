"""Import all table definitions for use in Alembic migrations"""
from app.models.base import metadata
from app.models.user import users
from app.models.interview import interview_scenarios, interview_sessions, interview_questions
from app.models.evaluation import (
    response_metadata,
    response_analysis,
    answer_evaluations,
    resume_evaluations,
    overall_interview_evaluations
)
from app.models.learning import resources, lc_questions, user_resource_interactions
from app.models.career import (
    # Major system
    major_categories,
    major_subcategories,
    majors,
    major_career_mappings,
    # Career system
    career_categories,
    careers,
    career_skills,
    career_skill_mappings,
    # External job system
    job_platforms,
    external_jobs,
    job_career_mappings,
    # User career planning
    user_career_preferences,
    career_plans,
)
from app.models.recommendation import (
    user_events,
    user_profiles,
    item_similarities,
    user_offline_features,
    model_versions,
)

__all__ = [
    "metadata",
    # User
    "users",
    # Interview
    "interview_scenarios",
    "interview_sessions",
    "interview_questions",
    # Evaluation
    "response_metadata",
    "response_analysis",
    "answer_evaluations",
    "resume_evaluations",
    "overall_interview_evaluations",
    # Learning
    "resources",
    "lc_questions",
    "user_resource_interactions",
    # Major system
    "major_categories",
    "major_subcategories",
    "majors",
    "major_career_mappings",
    # Career system
    "career_categories",
    "careers",
    "career_skills",
    "career_skill_mappings",
    # External job system
    "job_platforms",
    "external_jobs",
    "job_career_mappings",
    # User career planning
    "user_career_preferences",
    "career_plans",
    # Recommendation
    "user_events",
    "user_profiles",
    "item_similarities",
    "user_offline_features",
    "model_versions",
]
