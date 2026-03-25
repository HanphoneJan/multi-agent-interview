"""Benchmark test data for AI Interview Evaluation System

This module contains test datasets for evaluating the accuracy and reliability
of the AI interview scoring system.
"""

# ============ 单题回答样本（Golden Dataset） ============

SINGLE_ANSWER_BENCHMARK = [
    {
        "id": "A001",
        "category": "technical_excellent",
        "question": "解释 Python 的 GIL 机制",
        "answer": """Python 的 GIL（全局解释器锁）是一种机制，用于保护对 Python 对象的访问，防止多线程同时执行 Python 字节码。

主要特点：
1. GIL 确保任何时候只有一个线程在执行 Python 字节码
2. 它简化了 CPython 的内存管理，避免复杂的锁机制
3. 对于 I/O 密集型任务，多线程仍然有效
4. 对于 CPU 密集型任务，建议使用多进程而非多线程

优缺点：
- 优点：简化解释器实现，避免大量的细粒度锁
- 缺点：限制了多线程的并行性能，在多核 CPU 上无法充分利用资源

解决方案：
- 使用 multiprocessing 模块进行真正的并行计算
- 使用 C 扩展释放 GIL（如 NumPy）
- 使用异步编程（asyncio）处理 I/O 密集型任务""",
        "expected_score": 0.85,
        "expected_strengths_count": 3,
        "expected_weaknesses_count": 1
    },
    {
        "id": "A002",
        "category": "technical_poor",
        "question": "什么是数据库索引？",
        "answer": "不知道，没学过",
        "expected_score": 0.15,
        "expected_strengths_count": 0,
        "expected_weaknesses_count": 2
    },
    {
        "id": "A003",
        "category": "technical_good",
        "question": "解释 RESTful API 设计原则",
        "answer": """RESTful API 是一种基于 HTTP 协议的 API 设计风格，主要原则包括：

1. 资源导向：使用 URL 表示资源，如 /users/123
2. HTTP 方法：GET 获取、POST 创建、PUT 更新、DELETE 删除
3. 无状态：每个请求独立，服务器不保存客户端状态
4. 统一接口：使用标准的 HTTP 状态码和内容类型

优点：简单、可扩展、易于理解和使用。""",
        "expected_score": 0.70,
        "expected_strengths_count": 2,
        "expected_weaknesses_count": 1
    },
    {
        "id": "A004",
        "category": "technical_average",
        "question": "什么是死锁？如何避免？",
        "answer": "死锁就是两个进程互相等待对方释放资源。避免方法是不要同时占用多个资源。",
        "expected_score": 0.45,
        "expected_strengths_count": 1,
        "expected_weaknesses_count": 2
    },
    {
        "id": "A005",
        "category": "behavioral_excellent",
        "question": "描述一次你解决团队冲突的经历",
        "answer": """在上一份工作期间，我们团队两位资深开发者在技术选型上产生了严重分歧：一位主张使用微服务架构，另一位坚持单体架构。

我采取的解决步骤：
1. 分别沟通：单独与两位同事交流，了解各自的顾虑和理由
2. 收集数据：整理了项目需求、团队规模、维护成本等客观数据
3. 组织讨论：召集技术评审会议，让双方充分表达观点
4. 寻求共识：提出渐进式方案——先保持单体，但按模块划分，为未来微服务预留接口

最终结果：
- 双方都能接受这个折中方案
- 项目按时交付，后期也确实顺利迁移到微服务
- 团队关系更加融洽，建立了更好的沟通机制

这次经历让我认识到，技术决策需要兼顾技术合理性和团队和谐。""",
        "expected_score": 0.88,
        "expected_strengths_count": 3,
        "expected_weaknesses_count": 0
    },
    {
        "id": "A006",
        "category": "behavioral_poor",
        "question": "你最大的缺点是什么？",
        "answer": "我没有缺点，我觉得我各方面都很完美。",
        "expected_score": 0.20,
        "expected_strengths_count": 0,
        "expected_weaknesses_count": 3
    },
    {
        "id": "A007",
        "category": "behavioral_good",
        "question": "为什么选择我们公司？",
        "answer": """我选择贵公司主要有三个原因：

第一，贵公司在人工智能领域的领先地位吸引了我，我一直关注贵公司发布的开源模型和技术博客。

第二，这个岗位与我的专业背景和职业规划高度匹配，我希望在 NLP 方向深入发展。

第三，贵公司的企业文化强调创新和协作，这正是我理想的工作环境。

我相信在这里能够获得快速成长的机会，同时也能为团队贡献价值。""",
        "expected_score": 0.75,
        "expected_strengths_count": 2,
        "expected_weaknesses_count": 1
    },
    {
        "id": "A008",
        "category": "problem_solving_excellent",
        "question": "如何设计一个高并发的秒杀系统？",
        "answer": """设计高并发秒杀系统需要考虑多个层面：

**1. 前端优化**
- 静态化：商品详情页 CDN 缓存
- 限流：验证码、答题防刷
- 错峰：分时段开放购买

**2. 网关层**
- Nginx 限流：限制单个 IP 访问频率
- 黑名单：识别并拦截恶意请求
- 负载均衡：多实例分摊压力

**3. 应用层**
- Redis 预减库存：避免直接访问数据库
- 异步处理：使用消息队列削峰填谷
- 令牌桶算法：控制流量速率

**4. 数据库层**
- 乐观锁：版本号控制并发更新
- 分库分表：分散数据压力
- 读写分离：查询走从库

**5. 兜底方案**
- 降级策略：非核心功能关闭
- 熔断机制：防止雪崩效应
- 库存预热：提前加载到缓存

这样的架构可以支撑百万级并发，同时保证数据一致性。""",
        "expected_score": 0.90,
        "expected_strengths_count": 4,
        "expected_weaknesses_count": 0
    },
    {
        "id": "A009",
        "category": "problem_solving_average",
        "question": "如何查找数组中的重复元素？",
        "answer": "可以用哈希表，遍历数组，把每个元素放进去，如果发现已经存在就是重复的。时间复杂度 O(n)。",
        "expected_score": 0.55,
        "expected_strengths_count": 1,
        "expected_weaknesses_count": 2
    },
    {
        "id": "A010",
        "category": "communication_excellent",
        "question": "如何向非技术人员解释技术方案？",
        "answer": """向非技术人员解释技术方案，我遵循以下原则：

**1. 了解受众**
- 先了解对方的背景知识和关注点
- 用他们熟悉的业务语言而非技术术语

**2. 类比说明**
- 将技术概念映射到日常生活场景
- 例如：把数据库索引比作书的目录
- 把缓存比作办公桌上的常用文件

**3. 可视化**
- 使用流程图、架构图辅助说明
- 一图胜千言

**4. 聚焦价值**
- 强调技术方案解决什么业务问题
- 说明投入产出比
- 用数据说话：性能提升 XX%，成本降低 XX%

**5. 互动确认**
- 讲解过程中观察对方反应
- 适时提问确认理解程度
- 预留答疑时间

实际案例：曾向财务总监解释数据仓库方案，用"整理杂乱的文件柜"作类比，成功获得预算批准。""",
        "expected_score": 0.85,
        "expected_strengths_count": 3,
        "expected_weaknesses_count": 0
    },
    {
        "id": "A011",
        "category": "communication_poor",
        "question": "描述一次你与产品经理的沟通经历",
        "answer": "就正常沟通啊，他说需求我做，没什么好说的。",
        "expected_score": 0.25,
        "expected_strengths_count": 0,
        "expected_weaknesses_count": 2
    },
    {
        "id": "A012",
        "category": "technical_deep",
        "question": "Redis 持久化机制有哪些？各有什么优缺点？",
        "answer": """Redis 提供两种持久化机制：RDB 和 AOF。

**RDB（快照）**
- 原理：定期将内存数据快照保存到磁盘
- 优点：文件紧凑，恢复速度快，适合备份
- 缺点：可能丢失最后一次快照后的数据

**AOF（日志）**
- 原理：记录每个写操作命令
- 优点：数据安全性高，可配置每秒同步或实时同步
- 缺点：文件较大，恢复速度较慢

**混合模式（Redis 4.0+）**
- RDB 做全量，AOF 做增量
- 兼顾恢复速度和数据安全

选择建议：
- 对数据安全性要求高：AOF
- 对性能要求高，可容忍少量数据丢失：RDB
- 生产环境推荐：混合模式""",
        "expected_score": 0.80,
        "expected_strengths_count": 3,
        "expected_weaknesses_count": 1
    },
    {
        "id": "A013",
        "category": "learning_ability",
        "question": "最近在学习什么新技术？",
        "answer": """最近我在系统学习 Rust 语言，主要动机是提升系统编程能力。

**学习路径：**
1. 官方文档《The Rust Programming Language》
2. 小项目实践：实现 HTTP 服务器、命令行工具
3. 阅读开源项目：tokio、serde 的源码

**遇到的挑战：**
- 所有权和生命周期概念初期较难理解
- 解决：通过大量练习和画图分析内存模型

**应用计划：**
- 计划用 Rust 重写现有 Python 服务的性能瓶颈模块
- 目标是将关键路径延迟降低 50%

通过这个过程，我不仅掌握了 Rust，更深刻理解了内存安全和零成本抽象的设计理念。""",
        "expected_score": 0.82,
        "expected_strengths_count": 3,
        "expected_weaknesses_count": 0
    },
    {
        "id": "A014",
        "category": "vague_answer",
        "question": "你的职业规划是什么？",
        "answer": "努力工作，争取升职，为公司做贡献。",
        "expected_score": 0.35,
        "expected_strengths_count": 0,
        "expected_weaknesses_count": 2
    },
    {
        "id": "A015",
        "category": "technical_excellent",
        "question": "MySQL 索引底层原理是什么？",
        "answer": """MySQL 索引主要基于 B+ 树实现，以下是其核心原理：

**B+ 树结构特点：**
- 非叶子节点只存键值，不存数据，可存放更多索引
- 叶子节点通过指针相连，支持范围查询
- 所有查询都要走到叶子节点，查询效率稳定

**InnoDB 索引类型：**
1. 聚簇索引：叶子节点存完整行数据，按主键排序
2. 二级索引：叶子节点存主键值，需回表查完整数据

**索引优化原则：**
- 最左前缀原则：复合索引从左到右匹配
- 覆盖索引：查询字段都在索引中，避免回表
- 索引下推：在存储引擎层过滤数据，减少回表次数

**其他索引类型：**
- Hash 索引：精确查找快，不支持范围查询
- 全文索引：用于文本搜索
- 空间索引：用于地理数据

理解索引原理对 SQL 优化至关重要。""",
        "expected_score": 0.87,
        "expected_strengths_count": 3,
        "expected_weaknesses_count": 0
    },
    {
        "id": "A016",
        "category": "boundary_empty",
        "question": "你有什么问题要问我吗？",
        "answer": "",
        "expected_score": 0.10,
        "expected_strengths_count": 0,
        "expected_weaknesses_count": 1
    },
    {
        "id": "A017",
        "category": "boundary_short",
        "question": "介绍一下你自己",
        "answer": "我叫张三。",
        "expected_score": 0.30,
        "expected_strengths_count": 0,
        "expected_weaknesses_count": 2
    },
    {
        "id": "A018",
        "category": "irrelevant",
        "question": "什么是 Docker？",
        "answer": "Docker 是一种编程语言，主要用于开发移动应用，由 Google 开发。",
        "expected_score": 0.20,
        "expected_strengths_count": 0,
        "expected_weaknesses_count": 3
    },
    {
        "id": "A019",
        "category": "code_quality",
        "question": "这段代码有什么问题？如何优化？",
        "answer": """代码：
```python
def get_user_data(user_id):
    users = db.query("SELECT * FROM users")
    for user in users:
        if user['id'] == user_id:
            return user
    return None
```

问题分析：
1. **SQL 注入风险**：直接拼接 SQL 字符串
2. **性能问题**：查询全表再过滤，未使用索引
3. **内存浪费**：一次性加载所有用户数据
4. **错误处理缺失**：没有处理数据库连接异常

优化方案：
```python
def get_user_data(user_id: int) -> Optional[Dict]:
    try:
        with db.connection() as conn:
            cursor = conn.execute(
                "SELECT id, name, email FROM users WHERE id = %s",
                (user_id,)
            )
            return cursor.fetchone()
    except DatabaseError as e:
        logger.error(f"Failed to get user {user_id}: {e}")
        raise UserNotFoundError(f"User {user_id} not found")
```

优化点：
- 使用参数化查询防止 SQL 注入
- 添加 WHERE 条件利用索引
- 只查询需要的字段
- 添加类型注解和错误处理""",
        "expected_score": 0.92,
        "expected_strengths_count": 4,
        "expected_weaknesses_count": 0
    },
    {
        "id": "A020",
        "category": "system_design",
        "question": "设计一个短链接服务",
        "answer": """短链接服务（如 bit.ly）设计考虑：

**核心功能：**
- 长链接 → 短链接映射
- 短链接重定向
- 访问统计

**架构设计：**
```
Client → Load Balancer → API Server → Cache → Database
                            ↓
                        Analytics Queue
```

**关键算法：**
1. **哈希算法**：MD5/SHA 后取前 7 位，冲突时+1重试
2. **Base62 编码**：将自增 ID 转为 62 进制（a-zA-Z0-9）
3. **预生成**：提前生成短码放入池子，减少实时计算

**数据库设计：**
```sql
CREATE TABLE short_urls (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    short_code VARCHAR(7) UNIQUE NOT NULL,
    long_url VARCHAR(2048) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NULL,
    click_count INT DEFAULT 0
);

CREATE INDEX idx_short_code ON short_urls(short_code);
```

**性能优化：**
- 缓存热点数据（Redis，TTL 24h）
- 读写分离，查询走从库
- 布隆过滤器防止缓存穿透

**扩展考虑：**
- 自定义短码（付费功能）
- 访问限流（防滥用）
- 链接安全检测（防钓鱼）""",
        "expected_score": 0.88,
        "expected_strengths_count": 3,
        "expected_weaknesses_count": 1
    },
]

