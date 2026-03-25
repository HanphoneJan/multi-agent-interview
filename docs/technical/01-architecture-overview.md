# AI Interview Agent - 系统架构总览

> 本文档面向Agent开发岗位面试，系统介绍项目架构设计和技术亮点

## 一、项目简介

AI Interview Agent 是一个基于 **Multi-Agent架构** 的智能面试系统，模拟真实技术面试场景，提供：

- **AI面试官**：进行技术问答、追问、节奏控制
- **AI评估员**：实时评估回答质量，多维度打分
- **AI学习顾问**：分析薄弱点，推荐个性化学习资源

### 核心数据

| 指标 | 数值 |
|-----|------|
| 代码行数 | 15,000+ |
| Agent数量 | 3个核心Agent + 1个流程控制器 |
| 推荐算法 | 4种（RAG + 混合推荐） |
| 向量维度 | 384维 |
| 评估维度 | 8个维度 |

---

## 二、系统架构

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              前端层 (UniApp)                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐ │
│  │   面试页面   │  │   报告页面   │  │   学习页面   │  │    资源推荐页    │ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         API网关层 (FastAPI)                              │
│                    JWT认证 / 限流 / 请求路由                               │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
           ┌────────────────────────┼────────────────────────┐
           ▼                        ▼                        ▼
┌─────────────────────┐  ┌─────────────────────┐  ┌─────────────────────┐
│   RESTful API       │  │   WebSocket服务      │  │   定时任务服务       │
│   (面试管理/评估)    │  │   (实时面试通信)      │  │   (模型训练/清理)    │
└─────────────────────┘  └─────────────────────┘  └─────────────────────┘
           │                        │                        │
           └────────────────────────┼────────────────────────┘
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         Agent核心层                                      │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                      Multi-Agent System                          │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │   │
│  │  │ Interviewer  │  │  Evaluator   │  │    Coach     │          │   │
│  │  │   Agent      │  │    Agent     │  │    Agent     │          │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘          │   │
│  │         │                  │                  │                │   │
│  │         └──────────────────┼──────────────────┘                │   │
│  │                            ▼                                   │   │
│  │              ┌─────────────────────────┐                      │   │
│  │              │    Flow Controller      │                      │   │
│  │              │    (流程编排引擎)        │                      │   │
│  │              └─────────────────────────┘                      │   │
│  └─────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
           ┌────────────────────────┼────────────────────────┐
           ▼                        ▼                        ▼
┌─────────────────────┐  ┌─────────────────────┐  ┌─────────────────────┐
│   推荐系统           │  │   LLM服务           │  │   数据存储          │
│   ├─ RAG推荐        │  │   ├─ 通义千问        │  │   ├─ PostgreSQL    │
│   ├─ 混合推荐        │  │   ├─ 多模态处理      │  │   ├─ Milvus向量库   │
│   ├─ 规则推荐        │  │   └─ 流式响应        │  │   └─ Redis缓存     │
│   └─ 协同过滤        │  │                      │  │                     │
└─────────────────────┘  └─────────────────────┘  └─────────────────────┘
```

---

## 三、技术栈

### 3.1 后端技术

| 层级 | 技术选型 | 用途 |
|-----|---------|------|
| 框架 | FastAPI + Django | 异步API + 管理后台 |
| Agent框架 | 自研(参考CrewAI) | 多Agent协作 |
| LLM | 通义千问 (qwen-plus) | 对话/评估/推荐 |
| 向量数据库 | Milvus | 语义检索 |
| 关系数据库 | PostgreSQL | 业务数据 |
| 缓存 | Redis | 会话/缓存 |
| 消息队列 | Celery | 异步任务 |

### 3.2 算法/模型

| 模块 | 技术 | 说明 |
|-----|------|------|
| Embedding | sentence-transformers (paraphrase-multilingual-MiniLM-L12-v2) | 384维向量 |
| 相似度计算 | 余弦相似度 | 向量检索 |
| 推荐算法 | 混合推荐(规则+内容+协同+RAG) | 多路召回 |
| 评估维度 | 8维度评分 | 专业知识/技能匹配/表达/逻辑/抗压/性格/动机/价值观 |

---

## 四、核心亮点

### 4.1 亮点一：自研Agent框架（参考CrewAI设计）

**为什么选择自研而非直接用CrewAI/LangChain？**

1. **更轻量**：只实现核心能力，减少依赖
2. **更灵活**：针对面试场景定制流程控制
3. **学习价值**：深入理解Agent设计原理

**核心抽象**：

```python
# BaseAgent - 所有Agent的基类
class BaseAgent(ABC):
    def __init__(self, role, goal, backstory, llm_config):
        self.role = role          # 角色名称
        self.goal = goal          # 目标
        self.backstory = backstory  # 背景故事

    @abstractmethod
    async def execute(self, task, context) -> AgentOutput:
        """执行任务"""
        pass
```

### 4.2 亮点二：流程编排引擎

支持复杂的面试流程控制：

```python
class InterviewFlow(Flow):
    @start()
    async def self_introduction(self, context):
        """自我介绍阶段"""
        return "请做个自我介绍"

    @listen(self_introduction)
    async def technical_round(self, prev_result, context):
        """技术问答阶段"""
        return "技术问题..."

    @router(technical_round)
    async def adaptive_next(self, prev_result, context):
        """自适应路由"""
        if context.get_sync("level") == "expert":
            return "system_design"
        return "basic_coding"
