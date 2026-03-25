"""推荐系统 Benchmark 测试数据

包含：
- 模拟用户画像
- 测试资源库
- 用户行为数据
- 面试评估数据
"""

from typing import Dict, List, Any

# ============ 测试用户画像 ============

TEST_USER_PROFILES: List[Dict[str, Any]] = [
    {
        "user_id": 1001,
        "type": "cs_student_python_weak",
        "description": "计算机专业学生，编程基础薄弱",
        "profile": {
            "major": "计算机科学",
            "learning_stage": "在校学习",
            "university": "某理工大学",
            "gender": "男",
        },
        "evaluation": {
            "professional_knowledge": 55,  # 薄弱
            "skill_match": 70,
            "language_expression": 75,
            "logical_thinking": 80,
            "stress_response": 65,
            "personality": 80,
            "motivation": 85,
            "value": 75,
            "overall_score": 70,
        },
        "weak_areas": ["professional_knowledge"],
        "expected_tags": ["Python", "数据结构", "算法", "编程基础", "计算机基础"],
        "irrelevant_tags": ["沟通技巧", "压力管理", "产品设计"],
    },
    {
        "user_id": 1002,
        "type": "new_grad_communication_weak",
        "description": "应届生，沟通和抗压能力待提升",
        "profile": {
            "major": "软件工程",
            "learning_stage": "应届毕业",
            "university": "某大学",
            "gender": "女",
        },
        "evaluation": {
            "professional_knowledge": 75,
            "skill_match": 70,
            "language_expression": 45,  # 薄弱
            "logical_thinking": 70,
            "stress_response": 50,  # 薄弱
            "personality": 65,
            "motivation": 80,
            "value": 75,
            "overall_score": 65,
        },
        "weak_areas": ["language_expression", "stress_response"],
        "expected_tags": ["沟通技巧", "面试技巧", "表达能力", "压力管理", "职场软技能"],
        "irrelevant_tags": ["Python", "Java", "分布式系统"],
    },
    {
        "user_id": 1003,
        "type": "experienced_system_design_weak",
        "description": "有经验的开发者，需提升架构能力",
        "profile": {
            "major": "计算机科学",
            "learning_stage": "在职人士",
            "university": "某985大学",
            "gender": "男",
        },
        "evaluation": {
            "professional_knowledge": 85,
            "skill_match": 80,
            "language_expression": 85,
            "logical_thinking": 75,
            "stress_response": 80,
            "personality": 85,
            "motivation": 90,
            "value": 80,
            "overall_score": 82,
        },
        "weak_areas": [],  # 全面发展，但可推荐进阶内容
        "expected_tags": ["系统设计", "架构", "进阶", "分布式", "性能优化"],
        "irrelevant_tags": ["编程入门", "基础语法"],
    },
    {
        "user_id": 1004,
        "type": "frontend_dev_js_weak",
        "description": "前端开发者，JavaScript 基础不牢",
        "profile": {
            "major": "数字媒体",
            "learning_stage": "在职人士",
            "university": "某艺术学院",
            "gender": "女",
        },
        "evaluation": {
            "professional_knowledge": 60,  # 薄弱
            "skill_match": 65,
            "language_expression": 80,
            "logical_thinking": 70,
            "stress_response": 75,
            "personality": 85,
            "motivation": 85,
            "value": 80,
            "overall_score": 72,
        },
        "weak_areas": ["professional_knowledge"],
        "expected_tags": ["JavaScript", "前端", "React", "Vue", "CSS", "HTML"],
        "irrelevant_tags": ["Python", "Java", "数据库原理"],
    },
    {
        "user_id": 1005,
        "type": "cold_start_new_user",
        "description": "全新用户，无任何数据",
        "profile": {
            "major": "",
            "learning_stage": "",
            "university": "",
            "gender": "",
        },
        "evaluation": None,  # 无评估记录
        "weak_areas": [],
        "expected_tags": ["热门", "基础", "入门", "职业规划"],
        "irrelevant_tags": [],
    },
    {
        "user_id": 1006,
        "type": "data_scientist_ml_weak",
        "description": "数据分析师，机器学习算法薄弱",
        "profile": {
            "major": "统计学",
            "learning_stage": "在职人士",
            "university": "某财经大学",
            "gender": "男",
        },
        "evaluation": {
            "professional_knowledge": 65,  # 薄弱
            "skill_match": 60,
            "language_expression": 80,
            "logical_thinking": 75,
            "stress_response": 80,
            "personality": 80,
            "motivation": 85,
            "value": 80,
            "overall_score": 75,
        },
        "weak_areas": ["professional_knowledge", "skill_match"],
        "expected_tags": ["机器学习", "深度学习", "Python", "数据分析", "算法"],
        "irrelevant_tags": ["前端", "UI设计", "产品管理"],
    },
]