# ============ 边界测试集 ============

BOUNDARY_TEST_CASES = [
    {
        "id": "B001",
        "type": "empty",
        "question": "请描述你的项目经验",
        "answer": "",
        "description": "空回答"
    },
    {
        "id": "B002",
        "type": "single_char",
        "question": "请介绍你自己",
        "answer": "a",
        "description": "单字符回答"
    },
    {
        "id": "B003",
        "type": "chinese_single",
        "question": "请介绍你自己",
        "answer": "是",
        "description": "单中文字符"
    },
    {
        "id": "B004",
        "type": "emoji",
        "question": "你有什么爱好？",
        "answer": "😀🎮🏃‍♂️📚🎬",
        "description": "纯表情符号"
    },
    {
        "id": "B005",
        "type": "code_only",
        "question": "写一个快速排序",
        "answer": """```python
def quicksort(arr):
    if len(arr) <= 1:
        return arr
    pivot = arr[len(arr) // 2]
    left = [x for x in arr if x < pivot]
    middle = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]
    return quicksort(left) + middle + quicksort(right)
```""",
        "description": "纯代码块"
    },
    {
        "id": "B006",
        "type": "long_answer",
        "question": "介绍你的工作经历",
        "answer": "我在 A 公司工作" * 500,  # 约 2500 字
        "description": "超长回答（>2000字）"
    },
    {
        "id": "B007",
        "type": "special_chars",
        "question": "你有什么问题？",
        "answer": "<script>alert('xss')</script> &nbsp; \n\t\r \x00\x01\x02",
        "description": "特殊字符和 HTML"
    },
    {
        "id": "B008",
        "type": "gibberish",
        "question": "解释什么是 MVC",
        "answer": "asdf qwer zxcv mvc is good framework model view controller blah blah",
        "description": "无意义文本"
    },
    {
        "id": "B009",
        "type": "repeated",
        "question": "你的优势是什么？",
        "answer": "学习能力强 " * 100,
        "description": "重复内容"
    },
    {
        "id": "B010",
        "type": "none_value",
        "question": "测试问题",
        "answer": None,
        "description": "None 值"
    },
]

