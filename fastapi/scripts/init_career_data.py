"""
Initialize career and major data from MOE (Ministry of Education) standard
教育部专业目录数据初始化脚本

数据来源：
- 《普通高等学校本科专业目录（2024年）》
- 《中华人民共和国职业分类大典》
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from app.database import async_session_factory
from app.models.career import (
    major_categories, major_subcategories, majors, major_career_mappings,
    career_categories, careers, career_skills, career_skill_mappings,
    job_platforms,
)


# ============ 教育部专业目录数据（部分示例） ============
# 完整数据可从教育部官网获取：http://www.moe.gov.cn/

MOE_MAJORS_DATA = [
    {
        "category": {"code": "01", "name": "哲学", "name_en": "Philosophy"},
        "subcategories": [
            {
                "code": "0101",
                "name": "哲学类",
                "majors": [
                    {"code": "010101", "name": "哲学", "degree_type": "学士", "duration": 4, "keywords": ["哲学", "Philosophy"]},
                    {"code": "010102", "name": "逻辑学", "degree_type": "学士", "duration": 4, "keywords": ["逻辑", "Logic"]},
                    {"code": "010103", "name": "宗教学", "degree_type": "学士", "duration": 4, "keywords": ["宗教", "Religion"]},
                    {"code": "010104", "name": "伦理学", "degree_type": "学士", "duration": 4, "keywords": ["伦理", "Ethics"]},
                ]
            }
        ]
    },
    {
        "category": {"code": "02", "name": "经济学", "name_en": "Economics"},
        "subcategories": [
            {
                "code": "0201",
                "name": "经济学类",
                "majors": [
                    {"code": "020101", "name": "经济学", "degree_type": "学士", "duration": 4, "keywords": ["经济", "Economics"]},
                    {"code": "020102", "name": "经济统计学", "degree_type": "学士", "duration": 4, "keywords": ["统计", "Statistics"]},
                    {"code": "020103", "name": "国民经济管理", "degree_type": "学士", "duration": 4, "keywords": ["国民经济"]},
                    {"code": "020104", "name": "资源与环境经济学", "degree_type": "学士", "duration": 4, "keywords": ["环境经济"]},
                    {"code": "020105", "name": "商务经济学", "degree_type": "学士", "duration": 4, "keywords": ["商务"]},
                    {"code": "020106", "name": "能源经济", "degree_type": "学士", "duration": 4, "keywords": ["能源"]},
                    {"code": "020107", "name": "劳动经济学", "degree_type": "学士", "duration": 4, "keywords": ["劳动经济"]},
                    {"code": "020108", "name": "经济工程", "degree_type": "学士", "duration": 4, "keywords": ["经济工程"]},
                    {"code": "020109", "name": "数字经济", "degree_type": "学士", "duration": 4, "keywords": ["数字经济", "Digital Economy"]},
                ]
            },
            {
                "code": "0202",
                "name": "财政学类",
                "majors": [
                    {"code": "020201", "name": "财政学", "degree_type": "学士", "duration": 4, "keywords": ["财政", "Finance"]},
                    {"code": "020202", "name": "税收学", "degree_type": "学士", "duration": 4, "keywords": ["税收", "Taxation"]},
                ]
            },
            {
                "code": "0203",
                "name": "金融学类",
                "majors": [
                    {"code": "020301", "name": "金融学", "degree_type": "学士", "duration": 4, "keywords": ["金融", "Finance"]},
                    {"code": "020302", "name": "金融工程", "degree_type": "学士", "duration": 4, "keywords": ["金融工程"]},
                    {"code": "020303", "name": "保险学", "degree_type": "学士", "duration": 4, "keywords": ["保险", "Insurance"]},
                    {"code": "020304", "name": "投资学", "degree_type": "学士", "duration": 4, "keywords": ["投资", "Investment"]},
                    {"code": "020305", "name": "金融数学", "degree_type": "学士", "duration": 4, "keywords": ["金融数学"]},
                    {"code": "020306", "name": "信用管理", "degree_type": "学士", "duration": 4, "keywords": ["信用管理"]},
                    {"code": "020307", "name": "经济与金融", "degree_type": "学士", "duration": 4, "keywords": ["经济金融"]},
                    {"code": "020308", "name": "精算学", "degree_type": "学士", "duration": 4, "keywords": ["精算", "Actuary"]},
                    {"code": "020309", "name": "互联网金融", "degree_type": "学士", "duration": 4, "keywords": ["互联网金融"]},
                    {"code": "020310", "name": "金融科技", "degree_type": "学士", "duration": 4, "keywords": ["金融科技", "FinTech"]},
                ]
            },
        ]
    },
    {
        "category": {"code": "07", "name": "理学", "name_en": "Science"},
        "subcategories": [
            {
                "code": "0701",
                "name": "数学类",
                "majors": [
                    {"code": "070101", "name": "数学与应用数学", "degree_type": "学士", "duration": 4, "keywords": ["数学", "Math"]},
                    {"code": "070102", "name": "信息与计算科学", "degree_type": "学士", "duration": 4, "keywords": ["计算科学"]},
                    {"code": "070103", "name": "数理基础科学", "degree_type": "学士", "duration": 4, "keywords": ["数理基础"]},
                    {"code": "070104", "name": "数据计算及应用", "degree_type": "学士", "duration": 4, "keywords": ["数据计算"]},
                ]
            },
            {
                "code": "0712",
                "name": "统计学类",
                "majors": [
                    {"code": "071201", "name": "统计学", "degree_type": "学士", "duration": 4, "keywords": ["统计", "Statistics"]},
                    {"code": "071202", "name": "应用统计学", "degree_type": "学士", "duration": 4, "keywords": ["应用统计"]},
                ]
            },
        ]
    },
    {
        "category": {"code": "08", "name": "工学", "name_en": "Engineering"},
        "subcategories": [
            {
                "code": "0802",
                "name": "机械类",
                "majors": [
                    {"code": "080201", "name": "机械工程", "degree_type": "学士", "duration": 4, "keywords": ["机械", "Mechanical"]},
                    {"code": "080202", "name": "机械设计制造及其自动化", "degree_type": "学士", "duration": 4, "keywords": ["机械设计", "自动化"]},
                    {"code": "080203", "name": "材料成型及控制工程", "degree_type": "学士", "duration": 4, "keywords": ["材料成型"]},
                    {"code": "080204", "name": "机械电子工程", "degree_type": "学士", "duration": 4, "keywords": ["机械电子"]},
                    {"code": "080205", "name": "工业设计", "degree_type": "学士", "duration": 4, "keywords": ["工业设计", "ID"]},
                    {"code": "080206", "name": "过程装备与控制工程", "degree_type": "学士", "duration": 4, "keywords": ["过程装备"]},
                    {"code": "080207", "name": "车辆工程", "degree_type": "学士", "duration": 4, "keywords": ["车辆", "汽车"]},
                    {"code": "080208", "name": "汽车服务工程", "degree_type": "学士", "duration": 4, "keywords": ["汽车服务"]},
                    {"code": "080209", "name": "机械工艺技术", "degree_type": "学士", "duration": 4, "keywords": ["机械工艺"]},
                    {"code": "080210", "name": "微机电系统工程", "degree_type": "学士", "duration": 4, "keywords": ["微机电", "MEMS"]},
                    {"code": "080211", "name": "机电技术教育", "degree_type": "学士", "duration": 4, "keywords": ["机电教育"]},
                    {"code": "080212", "name": "汽车维修工程教育", "degree_type": "学士", "duration": 4, "keywords": ["汽修"]},
                    {"code": "080213", "name": "智能制造工程", "degree_type": "学士", "duration": 4, "keywords": ["智能制造"]},
                    {"code": "080214", "name": "智能车辆工程", "degree_type": "学士", "duration": 4, "keywords": ["智能车辆"]},
                    {"code": "080215", "name": "仿生科学与工程", "degree_type": "学士", "duration": 4, "keywords": ["仿生"]},
                    {"code": "080216", "name": "新能源汽车工程", "degree_type": "学士", "duration": 4, "keywords": ["新能源汽车"]},
                    {"code": "080217", "name": "增材制造工程", "degree_type": "学士", "duration": 4, "keywords": ["增材制造", "3D打印"]},
                    {"code": "080218", "name": "智能交互设计", "degree_type": "学士", "duration": 4, "keywords": ["交互设计"]},
                    {"code": "080219", "name": "应急装备技术与工程", "degree_type": "学士", "duration": 4, "keywords": ["应急装备"]},
                ]
            },
            {
                "code": "0807",
                "name": "电子信息类",
                "majors": [
                    {"code": "080701", "name": "电子信息工程", "degree_type": "学士", "duration": 4, "keywords": ["电子信息", "EE"]},
                    {"code": "080702", "name": "电子科学与技术", "degree_type": "学士", "duration": 4, "keywords": ["电子科学"]},
                    {"code": "080703", "name": "通信工程", "degree_type": "学士", "duration": 4, "keywords": ["通信", "Telecom"]},
                    {"code": "080704", "name": "微电子科学与工程", "degree_type": "学士", "duration": 4, "keywords": ["微电子", "Microelectronics"]},
                    {"code": "080705", "name": "光电信息科学与工程", "degree_type": "学士", "duration": 4, "keywords": ["光电", "Optoelectronics"]},
                    {"code": "080706", "name": "信息工程", "degree_type": "学士", "duration": 4, "keywords": ["信息工程"]},
                    {"code": "080707", "name": "广播电视工程", "degree_type": "学士", "duration": 4, "keywords": ["广电"]},
                    {"code": "080708", "name": "水声工程", "degree_type": "学士", "duration": 4, "keywords": ["水声"]},
                    {"code": "080709", "name": "电子封装技术", "degree_type": "学士", "duration": 4, "keywords": ["电子封装"]},
                    {"code": "080710", "name": "集成电路设计与集成系统", "degree_type": "学士", "duration": 4, "keywords": ["集成电路", "IC设计"]},
                    {"code": "080711", "name": "医学信息工程", "degree_type": "学士", "duration": 4, "keywords": ["医学信息"]},
                    {"code": "080712", "name": "电磁场与无线技术", "degree_type": "学士", "duration": 4, "keywords": ["电磁场"]},
                    {"code": "080713", "name": "电波传播与天线", "degree_type": "学士", "duration": 4, "keywords": ["电波"]},
                    {"code": "080714", "name": "电子信息科学与技术", "degree_type": "学士", "duration": 4, "keywords": ["电子科学"]},
                    {"code": "080715", "name": "电信工程及管理", "degree_type": "学士", "duration": 4, "keywords": ["电信工程"]},
                    {"code": "080716", "name": "应用电子技术教育", "degree_type": "学士", "duration": 4, "keywords": ["电子技术教育"]},
                    {"code": "080717", "name": "人工智能", "degree_type": "学士", "duration": 4, "keywords": ["人工智能", "AI"]},
                    {"code": "080718", "name": "海洋信息工程", "degree_type": "学士", "duration": 4, "keywords": ["海洋信息"]},
                    {"code": "080719", "name": "柔性电子学", "degree_type": "学士", "duration": 4, "keywords": ["柔性电子"]},
                    {"code": "080720", "name": "智能测控工程", "degree_type": "学士", "duration": 4, "keywords": ["智能测控"]},
                    {"code": "080721", "name": "智能视觉工程", "degree_type": "学士", "duration": 4, "keywords": ["智能视觉"]},
                ]
            },
            {
                "code": "0809",
                "name": "计算机类",
                "majors": [
                    {"code": "080901", "name": "计算机科学与技术", "degree_type": "学士", "duration": 4, "keywords": ["计算机", "CS", "Computer Science"]},
                    {"code": "080902", "name": "软件工程", "degree_type": "学士", "duration": 4, "keywords": ["软件", "SE", "Software Engineering"]},
                    {"code": "080903", "name": "网络工程", "degree_type": "学士", "duration": 4, "keywords": ["网络", "Network"]},
                    {"code": "080904", "name": "信息安全", "degree_type": "学士", "duration": 4, "keywords": ["安全", "Security"]},
                    {"code": "080905", "name": "物联网工程", "degree_type": "学士", "duration": 4, "keywords": ["物联网", "IoT"]},
                    {"code": "080906", "name": "数字媒体技术", "degree_type": "学士", "duration": 4, "keywords": ["数媒", "Digital Media"]},
                    {"code": "080907", "name": "智能科学与技术", "degree_type": "学士", "duration": 4, "keywords": ["智能科学", "AI Science"]},
                    {"code": "080908", "name": "空间信息与数字技术", "degree_type": "学士", "duration": 4, "keywords": ["空间信息"]},
                    {"code": "080909", "name": "电子与计算机工程", "degree_type": "学士", "duration": 4, "keywords": ["电子计算机"]},
                    {"code": "080910", "name": "数据科学与大数据技术", "degree_type": "学士", "duration": 4, "keywords": ["数据科学", "大数据", "Big Data"]},
                    {"code": "080911", "name": "网络空间安全", "degree_type": "学士", "duration": 4, "keywords": ["网安", "Cyber Security"]},
                    {"code": "080912", "name": "新媒体技术", "degree_type": "学士", "duration": 4, "keywords": ["新媒体"]},
                    {"code": "080913", "name": "电影制作", "degree_type": "学士", "duration": 4, "keywords": ["电影"]},
                    {"code": "080914", "name": "保密技术", "degree_type": "学士", "duration": 4, "keywords": ["保密"]},
                    {"code": "080915", "name": "服务科学与工程", "degree_type": "学士", "duration": 4, "keywords": ["服务工程"]},
                    {"code": "080916", "name": "虚拟现实技术", "degree_type": "学士", "duration": 4, "keywords": ["VR", "虚拟现实"]},
                    {"code": "080917", "name": "区块链工程", "degree_type": "学士", "duration": 4, "keywords": ["区块链", "Blockchain"]},
                    {"code": "080918", "name": "密码科学与技术", "degree_type": "学士", "duration": 4, "keywords": ["密码学", "Cryptography"]},
                ]
            },
            {
                "code": "0810",
                "name": "土木类",
                "majors": [
                    {"code": "081001", "name": "土木工程", "degree_type": "学士", "duration": 4, "keywords": ["土木", "Civil Engineering"]},
                    {"code": "081002", "name": "建筑环境与能源应用工程", "degree_type": "学士", "duration": 4, "keywords": ["建环"]},
                    {"code": "081003", "name": "给排水科学与工程", "degree_type": "学士", "duration": 4, "keywords": ["给排水"]},
                    {"code": "081004", "name": "建筑电气与智能化", "degree_type": "学士", "duration": 4, "keywords": ["建筑电气"]},
                    {"code": "081005", "name": "城市地下空间工程", "degree_type": "学士", "duration": 4, "keywords": ["地下空间"]},
                    {"code": "081006", "name": "道路桥梁与渡河工程", "degree_type": "学士", "duration": 4, "keywords": ["道桥"]},
                    {"code": "081007", "name": "铁道工程", "degree_type": "学士", "duration": 4, "keywords": ["铁道"]},
                    {"code": "081008", "name": "智能建造", "degree_type": "学士", "duration": 4, "keywords": ["智能建造"]},
                    {"code": "081009", "name": "土木、水利与海洋工程", "degree_type": "学士", "duration": 4, "keywords": ["土木水利"]},
                    {"code": "081010", "name": "土木、水利与交通工程", "degree_type": "学士", "duration": 4, "keywords": ["土木交通"]},
                    {"code": "081011", "name": "城市水系统工程", "degree_type": "学士", "duration": 4, "keywords": ["城市水系统"]},
                    {"code": "081012", "name": "智能建造与智慧交通", "degree_type": "学士", "duration": 4, "keywords": ["智慧交通"]},
                    {"code": "081013", "name": "工程软件", "degree_type": "学士", "duration": 4, "keywords": ["工程软件"]},
                ]
            },
        ]
    },
    {
        "category": {"code": "12", "name": "管理学", "name_en": "Management"},
        "subcategories": [
            {
                "code": "1201",
                "name": "管理科学与工程类",
                "majors": [
                    {"code": "120101", "name": "管理科学", "degree_type": "学士", "duration": 4, "keywords": ["管理科学"]},
                    {"code": "120102", "name": "信息管理与信息系统", "degree_type": "学士", "duration": 4, "keywords": ["信管", "MIS"]},
                    {"code": "120103", "name": "工程管理", "degree_type": "学士", "duration": 4, "keywords": ["工程管理"]},
                    {"code": "120104", "name": "房地产开发与管理", "degree_type": "学士", "duration": 4, "keywords": ["房地产"]},
                    {"code": "120105", "name": "工程造价", "degree_type": "学士", "duration": 4, "keywords": ["造价"]},
                    {"code": "120106", "name": "保密管理", "degree_type": "学士", "duration": 4, "keywords": ["保密管理"]},
                    {"code": "120107", "name": "邮政管理", "degree_type": "学士", "duration": 4, "keywords": ["邮政"]},
                    {"code": "120108", "name": "大数据管理与应用", "degree_type": "学士", "duration": 4, "keywords": ["大数据管理"]},
                    {"code": "120109", "name": "工程审计", "degree_type": "学士", "duration": 4, "keywords": ["工程审计"]},
                    {"code": "120110", "name": "计算金融", "degree_type": "学士", "duration": 4, "keywords": ["计算金融"]},
                    {"code": "120111", "name": "应急管理", "degree_type": "学士", "duration": 4, "keywords": ["应急管理"]},
                ]
            },
            {
                "code": "1202",
                "name": "工商管理类",
                "majors": [
                    {"code": "120201", "name": "工商管理", "degree_type": "学士", "duration": 4, "keywords": ["工商管理", "MBA"]},
                    {"code": "120202", "name": "市场营销", "degree_type": "学士", "duration": 4, "keywords": ["营销", "Marketing"]},
                    {"code": "120203", "name": "会计学", "degree_type": "学士", "duration": 4, "keywords": ["会计", "Accounting"]},
                    {"code": "120204", "name": "财务管理", "degree_type": "学士", "duration": 4, "keywords": ["财务"]},
                    {"code": "120205", "name": "国际商务", "degree_type": "学士", "duration": 4, "keywords": ["国际商务"]},
                    {"code": "120206", "name": "人力资源管理", "degree_type": "学士", "duration": 4, "keywords": ["人力资源", "HR"]},
                    {"code": "120207", "name": "审计学", "degree_type": "学士", "duration": 4, "keywords": ["审计", "Audit"]},
                    {"code": "120208", "name": "资产评估", "degree_type": "学士", "duration": 4, "keywords": ["资产评估"]},
                    {"code": "120209", "name": "物业管理", "degree_type": "学士", "duration": 4, "keywords": ["物业"]},
                    {"code": "120210", "name": "文化产业管理", "degree_type": "学士", "duration": 4, "keywords": ["文化产业"]},
                    {"code": "120211", "name": "劳动关系", "degree_type": "学士", "duration": 4, "keywords": ["劳动关系"]},
                    {"code": "120212", "name": "体育经济与管理", "degree_type": "学士", "duration": 4, "keywords": ["体育管理"]},
                    {"code": "120213", "name": "财务会计教育", "degree_type": "学士", "duration": 4, "keywords": ["财会教育"]},
                    {"code": "120214", "name": "市场营销教育", "degree_type": "学士", "duration": 4, "keywords": ["营销教育"]},
                    {"code": "120215", "name": "零售业管理", "degree_type": "学士", "duration": 4, "keywords": ["零售管理"]},
                    {"code": "120216", "name": "创业管理", "degree_type": "学士", "duration": 4, "keywords": ["创业"]},
                    {"code": "120217", "name": "海关稽查", "degree_type": "学士", "duration": 4, "keywords": ["海关"]},
                ]
            },
        ]
    },
]


# ============ 职业分类数据 ============

CAREER_CATEGORIES_DATA = [
    {"code": "1", "name": "党的机关、国家机关、群众团体和社会组织、企事业单位负责人", "description": "各级党政机关、群团组织及企事业单位领导人员"},
    {"code": "2", "name": "专业技术人员", "description": "从事科学研究和专业技术工作的人员"},
    {"code": "3", "name": "办事人员和有关人员", "description": "从事行政业务、行政事务工作的人员"},
    {"code": "4", "name": "社会生产服务和生活服务人员", "description": "从事社会生产服务和生活服务工作的人员"},
    {"code": "5", "name": "农、林、牧、渔业生产及辅助人员", "description": "从事农、林、牧、渔业生产活动及辅助工作的人员"},
    {"code": "6", "name": "生产制造及有关人员", "description": "从事产品生产制造及辅助工作的人员"},
    {"code": "7", "name": "军人", "description": "现役军人"},
    {"code": "8", "name": "不便分类的其他从业人员", "description": "不便分类的其他从业人员"},
]


# 初始职业数据（IT/互联网相关）
INITIAL_CAREERS_DATA = [
    {
        "code": "2-02-10-01",
        "name": "后端开发工程师",
        "aliases": ["Java工程师", "服务端开发工程师", "Backend Developer"],
        "category_id": None,  # 将在导入时设置
        "description": "负责服务器端应用程序的设计和开发，处理业务逻辑、数据存储和API设计",
        "required_skills": ["Java/Python/Go", "MySQL/PostgreSQL", "Redis", "消息队列", "微服务"],
        "salary_range_min": 15000,
        "salary_range_max": 50000,
        "growth_path": "初级工程师 → 中级工程师 → 高级工程师 → 架构师/技术专家",
        "work_environment": "办公室/远程",
        "education_requirement": "本科及以上",
        "skills": [
            {"name": "Java", "category": "编程语言", "importance": 5, "is_required": True},
            {"name": "Spring Boot", "category": "框架", "importance": 5, "is_required": True},
            {"name": "MySQL", "category": "数据库", "importance": 5, "is_required": True},
            {"name": "Redis", "category": "缓存", "importance": 4, "is_required": True},
            {"name": "消息队列", "category": "中间件", "importance": 4, "is_required": False},
            {"name": "微服务", "category": "架构", "importance": 4, "is_required": False},
            {"name": "Docker", "category": "运维", "importance": 3, "is_required": False},
            {"name": "Linux", "category": "操作系统", "importance": 4, "is_required": True},
        ],
        "related_majors": ["080901", "080902", "080910"],  # 计算机、软件、数据科学
    },
    {
        "code": "2-02-10-02",
        "name": "前端开发工程师",
        "aliases": ["Web前端工程师", "Frontend Developer", "客户端开发工程师"],
        "category_id": None,
        "description": "负责用户界面和交互体验的开发，实现视觉效果和用户交互逻辑",
        "required_skills": ["HTML/CSS/JavaScript", "Vue/React/Angular", "前端工程化", "TypeScript"],
        "salary_range_min": 12000,
        "salary_range_max": 45000,
        "growth_path": "初级工程师 → 中级工程师 → 高级工程师 → 前端专家/架构师",
        "work_environment": "办公室/远程",
        "education_requirement": "本科及以上",
        "skills": [
            {"name": "JavaScript", "category": "编程语言", "importance": 5, "is_required": True},
            {"name": "Vue.js", "category": "框架", "importance": 5, "is_required": False},
            {"name": "React", "category": "框架", "importance": 5, "is_required": False},
            {"name": "HTML/CSS", "category": "基础", "importance": 5, "is_required": True},
            {"name": "TypeScript", "category": "编程语言", "importance": 4, "is_required": False},
            {"name": "Webpack", "category": "工具", "importance": 3, "is_required": False},
            {"name": "Node.js", "category": "运行时", "importance": 3, "is_required": False},
        ],
        "related_majors": ["080901", "080902", "080906"],  # 计算机、软件、数字媒体
    },
    {
        "code": "2-02-10-03",
        "name": "算法工程师",
        "aliases": ["机器学习工程师", "AI工程师", "Algorithm Engineer"],
        "category_id": None,
        "description": "负责机器学习算法的研究、开发和应用，解决复杂的业务问题",
        "required_skills": ["Python", "机器学习", "深度学习框架", "数学基础", "数据结构与算法"],
        "salary_range_min": 20000,
        "salary_range_max": 60000,
        "growth_path": "算法工程师 → 高级算法工程师 → 算法专家 → 首席科学家",
        "work_environment": "办公室",
        "education_requirement": "硕士及以上",
        "skills": [
            {"name": "Python", "category": "编程语言", "importance": 5, "is_required": True},
            {"name": "机器学习", "category": "AI/ML", "importance": 5, "is_required": True},
            {"name": "深度学习", "category": "AI/ML", "importance": 5, "is_required": True},
            {"name": "TensorFlow/PyTorch", "category": "框架", "importance": 5, "is_required": True},
            {"name": "数学建模", "category": "基础", "importance": 5, "is_required": True},
            {"name": "数据结构", "category": "基础", "importance": 4, "is_required": True},
            {"name": "NLP/CV", "category": "AI/ML", "importance": 4, "is_required": False},
        ],
        "related_majors": ["080901", "080907", "080910", "071201"],  # 计算机、智能科学、数据科学、统计学
    },
    {
        "code": "2-02-10-04",
        "name": "数据分析师",
        "aliases": ["数据工程师", "商业分析师", "Data Analyst"],
        "category_id": None,
        "description": "通过数据挖掘和分析为业务决策提供支持，产出数据报告和洞察",
        "required_skills": ["SQL", "Python/R", "数据可视化", "统计学", "业务理解"],
        "salary_range_min": 12000,
        "salary_range_max": 40000,
        "growth_path": "数据分析师 → 高级分析师 → 数据分析专家 → 数据总监",
        "work_environment": "办公室",
        "education_requirement": "本科及以上",
        "skills": [
            {"name": "SQL", "category": "数据库", "importance": 5, "is_required": True},
            {"name": "Python", "category": "编程语言", "importance": 4, "is_required": False},
            {"name": "Excel", "category": "工具", "importance": 4, "is_required": True},
            {"name": "Tableau/PowerBI", "category": "可视化", "importance": 4, "is_required": False},
            {"name": "统计学", "category": "基础", "importance": 4, "is_required": True},
            {"name": "数据挖掘", "category": "分析方法", "importance": 3, "is_required": False},
        ],
        "related_majors": ["071201", "020102", "080910"],  # 统计学、经济统计、数据科学
    },
    {
        "code": "2-02-10-05",
        "name": "运维工程师",
        "aliases": ["SRE", "DevOps工程师", "系统工程师"],
        "category_id": None,
        "description": "负责系统稳定性、自动化运维、云基础设施管理和DevOps实践",
        "required_skills": ["Linux", "Docker/Kubernetes", "CI/CD", "监控告警", "云原生"],
        "salary_range_min": 12000,
        "salary_range_max": 40000,
        "growth_path": "运维工程师 → SRE → 运维专家 → 运维架构师",
        "work_environment": "办公室/轮班",
        "education_requirement": "本科及以上",
        "skills": [
            {"name": "Linux", "category": "操作系统", "importance": 5, "is_required": True},
            {"name": "Docker", "category": "容器", "importance": 5, "is_required": True},
            {"name": "Kubernetes", "category": "容器编排", "importance": 4, "is_required": False},
            {"name": "Shell/Python", "category": "脚本", "importance": 4, "is_required": True},
            {"name": "Jenkins", "category": "CI/CD", "importance": 4, "is_required": False},
            {"name": "Prometheus", "category": "监控", "importance": 3, "is_required": False},
            {"name": "AWS/阿里云", "category": "云平台", "importance": 4, "is_required": False},
        ],
        "related_majors": ["080901", "080903"],  # 计算机、网络工程
    },
    {
        "code": "2-02-10-06",
        "name": "产品经理",
        "aliases": ["PM", "产品专员", "Product Manager"],
        "category_id": None,
        "description": "负责产品规划、需求分析和项目管理，协调技术、设计和业务团队",
        "required_skills": ["需求分析", "产品设计", "数据分析", "沟通协调", "项目管理"],
        "salary_range_min": 15000,
        "salary_range_max": 50000,
        "growth_path": "产品助理 → 产品经理 → 高级产品经理 → 产品总监",
        "work_environment": "办公室",
        "education_requirement": "本科及以上",
        "skills": [
            {"name": "需求分析", "category": "产品能力", "importance": 5, "is_required": True},
            {"name": "Axure/Figma", "category": "工具", "importance": 4, "is_required": False},
            {"name": "数据分析", "category": "分析能力", "importance": 4, "is_required": True},
            {"name": "项目管理", "category": "管理能力", "importance": 4, "is_required": True},
            {"name": "用户研究", "category": "产品能力", "importance": 4, "is_required": False},
            {"name": "沟通协调", "category": "软技能", "importance": 5, "is_required": True},
        ],
        "related_majors": ["080901", "120201", "120202"],  # 计算机、工商管理、市场营销
    },
    {
        "code": "2-02-10-07",
        "name": "嵌入式开发工程师",
        "aliases": ["单片机工程师", "Firmware Engineer"],
        "category_id": None,
        "description": "开发嵌入式系统和物联网设备软件，涉及底层驱动和固件开发",
        "required_skills": ["C/C++", "RTOS", "硬件原理", "通信协议", "ARM/MIPS"],
        "salary_range_min": 12000,
        "salary_range_max": 35000,
        "growth_path": "嵌入式工程师 → 高级工程师 → 架构师 → 技术总监",
        "work_environment": "办公室/实验室",
        "education_requirement": "本科及以上",
        "skills": [
            {"name": "C/C++", "category": "编程语言", "importance": 5, "is_required": True},
            {"name": "RTOS", "category": "操作系统", "importance": 4, "is_required": True},
            {"name": "ARM", "category": "硬件", "importance": 4, "is_required": True},
            {"name": "通信协议", "category": "协议", "importance": 4, "is_required": True},
            {"name": "硬件原理", "category": "硬件", "importance": 3, "is_required": True},
        ],
        "related_majors": ["080701", "080703", "080704"],  # 电子信息、通信、微电子
    },
    {
        "code": "2-02-10-08",
        "name": "测试工程师",
        "aliases": ["QA工程师", "质量保障工程师", "Test Engineer"],
        "category_id": None,
        "description": "负责软件质量保证，设计测试用例，执行测试并输出报告",
        "required_skills": ["测试理论", "自动化测试", "Python/Java", "性能测试", "缺陷管理"],
        "salary_range_min": 10000,
        "salary_range_max": 35000,
        "growth_path": "测试工程师 → 高级测试工程师 → 测试专家 → 质量总监",
        "work_environment": "办公室",
        "education_requirement": "本科及以上",
        "skills": [
            {"name": "功能测试", "category": "测试", "importance": 5, "is_required": True},
            {"name": "自动化测试", "category": "测试", "importance": 4, "is_required": False},
            {"name": "Selenium", "category": "工具", "importance": 4, "is_required": False},
            {"name": "JMeter", "category": "性能测试", "importance": 3, "is_required": False},
            {"name": "Python", "category": "编程语言", "importance": 4, "is_required": False},
        ],
        "related_majors": ["080901", "080902"],  # 计算机、软件
    },
]


# ============ 招聘平台配置 ============

JOB_PLATFORMS_DATA = [
    {
        "name": "智联招聘",
        "code": "zhaopin",
        "api_endpoint": "https://api.zhaopin.com",
        "is_active": True,
        "rate_limit": 100,
    },
    {
        "name": "BOSS直聘",
        "code": "boss",
        "api_endpoint": "https://api.zhipin.com",
        "is_active": True,
        "rate_limit": 100,
    },
    {
        "name": "拉勾网",
        "code": "lagou",
        "api_endpoint": "https://api.lagou.com",
        "is_active": True,
        "rate_limit": 100,
    },
    {
        "name": "前程无忧",
        "code": "51job",
        "api_endpoint": "https://api.51job.com",
        "is_active": True,
        "rate_limit": 100,
    },
]


async def init_major_categories(db):
    """Initialize major categories"""
    for category_data in MOE_MAJORS_DATA:
        cat = category_data["category"]
        stmt = insert(major_categories).values(
            code=cat["code"],
            name=cat["name"],
            name_en=cat.get("name_en"),
            description=cat.get("description")
        ).on_conflict_do_nothing(index_elements=["code"])
        await db.execute(stmt)
    await db.commit()
    print(f" Initialized {len(MOE_MAJORS_DATA)} major categories")


async def init_major_subcategories(db):
    """Initialize major subcategories"""
    count = 0
    for category_data in MOE_MAJORS_DATA:
        cat_result = await db.execute(
            select(major_categories.c.id).where(major_categories.c.code == category_data["category"]["code"])
        )
        cat_id = cat_result.scalar()

        for sub_data in category_data["subcategories"]:
            stmt = insert(major_subcategories).values(
                category_id=cat_id,
                code=sub_data["code"],
                name=sub_data["name"],
                description=sub_data.get("description")
            ).on_conflict_do_nothing(index_elements=["code"])
            await db.execute(stmt)
            count += 1
    await db.commit()
    print(f" Initialized {count} major subcategories")


async def init_majors(db):
    """Initialize majors"""
    count = 0
    for category_data in MOE_MAJORS_DATA:
        for sub_data in category_data["subcategories"]:
            sub_result = await db.execute(
                select(major_subcategories.c.id).where(major_subcategories.c.code == sub_data["code"])
            )
            sub_id = sub_result.scalar()

            for major_data in sub_data["majors"]:
                stmt = insert(majors).values(
                    subcategory_id=sub_id,
                    code=major_data["code"],
                    name=major_data["name"],
                    degree_type=major_data.get("degree_type"),
                    duration=major_data.get("duration"),
                    keywords=major_data.get("keywords", [])
                ).on_conflict_do_nothing(index_elements=["code"])
                await db.execute(stmt)
                count += 1
    await db.commit()
    print(f" Initialized {count} majors")


async def init_career_categories(db):
    """Initialize career categories"""
    for cat_data in CAREER_CATEGORIES_DATA:
        stmt = insert(career_categories).values(
            code=cat_data["code"],
            name=cat_data["name"],
            description=cat_data.get("description")
        ).on_conflict_do_nothing(index_elements=["code"])
        await db.execute(stmt)
    await db.commit()
    print(f" Initialized {len(CAREER_CATEGORIES_DATA)} career categories")


async def init_career_skills(db, db_skills: dict):
    """Initialize career skills and return skill name -> id mapping"""
    skill_ids = {}

    for career_data in INITIAL_CAREERS_DATA:
        for skill_data in career_data.get("skills", []):
            skill_name = skill_data["name"]
            if skill_name not in skill_ids:
                # Insert skill
                stmt = insert(career_skills).values(
                    name=skill_name,
                    category=skill_data.get("category"),
                    description=None
                ).on_conflict_do_nothing(index_elements=["name"])
                await db.execute(stmt)

    await db.commit()

    # Get all skill IDs
    result = await db.execute(select(career_skills.c.id, career_skills.c.name))
    for row in result:
        skill_ids[row.name] = row.id

    print(f" Initialized {len(skill_ids)} career skills")
    return skill_ids


async def init_careers(db, skill_ids: dict):
    """Initialize careers and their skill mappings"""
    # Get the "专业技术人员" category ID
    cat_result = await db.execute(
        select(career_categories.c.id).where(career_categories.c.code == "2")
    )
    category_id = cat_result.scalar()

    career_ids = {}

    for career_data in INITIAL_CAREERS_DATA:
        # Insert career
        stmt = insert(careers).values(
            category_id=category_id,
            code=career_data["code"],
            name=career_data["name"],
            aliases=career_data.get("aliases", []),
            description=career_data.get("description"),
            required_skills=career_data.get("required_skills", []),
            salary_range_min=career_data.get("salary_range_min"),
            salary_range_max=career_data.get("salary_range_max"),
            growth_path=career_data.get("growth_path"),
            work_environment=career_data.get("work_environment"),
            education_requirement=career_data.get("education_requirement"),
        ).on_conflict_do_nothing(index_elements=["code"])
        await db.execute(stmt)

    await db.commit()

    # Get all career IDs
    result = await db.execute(select(careers.c.id, careers.c.code))
    for row in result:
        career_ids[row.code] = row.id

    # Insert skill mappings
    for career_data in INITIAL_CAREERS_DATA:
        career_id = career_ids.get(career_data["code"])
        if not career_id:
            continue

        for skill_data in career_data.get("skills", []):
            skill_id = skill_ids.get(skill_data["name"])
            if skill_id:
                stmt = insert(career_skill_mappings).values(
                    career_id=career_id,
                    skill_id=skill_id,
                    importance=skill_data.get("importance", 3),
                    is_required=skill_data.get("is_required", True)
                ).on_conflict_do_nothing(constraint="uq_career_skill")
                await db.execute(stmt)

    await db.commit()
    print(f" Initialized {len(career_ids)} careers with skill mappings")
    return career_ids


async def init_major_career_mappings(db, career_ids: dict):
    """Initialize major-career mappings"""
    count = 0

    for career_data in INITIAL_CAREERS_DATA:
        career_id = career_ids.get(career_data["code"])
        if not career_id:
            continue

        for i, major_code in enumerate(career_data.get("related_majors", [])):
            major_result = await db.execute(
                select(majors.c.id).where(majors.c.code == major_code)
            )
            major_id = major_result.scalar()

            if major_id:
                stmt = insert(major_career_mappings).values(
                    major_id=major_id,
                    career_id=career_id,
                    match_score=90 if i == 0 else 80,
                    is_primary=(i == 0)
                ).on_conflict_do_nothing(constraint="uq_major_career")
                await db.execute(stmt)
                count += 1

    await db.commit()
    print(f" Initialized {count} major-career mappings")


async def init_job_platforms(db):
    """Initialize job platforms"""
    for platform_data in JOB_PLATFORMS_DATA:
        stmt = insert(job_platforms).values(
            name=platform_data["name"],
            code=platform_data["code"],
            api_endpoint=platform_data.get("api_endpoint"),
            is_active=platform_data.get("is_active", True),
            rate_limit=platform_data.get("rate_limit", 100)
        ).on_conflict_do_nothing(index_elements=["code"])
        await db.execute(stmt)
    await db.commit()
    print(f" Initialized {len(JOB_PLATFORMS_DATA)} job platforms")


async def main():
    """Main initialization function"""
    print("Starting career and major data initialization...\n")

    async with async_session_factory() as db:
        try:
            # Initialize major system
            print(" Initializing major system...")
            await init_major_categories(db)
            await init_major_subcategories(db)
            await init_majors(db)

            # Initialize career system
            print("\n Initializing career system...")
            await init_career_categories(db)
            skill_ids = await init_career_skills(db, {})
            career_ids = await init_careers(db, skill_ids)
            await init_major_career_mappings(db, career_ids)

            # Initialize job platforms
            print("\n Initializing job platforms...")
            await init_job_platforms(db)

            print("\n Initialization completed successfully!")

        except Exception as e:
            print(f"\n Error during initialization: {e}")
            await db.rollback()
            raise


if __name__ == "__main__":
    asyncio.run(main())