```

**支持的模式**：
- `@start()` - 流程起点
- `@listen(step)` - 顺序执行
- `@router(step)` - 条件分支
- `@parallel([steps])` - 并行执行

### 4.3 亮点三：多路召回推荐系统

```
用户请求
    │
    ├──→ 规则推荐 (50%权重) ──┐
    │                         │
    ├──→ 内容推荐 (30%权重) ──┼──→ 融合排序 ──→ 多样性重排 ──→ 结果
    │                         │
    └──→ 协同过滤 (20%权重) ──┘
```

**四种推荐方式**：

| 方式 | 原理 | 适用场景 |
|-----|------|---------|
| RAG推荐 | 向量检索 + LLM生成推荐理由 | 面试后个性化推荐 |
| 规则推荐 | 基于评估薄弱点匹配标签 | 冷启动 |
| 内容推荐 | 基于Embedding相似度 | 有历史行为 |
| 协同过滤 | 基于用户行为相似度 | 用户量足够 |

### 4.4 亮点四：实时多Agent协作

WebSocket连接中，多个Agent并行工作：

```python
# 候选人回答后，并行执行评估和追问生成
results = await asyncio.gather(
    self._evaluate_answer(answer),      # 评估员Agent
    self._generate_follow_up(answer),   # 面试官Agent
    return_exceptions=True,
)
```

---

## 五、项目结构

```
fastapi/
├── app/
│   ├── agents/              # Agent核心层
│   │   ├── base.py          # Agent基类
│   │   ├── interviewer.py   # 面试官Agent
│   │   ├── evaluator.py     # 评估员Agent
│   │   ├── coach.py         # 学习顾问Agent
│   │   ├── flow.py          # 流程编排引擎
│   │   ├── interview_flow.py # 面试流程定义
│   │   ├── task.py          # 任务定义
│   │   ├── prompts/         # Prompt模板
│   │   └── config/          # Agent配置(YAML)
│   │
│   ├── recommenders/        # 推荐系统
│   │   ├── base.py          # 推荐器基类
│   │   ├── rag_recommender.py      # RAG推荐
│   │   ├── hybrid.py               # 混合推荐
│   │   ├── content_based.py        # 内容推荐
│   │   ├── collaborative_filtering.py # 协同过滤
│   │   ├── rule_based.py           # 规则推荐
│   │   └── embedding_service.py    # 向量化服务
│   │
│   ├── websockets/          # WebSocket服务
│   │   ├── interview_crew.py       # Crew模式面试
│   │   ├── interview_realtime.py   # 实时面试
│   │   ├── manager.py              # 连接管理
│   │   └── protocol.py             # 消息协议
│   │
│   ├── core/                # 基础设施
│   │   ├── milvus_client.py        # 向量数据库
│   │   ├── embedding.py            # Embedding服务
│   │   ├── prompts.py              # Prompt模板
│   │   └── constants.py            # 常量配置
│   │
│   └── services/            # 业务服务
│       ├── interview_crew_service.py
│       ├── recommendation_service.py
│       └── qwen3_omni_http_service.py
│
├── tests/                   # 测试
│   ├── unit/                # 单元测试
│   ├── test_recommenders/   # 推荐器测试
│   └── benchmark/           # 性能测试
│
└── docs/
    └── technical/           # 技术文档
```

---

## 六、面试话术建议

### 6.1 项目介绍（1分钟版本）

> "我开发了一个AI面试Agent系统，核心是一个Multi-Agent架构，包含面试官、评估员、学习顾问三个Agent。系统采用自研的Agent框架（参考CrewAI），支持流程编排，可以处理复杂的面试流程。在推荐模块，我实现了RAG+混合推荐，结合向量检索和LLM生成个性化推荐理由。技术栈主要是FastAPI + 通义千问 + Milvus向量库。"

### 6.2 技术亮点（深入版）

**Q: 为什么要自研Agent框架，而不是直接用CrewAI？**

> "主要是为了学习和轻量化。自研框架让我深入理解了Agent的核心原理：角色定义、任务分配、上下文管理。而且我们的场景相对垂直，自研框架更轻量，代码量只有CrewAI的1/10，但核心能力都具备。"

**Q: 流程编排引擎是怎么设计的？**

> "我参考了CrewAI的Flow设计，使用装饰器模式定义流程。支持`@start`标记起点，`@listen`顺序执行，`@router`条件分支，`@parallel`并行执行。底层是一个DAG执行器，自动处理依赖关系。"

**Q: 推荐系统有哪些创新点？**

> "我们采用多路召回+融合排序的架构。针对面试场景，设计了两种推荐：
> 1. RAG推荐：面试后基于评估结果做向量检索，LLM生成推荐理由
> 2. 混合推荐：日常学习资源推荐，融合规则、内容、协同三种策略"

---

## 七、学习路径建议

如果你是小白，建议按以下顺序学习：

1. **第一阶段**：理解Multi-Agent概念 → 阅读 `agents/base.py`
2. **第二阶段**：理解流程编排 → 阅读 `agents/flow.py`
3. **第三阶段**：理解RAG推荐 → 阅读 `recommenders/rag_recommender.py`
4. **第四阶段**：理解向量检索 → 阅读 `core/milvus_client.py`
5. **第五阶段**：理解WebSocket实时通信 → 阅读 `websockets/interview_crew.py`

---

*下一篇：[Agent系统设计详解](02-agent-system-design.md)*
