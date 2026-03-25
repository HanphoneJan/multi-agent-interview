"""Career and major tables (SQLAlchemy Core)"""
from sqlalchemy import (
    Table, Column, Integer, String, Text, DateTime, ForeignKey,
    Boolean, Float, JSON, ARRAY, UniqueConstraint, func
)
from app.models.base import metadata

# ============ Major System Tables ============

# 学科门类表
major_categories = Table(
    "major_categories",
    metadata,
    Column("id", Integer, primary_key=True, index=True),
    Column("code", String(10), unique=True, nullable=False, index=True),  # 如：08
    Column("name", String(50), nullable=False),  # 如：工学
    Column("name_en", String(50)),  # 英文名称
    Column("description", Text),
    Column("created_at", DateTime(timezone=True), server_default=func.now(), nullable=False),
)

# 专业类表（一级学科）
major_subcategories = Table(
    "major_subcategories",
    metadata,
    Column("id", Integer, primary_key=True, index=True),
    Column("category_id", Integer, ForeignKey("major_categories.id", ondelete="CASCADE"), nullable=False, index=True),
    Column("code", String(10), unique=True, nullable=False, index=True),  # 如：0809
    Column("name", String(100), nullable=False),  # 如：计算机类
    Column("description", Text),
    Column("created_at", DateTime(timezone=True), server_default=func.now(), nullable=False),
)

# 具体专业表（二级学科）
majors = Table(
    "majors",
    metadata,
    Column("id", Integer, primary_key=True, index=True),
    Column("subcategory_id", Integer, ForeignKey("major_subcategories.id", ondelete="CASCADE"), nullable=False, index=True),
    Column("code", String(10), unique=True, nullable=False, index=True),  # 如：080901
    Column("name", String(100), nullable=False),  # 如：计算机科学与技术
    Column("degree_type", String(20)),  # 学士/硕士/博士
    Column("duration", Integer),  # 学制（年）
    Column("description", Text),
    Column("keywords", ARRAY(String)),  # 匹配关键词
    Column("is_active", Boolean, default=True, nullable=False),
    Column("created_at", DateTime(timezone=True), server_default=func.now(), nullable=False),
    Column("updated_at", DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False),
)

# ============ Career System Tables ============

# 职业分类表
career_categories = Table(
    "career_categories",
    metadata,
    Column("id", Integer, primary_key=True, index=True),
    Column("code", String(10), unique=True, nullable=False, index=True),
    Column("name", String(100), nullable=False),
    Column("description", Text),
    Column("created_at", DateTime(timezone=True), server_default=func.now(), nullable=False),
)

# 具体职业表
careers = Table(
    "careers",
    metadata,
    Column("id", Integer, primary_key=True, index=True),
    Column("category_id", Integer, ForeignKey("career_categories.id", ondelete="SET NULL"), index=True),
    Column("code", String(20), unique=True),  # 职业代码
    Column("name", String(100), nullable=False, index=True),  # 职业名称
    Column("aliases", ARRAY(String)),  # 别名
    Column("description", Text),  # 职业描述
    Column("required_skills", ARRAY(String)),  # 核心技能要求
    Column("salary_range_min", Integer),  # 薪资下限
    Column("salary_range_max", Integer),  # 薪资上限
    Column("growth_path", Text),  # 发展路径
    Column("work_environment", Text),  # 工作环境
    Column("education_requirement", String(50)),  # 学历要求
    Column("is_active", Boolean, default=True, nullable=False),
    Column("source", String(50), default="manual"),  # 数据来源
    Column("external_id", String(100)),  # 外部平台ID
    Column("created_at", DateTime(timezone=True), server_default=func.now(), nullable=False),
    Column("updated_at", DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False),
)

# 职业技能标签表
career_skills = Table(
    "career_skills",
    metadata,
    Column("id", Integer, primary_key=True, index=True),
    Column("name", String(50), unique=True, nullable=False),
    Column("category", String(50)),  # 技能分类
    Column("description", Text),
    Column("created_at", DateTime(timezone=True), server_default=func.now(), nullable=False),
)

# 职业与技能关联表
career_skill_mappings = Table(
    "career_skill_mappings",
    metadata,
    Column("id", Integer, primary_key=True, index=True),
    Column("career_id", Integer, ForeignKey("careers.id", ondelete="CASCADE"), nullable=False, index=True),
    Column("skill_id", Integer, ForeignKey("career_skills.id", ondelete="CASCADE"), nullable=False, index=True),
    Column("importance", Integer, default=3),  # 重要程度 1-5
    Column("is_required", Boolean, default=True),  # 是否必需
    Column("created_at", DateTime(timezone=True), server_default=func.now(), nullable=False),
    UniqueConstraint("career_id", "skill_id", name="uq_career_skill"),
)