# ============ 测试资源库 ============

TEST_RESOURCES: List[Dict[str, Any]] = [
    # ===== 编程基础类 =====
    {"id": 1, "name": "Python 入门到实践", "tags": ["Python", "编程基础", "入门"],
     "type": "course", "difficulty": "easy", "views": 15000, "completions": 8000, "rating": 4.8},

    {"id": 2, "name": "数据结构与算法精讲", "tags": ["数据结构", "算法", "计算机基础"],
     "type": "course", "difficulty": "medium", "views": 12000, "completions": 6000, "rating": 4.7},

    {"id": 3, "name": "Java 核心技术卷", "tags": ["Java", "编程基础", "面向对象"],
     "type": "course", "difficulty": "medium", "views": 10000, "completions": 5000, "rating": 4.6},

    {"id": 4, "name": "JavaScript 高级程序设计", "tags": ["JavaScript", "前端", "编程基础"],
     "type": "course", "difficulty": "medium", "views": 11000, "completions": 5500, "rating": 4.7},

    # ===== 系统设计类 =====
    {"id": 5, "name": "系统设计面试指南", "tags": ["系统设计", "架构", "面试", "进阶"],
     "type": "course", "difficulty": "hard", "views": 8000, "completions": 3000, "rating": 4.9},

    {"id": 6, "name": "分布式系统原理", "tags": ["分布式", "架构", "进阶", "性能优化"],
     "type": "course", "difficulty": "hard", "views": 6000, "completions": 2000, "rating": 4.8},

    {"id": 7, "name": "微服务架构设计模式", "tags": ["微服务", "架构", "系统设计", "进阶"],
     "type": "course", "difficulty": "hard", "views": 7000, "completions": 2500, "rating": 4.7},

    # ===== 软技能类 =====
    {"id": 8, "name": "职场沟通技巧", "tags": ["沟通技巧", "软技能", "职场"],
     "type": "video", "difficulty": "easy", "views": 9000, "completions": 7000, "rating": 4.5},

    {"id": 9, "name": "面试表达训练", "tags": ["面试技巧", "表达能力", "沟通技巧"],
     "type": "video", "difficulty": "easy", "views": 8500, "completions": 6500, "rating": 4.6},

    {"id": 10, "name": "压力管理与情绪调节", "tags": ["压力管理", "心理健康", "软技能"],
     "type": "course", "difficulty": "easy", "views": 7000, "completions": 5000, "rating": 4.4},

    # ===== 前端技术类 =====
    {"id": 11, "name": "React 实战开发", "tags": ["React", "前端", "JavaScript"],
     "type": "course", "difficulty": "medium", "views": 9500, "completions": 4500, "rating": 4.7},

    {"id": 12, "name": "Vue.js 深入浅出", "tags": ["Vue", "前端", "JavaScript"],
     "type": "course", "difficulty": "medium", "views": 10000, "completions": 5000, "rating": 4.8},

    {"id": 13, "name": "CSS 高级布局技巧", "tags": ["CSS", "前端", "HTML"],
     "type": "video", "difficulty": "medium", "views": 6000, "completions": 3000, "rating": 4.5},

    # ===== 数据/AI 类 =====
    {"id": 14, "name": "机器学习实战", "tags": ["机器学习", "Python", "算法", "数据分析"],
     "type": "course", "difficulty": "hard", "views": 7500, "completions": 2800, "rating": 4.8},

    {"id": 15, "name": "深度学习入门", "tags": ["深度学习", "机器学习", "Python", "算法"],
     "type": "course", "difficulty": "hard", "views": 6500, "completions": 2200, "rating": 4.7},

    {"id": 16, "name": "SQL 数据库基础", "tags": ["SQL", "数据库", "数据分析"],
     "type": "course", "difficulty": "easy", "views": 11000, "completions": 7000, "rating": 4.6},

    # ===== 面试/职业类 =====
    {"id": 17, "name": "技术面试通关指南", "tags": ["面试技巧", "职业规划", "热门"],
     "type": "course", "difficulty": "easy", "views": 13000, "completions": 9000, "rating": 4.7},

    {"id": 18, "name": "程序员职业发展路径", "tags": ["职业规划", "进阶", "热门"],
     "type": "video", "difficulty": "easy", "views": 8000, "completions": 6000, "rating": 4.5},

    {"id": 19, "name": "简历撰写技巧", "tags": ["面试技巧", "职业规划", "热门", "基础"],
     "type": "video", "difficulty": "easy", "views": 9000, "completions": 7500, "rating": 4.6},

    # ===== 后端类 =====
    {"id": 20, "name": "Spring Boot 实战", "tags": ["Spring", "Java", "后端", "微服务"],
     "type": "course", "difficulty": "medium", "views": 8500, "completions": 4000, "rating": 4.7},
]