# ============ 完整面试样本 ============

FULL_INTERVIEW_BENCHMARK = [
    {
        "session_id": "S001",
        "category": "senior_candidate",
        "description": "资深后端工程师候选人",
        "qa_pairs": [
            {
                "question": "请介绍你最熟悉的项目",
                "answer": SINGLE_ANSWER_BENCHMARK[4]["answer"]  # 团队冲突解决
            },
            {
                "question": "如何设计一个高并发秒杀系统？",
                "answer": SINGLE_ANSWER_BENCHMARK[7]["answer"]
            },
            {
                "question": "Redis 持久化机制有哪些？",
                "answer": SINGLE_ANSWER_BENCHMARK[11]["answer"]
            },
            {
                "question": "描述一次解决技术难题的经历",
                "answer": SINGLE_ANSWER_BENCHMARK[9]["answer"]  # 非技术人员沟通
            }
        ],
        "expected_overall_score": 82,
        "expected_dimension_range": {
            "professional_knowledge": [75, 90],
            "skill_match": [80, 95],
            "language_expression": [75, 85],
            "logical_thinking": [80, 90],
            "stress_response": [70, 85],
            "personality": [75, 90],
            "motivation": [75, 90],
            "value": [75, 90]
        }
    },
    {
        "session_id": "S002",
        "category": "junior_candidate",
        "description": "初级前端工程师候选人",
        "qa_pairs": [
            {
                "question": "介绍一下 CSS 盒模型",
                "answer": "CSS 盒模型包括 content、padding、border 和 margin。标准盒模型中 width 只包含 content，而 IE 盒模型中 width 包含 content+padding+border。可以通过 box-sizing 属性切换。"
            },
            {
                "question": "什么是闭包？",
                "answer": "闭包是函数和声明该函数的词法环境的组合。简单说就是内部函数可以访问外部函数的变量，即使外部函数已经执行完毕。常用于数据封装和模块化。"
            },
            {
                "question": "为什么想来我们公司？",
                "answer": SINGLE_ANSWER_BENCHMARK[6]["answer"]
            }
        ],
        "expected_overall_score": 65,
        "expected_dimension_range": {
            "professional_knowledge": [60, 75],
            "skill_match": [60, 75],
            "language_expression": [65, 80],
            "logical_thinking": [60, 75],
            "stress_response": [65, 80],
            "personality": [70, 85],
            "motivation": [70, 85],
            "value": [65, 80]
        }
    },
    {
        "session_id": "S003",
        "category": "poor_candidate",
        "description": "表现不佳的候选人",
        "qa_pairs": [
            {
                "question": "介绍一下你自己",
                "answer": SINGLE_ANSWER_BENCHMARK[17]["answer"]  # 很短
            },
            {
                "question": "你有什么缺点？",
                "answer": SINGLE_ANSWER_BENCHMARK[5]["answer"]  # 没有缺点
            },
            {
                "question": "你的职业规划是什么？",
                "answer": SINGLE_ANSWER_BENCHMARK[13]["answer"]  # 很模糊
            }
        ],
        "expected_overall_score": 35,
        "expected_dimension_range": {
            "professional_knowledge": [30, 50],
            "skill_match": [30, 50],
            "language_expression": [35, 55],
            "logical_thinking": [30, 50],
            "stress_response": [40, 60],
            "personality": [40, 60],
            "motivation": [30, 50],
            "value": [40, 60]
        }
    },
    {
        "session_id": "S004",
        "category": "excellent_candidate",
        "description": "优秀候选人",
        "qa_pairs": [
            {
                "question": "设计一个短链接服务",
                "answer": SINGLE_ANSWER_BENCHMARK[19]["answer"]
            },
            {
                "question": "这段代码有什么问题？",
                "answer": SINGLE_ANSWER_BENCHMARK[18]["answer"]
            },
            {
                "question": "MySQL 索引原理",
                "answer": SINGLE_ANSWER_BENCHMARK[14]["answer"]
            },
            {
                "question": "Python GIL 机制",
                "answer": SINGLE_ANSWER_BENCHMARK[0]["answer"]
            }
        ],
        "expected_overall_score": 88,
        "expected_dimension_range": {
            "professional_knowledge": [85, 95],
            "skill_match": [85, 95],
            "language_expression": [80, 90],
            "logical_thinking": [85, 95],
            "stress_response": [75, 90],
            "personality": [80, 90],
            "motivation": [85, 95],
            "value": [80, 90]
        }
    },
    {
        "session_id": "S005",
        "category": "mixed_candidate",
        "description": "能力参差不齐的候选人",
        "qa_pairs": [
            {
                "question": "解释 RESTful API",
                "answer": SINGLE_ANSWER_BENCHMARK[2]["answer"]
            },
            {
                "question": "查找数组重复元素",
                "answer": SINGLE_ANSWER_BENCHMARK[8]["answer"]
            },
            {
                "question": "描述沟通经历",
                "answer": SINGLE_ANSWER_BENCHMARK[10]["answer"]
            }
        ],
        "expected_overall_score": 58,
        "expected_dimension_range": {
            "professional_knowledge": [55, 70],
            "skill_match": [50, 70],
            "language_expression": [50, 70],
            "logical_thinking": [55, 75],
            "stress_response": [60, 80],
            "personality": [60, 80],
            "motivation": [55, 75],
            "value": [60, 80]
        }
    }
]

