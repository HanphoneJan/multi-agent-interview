"""Application constants"""
from enum import Enum


class LearningStage(str, Enum):
    """Learning stage choices"""
    FRESHMAN_1 = "FRESHMAN_1"          # 大一上
    FRESHMAN_2 = "FRESHMAN_2"          # 大一下
    SOPHOMORE_1 = "SOPHOMORE_1"        # 大二上
    SOPHOMORE_2 = "SOPHOMORE_2"        # 大二下
    JUNIOR_1 = "JUNIOR_1"              # 大三上
    JUNIOR_2 = "JUNIOR_2"              # 大三下
    SENIOR_1 = "SENIOR_1"              # 大四上
    SENIOR_2 = "SENIOR_2"              # 大四下
    GRADUATE_STUDENT = "GRADUATE_STUDENT"  # 研究生
    JOB_SEEKER = "JOB_SEEKER"          # 应届生
    EMPLOYED = "EMPLOYED"              # 社会人士
    OTHER = "OTHER"                    # 其他


class Gender(str, Enum):
    """Gender choices"""
    MALE = "M"
    FEMALE = "F"
    OTHER = "O"


class ResourceType(str, Enum):
    """Resource type choices"""
    QUESTION = "question"
    COURSE = "course"
    VIDEO = "video"


class Difficulty(str, Enum):
    """Difficulty choices"""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class InterviewSessionStatus(str, Enum):
    """Interview session status"""
    CREATED = "created"
    IN_PROGRESS = "in_progress"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


# Learning stage display names
LEARNING_STAGE_DISPLAY = {
    LearningStage.FRESHMAN_1: "大一上",
    LearningStage.FRESHMAN_2: "大一下",
    LearningStage.SOPHOMORE_1: "大二上",
    LearningStage.SOPHOMORE_2: "大二下",
    LearningStage.JUNIOR_1: "大三上",
    LearningStage.JUNIOR_2: "大三下",
    LearningStage.SENIOR_1: "大四上",
    LearningStage.SENIOR_2: "大四下",
    LearningStage.GRADUATE_STUDENT: "研究生",
    LearningStage.JOB_SEEKER: "应届生",
    LearningStage.EMPLOYED: "社会人士",
    LearningStage.OTHER: "其他",
}

# Gender display names
GENDER_DISPLAY = {
    Gender.MALE: "男",
    Gender.FEMALE: "女",
    Gender.OTHER: "其他",
}

# ============ 评估相关 ============
# 默认/回退分数
DEFAULT_EVALUATION_SCORE = 0.5  # 0-1 区间
DEFAULT_REPORT_SCORE = 75  # 0-100 区间
DEFAULT_STRENGTHS = ["结构清晰"]
DEFAULT_WEAKNESSES = ["可补充更多细节"]
DEFAULT_EVALUATION_UNAVAILABLE = "评估暂不可用。"
DEFAULT_OVERALL_EVALUATION = "评估完成。"
DEFAULT_IMPROVEMENT_ADVICE = "建议继续提升面试表现。"
QWEN_NOT_CONFIGURED_EVAL = "请配置 QWEN_API_KEY 以启用智能评估"
QWEN_NOT_CONFIGURED_REPORT = "请配置 QWEN_API_KEY 以启用智能报告生成"
QWEN_CONFIG_ADVICE = "配置完成后可自动生成评估报告"
NO_RECORDS_EVALUATION = "暂无面试记录"
NO_RECORDS_ADVICE = "请完成面试后再生成报告"

# ============ 推荐相关 ============
# 薄弱领域阈值（低于此分数视为薄弱）
WEAK_AREA_THRESHOLD = 60
# 推荐规则：各维度阈值与对应标签
RECOMMENDATION_RULES = {
    "professional_knowledge": {
        "threshold": 60,
        "tags": ["Python", "Java", "Go", "Rust", "Django", "Spring"],
    },
    "logical_thinking": {
        "threshold": 60,
        "tags": ["算法", "数据结构", "LeetCode", "刷题", "思维"],
    },
    "language_expression": {
        "threshold": 70,
        "tags": ["面试", "沟通", "表达", "STAR法则", "演讲"],
    },
    "technical_communication": {
        "threshold": 65,
        "tags": ["技术文档", "技术分享", "架构设计", "系统设计"],
    },
    "problem_solving": {
        "threshold": 60,
        "tags": ["问题解决", "调试", "故障排查", "案例分析"],
    },
}
# 混合推荐权重
HYBRID_WEIGHTS = {
    "rule_based": 0.5,
    "content_based": 0.3,
    "collaborative": 0.2,
}
# 多路召回数量
RECOMMENDATION_RECALL_LIMITS = {
    "rule_based": 50,
    "content_based": 30,
    "collaborative": 20,
}
# 平衡资源默认分数
BALANCED_RESOURCE_SCORE = 0.5
# RAG 推荐提示
RAG_EVALUATION_NOT_FOUND = "评估记录不存在"
RAG_NO_WEAK_AREAS_ADVICE = "您的表现很优秀，继续保持！可以根据兴趣选择提升方向。"
RAG_NO_RESOURCES_ADVICE = "未找到匹配资源"
RAG_NO_VECTOR_RESULTS_ADVICE = "未找到相关推荐"
RAG_FALLBACK_ADVICE = "建议重点提升薄弱领域的学习。推荐的资源已根据您的评估结果进行匹配。学习过程中如有疑问，请随时提问。"
RAG_DEFAULT_ADVICE = "建议重点提升薄弱领域的学习。"
# 维度中文名（用于 RAG 薄弱领域识别）
EVALUATION_DIMENSION_NAMES = {
    "professional_knowledge": "专业知识",
    "skill_match": "技能匹配",
    "language_expression": "语言表达",
    "logical_thinking": "逻辑思维",
    "stress_response": "抗压能力",
    "personality": "性格特质",
    "motivation": "求职动机",
    "value": "价值观匹配",
}
# 推荐评估维度-标签映射（与 RECOMMENDATION_RULES 一致）
DIMENSION_TAGS = {k: v["tags"] for k, v in RECOMMENDATION_RULES.items()}

# ============ 会话与任务 ============
SESSION_EXPIRE_MINUTES = 30
# Redis key TTL for interview LLM context (messages), seconds
INTERVIEW_LLM_CTX_TTL = 7200  # 2 hours
CELERY_BEAT_SCHEDULE = {
    "cleanup_sessions_seconds": 60.0,
    "cleanup_files_seconds": 3600.0,
    "cleanup_cache_seconds": 3600.0,
    "train_model_seconds": 86400.0,
}

# ============ API 与模型 ============
QWEN_DEFAULT_MODEL = "qwen-plus"
QWEN_HTTP_TIMEOUT = 60.0
EMBEDDING_DEFAULT_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
EMBEDDING_CACHE_DIR = ".models"
EMBEDDING_DEFAULT_DIM = 384
GZIP_MINIMUM_SIZE = 1000
# 注意力阈值（低于此值认为注意力不足）
ATTENTION_SCORE_THRESHOLD = 0.5
# WebSocket 进度
PROGRESS_AUDIO_START = 0.2
PROGRESS_COMPLETE = 1.0