# 专业与职业关联表
major_career_mappings = Table(
    "major_career_mappings",
    metadata,
    Column("id", Integer, primary_key=True, index=True),
    Column("major_id", Integer, ForeignKey("majors.id", ondelete="CASCADE"), nullable=False, index=True),
    Column("career_id", Integer, ForeignKey("careers.id", ondelete="CASCADE"), nullable=False, index=True),
    Column("match_score", Integer, default=100),  # 匹配度 0-100
    Column("is_primary", Boolean, default=False),  # 是否主要就业方向
    Column("created_at", DateTime(timezone=True), server_default=func.now(), nullable=False),
    UniqueConstraint("major_id", "career_id", name="uq_major_career"),
)

# ============ External Job Data Tables ============

# 招聘平台配置表
job_platforms = Table(
    "job_platforms",
    metadata,
    Column("id", Integer, primary_key=True, index=True),
    Column("name", String(50), unique=True, nullable=False),  # 如：智联招聘
    Column("code", String(20), unique=True, nullable=False),  # 如：zhaopin
    Column("api_endpoint", String(500)),
    Column("api_key", String(255)),
    Column("is_active", Boolean, default=True, nullable=False),
    Column("rate_limit", Integer, default=100),  # 每分钟请求限制
    Column("last_sync_at", DateTime(timezone=True)),
    Column("created_at", DateTime(timezone=True), server_default=func.now(), nullable=False),
)

# 外部岗位信息表（缓存）
external_jobs = Table(
    "external_jobs",
    metadata,
    Column("id", Integer, primary_key=True, index=True),
    Column("platform_id", Integer, ForeignKey("job_platforms.id", ondelete="CASCADE"), nullable=False, index=True),
    Column("external_id", String(100), nullable=False),  # 平台原始ID
    Column("title", String(200), nullable=False, index=True),  # 职位标题
    Column("company_name", String(200), index=True),  # 公司名称
    Column("salary_min", Integer),  # 薪资下限
    Column("salary_max", Integer),  # 薪资上限
    Column("salary_months", Integer),  # 薪月数
    Column("city", String(50), index=True),  # 城市
    Column("district", String(50)),  # 区县
    Column("address", Text),  # 详细地址
    Column("education_requirement", String(50)),  # 学历要求
    Column("experience_requirement", String(50)),  # 经验要求
    Column("job_description", Text),  # 职位描述
    Column("job_tags", ARRAY(String)),  # 标签
    Column("skills_required", ARRAY(String)),  # 技能要求
    Column("apply_url", Text),  # 申请链接
    Column("publish_date", DateTime(timezone=True)),  # 发布日期
    Column("is_active", Boolean, default=True, nullable=False),
    Column("raw_data", JSON),  # 原始数据备份
    Column("created_at", DateTime(timezone=True), server_default=func.now(), nullable=False),
    Column("updated_at", DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False),
    UniqueConstraint("platform_id", "external_id", name="uq_platform_external_job"),
)

# 岗位与职业关联表
job_career_mappings = Table(
    "job_career_mappings",
    metadata,
    Column("id", Integer, primary_key=True, index=True),
    Column("job_id", Integer, ForeignKey("external_jobs.id", ondelete="CASCADE"), nullable=False, index=True),
    Column("career_id", Integer, ForeignKey("careers.id", ondelete="CASCADE"), nullable=False, index=True),
    Column("match_score", Integer, default=0),  # AI匹配分数
    Column("is_verified", Boolean, default=False),  # 是否人工确认
    Column("created_at", DateTime(timezone=True), server_default=func.now(), nullable=False),
    UniqueConstraint("job_id", "career_id", name="uq_job_career"),
)

# ============ User Career Planning Tables ============

# 用户职业偏好表
user_career_preferences = Table(
    "user_career_preferences",
    metadata,
    Column("id", Integer, primary_key=True, index=True),
    Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True),
    Column("preferred_careers", ARRAY(Integer)),  # 意向职业ID列表
    Column("preferred_cities", ARRAY(String)),  # 意向城市
    Column("salary_expectation_min", Integer),  # 期望薪资下限
    Column("salary_expectation_max", Integer),  # 期望薪资上限
    Column("work_preference", String(20)),  # 工作偏好：remote/hybrid/onsite
    Column("updated_at", DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False),
    Column("created_at", DateTime(timezone=True), server_default=func.now(), nullable=False),
)

# 职业规划记录表
career_plans = Table(
    "career_plans",
    metadata,
    Column("id", Integer, primary_key=True, index=True),
    Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
    Column("title", String(200)),  # 规划标题
    Column("target_career_id", Integer, ForeignKey("careers.id", ondelete="SET NULL")),
    Column("current_stage", String(50)),  # 当前阶段
    Column("target_stage", String(50)),  # 目标阶段
    Column("timeline_months", Integer),  # 规划周期（月）
    Column("milestones", JSON),  # 里程碑
    Column("skills_gap", ARRAY(String)),  # 技能差距
    Column("learning_resources", ARRAY(Integer)),  # 推荐学习资源ID
    Column("ai_suggestions", Text),  # AI生成的建议
    Column("is_active", Boolean, default=True, nullable=False),
    Column("created_at", DateTime(timezone=True), server_default=func.now(), nullable=False),
    Column("updated_at", DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False),
)