# ============ 评估阈值 ============

# 分数相关性（Pearson/Spearman）
SCORE_CORRELATION_THRESHOLD = 0.75

# 平均绝对误差
MAE_THRESHOLD = 0.15  # 单题 (0-1)
MAE_OVERALL_THRESHOLD = 10  # 整体 (0-100)

# 分类准确率（优秀/良好/及格/不及格）
CLASSIFICATION_ACCURACY_THRESHOLD = 0.80

# 重复测试一致性
REPEATABILITY_THRESHOLD = 0.90  # 变异系数 < 10%

# JSON 格式成功率
JSON_VALIDITY_THRESHOLD = 0.99

# 响应时间阈值（秒）
SINGLE_EVAL_TIME_THRESHOLD = 5
REPORT_GEN_TIME_THRESHOLD = 15


# ============ 辅助函数 ============

def get_test_case_by_id(case_id: str) -> dict:
    """根据 ID 获取单题测试用例"""
    for case in SINGLE_ANSWER_BENCHMARK:
        if case["id"] == case_id:
            return case
    return None


def get_interview_by_id(session_id: str) -> dict:
    """根据 ID 获取完整面试用例"""
    for interview in FULL_INTERVIEW_BENCHMARK:
        if interview["session_id"] == session_id:
            return interview
    return None


def get_test_cases_by_category(category: str) -> list:
    """根据分类获取测试用例"""
    return [case for case in SINGLE_ANSWER_BENCHMARK if category in case["category"]]


def score_to_grade(score: float) -> str:
    """将分数转换为等级"""
    if score >= 0.80:
        return "优秀"
    elif score >= 0.65:
        return "良好"
    elif score >= 0.45:
        return "及格"
    else:
        return "不及格"