# ============ 用户行为数据 ============

TEST_USER_BEHAVIORS: List[Dict[str, Any]] = [
    # user_id 1001: 偏好 Python 和算法
    {"user_id": 1001, "resource_id": 1, "interaction_type": "complete", "value": 5.0},
    {"user_id": 1001, "resource_id": 2, "interaction_type": "view", "value": 3.0},
    {"user_id": 1001, "resource_id": 16, "interaction_type": "complete", "value": 4.5},

    # user_id 1002: 偏好软技能
    {"user_id": 1002, "resource_id": 8, "interaction_type": "complete", "value": 5.0},
    {"user_id": 1002, "resource_id": 9, "interaction_type": "view", "value": 4.0},
    {"user_id": 1002, "resource_id": 10, "interaction_type": "complete", "value": 4.5},

    # user_id 1003: 全面发展，偏好架构
    {"user_id": 1003, "resource_id": 5, "interaction_type": "complete", "value": 5.0},
    {"user_id": 1003, "resource_id": 6, "interaction_type": "view", "value": 4.0},
    {"user_id": 1003, "resource_id": 7, "interaction_type": "view", "value": 3.5},

    # user_id 1004: 前端开发
    {"user_id": 1004, "resource_id": 4, "interaction_type": "complete", "value": 4.5},
    {"user_id": 1004, "resource_id": 11, "interaction_type": "view", "value": 4.0},
    {"user_id": 1004, "resource_id": 12, "interaction_type": "complete", "value": 5.0},

    # user_id 1006: 数据分析
    {"user_id": 1006, "resource_id": 14, "interaction_type": "view", "value": 3.5},
    {"user_id": 1006, "resource_id": 16, "interaction_type": "complete", "value": 4.0},
    {"user_id": 1006, "resource_id": 1, "interaction_type": "view", "value": 3.0},
]

# ============ 评估阈值 ============

# 准确性指标
PRECISION_AT_K_THRESHOLD = 0.60
RECALL_AT_K_THRESHOLD = 0.40
NDCG_AT_K_THRESHOLD = 0.65

# 面试关联度
INTERVIEW_CORRELATION_THRESHOLD = 0.70

# 多样性指标
TYPE_DIVERSITY_THRESHOLD = 0.60
TAG_COVERAGE_THRESHOLD = 0.50
ILS_THRESHOLD = 0.30

# 冷启动指标
COLD_START_SATISFACTION_THRESHOLD = 0.70

# 性能指标
PERSONALIZED_REC_TIME_THRESHOLD = 2.0
REPORT_REC_TIME_THRESHOLD = 5.0
RAG_REC_TIME_THRESHOLD = 8.0

# ============ 辅助函数 ============

def get_user_profile(user_id: int) -> Dict[str, Any]:
    """根据 ID 获取用户画像"""
    for user in TEST_USER_PROFILES:
        if user["user_id"] == user_id:
            return user
    return None

def get_resource_by_id(resource_id: int) -> Dict[str, Any]:
    """根据 ID 获取资源"""
    for resource in TEST_RESOURCES:
        if resource["id"] == resource_id:
            return resource
    return None

def get_user_behaviors(user_id: int) -> List[Dict[str, Any]]:
    """获取用户行为数据"""
    return [b for b in TEST_USER_BEHAVIORS if b["user_id"] == user_id]

def calculate_tag_overlap(recommendations: List[Dict], expected_tags: List[str]) -> float:
    """计算推荐与预期标签的重叠度"""
    if not recommendations or not expected_tags:
        return 0.0

    rec_tags = set()
    for rec in recommendations:
        tags = rec.get("tags", [])
        if isinstance(tags, str):
            tags = tags.split(",")
        rec_tags.update(tags)

    expected_set = set(expected_tags)
    overlap = len(rec_tags & expected_set)
    return overlap / len(expected_set) if expected_set else 0.0

def calculate_type_diversity(recommendations: List[Dict]) -> float:
    """计算推荐结果的类型多样性"""
    if not recommendations:
        return 0.0

    types = [r.get("type", "unknown") for r in recommendations]
    unique_types = len(set(types))
    return unique_types / len(types) if types else 0.0

def is_relevant_for_user(resource: Dict, user_profile: Dict) -> bool:
    """判断资源是否与用户相关（基于薄弱维度）"""
    expected_tags = user_profile.get("expected_tags", [])
    resource_tags = resource.get("tags", [])

    if isinstance(resource_tags, str):
        resource_tags = resource_tags.split(",")

    return any(tag in resource_tags for tag in expected_tags)
