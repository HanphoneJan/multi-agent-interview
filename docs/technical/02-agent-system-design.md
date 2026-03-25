# Agent系统设计详解

> 深入剖析Multi-Agent架构设计，适合面试深入讨论

## 一、什么是Multi-Agent系统？

### 1.1 概念解释

**类比理解**：想象一个真实的面试场景

```
真实面试                          AI面试Agent系统
─────────────────────────────────────────────────────────
技术面试官  ──────提问──────>     InterviewerAgent
    │                                    │
    │                            ┌───────┴───────┐
    │                            ▼               ▼
评估记录员  ──────打分──────>   EvaluatorAgent  CoachAgent
    │                           (实时评估)      (学习建议)
    │                                │
HR面试官    ──────反馈──────>       └──────→ 综合报告
```

**核心思想**：
- 每个Agent有明确的**角色(Role)**、**目标(Goal)**、**背景(Backstory)**
- Agent之间通过**共享上下文**协作
- 由**流程控制器**协调执行顺序

### 1.2 为什么不用单Agent？

| 方案 | 问题 | Multi-Agent优势 |
|-----|------|----------------|
| 单Agent | 角色混杂，Prompt复杂 | 职责分离，专注单一任务 |
| 单Agent | 难以并行处理 | 评估和追问可以并行 |
| 单Agent | 难以扩展新功能 | 新增Agent即可扩展 |

---

## 二、Agent基类设计

### 2.1 核心抽象

文件：`app/agents/base.py`

```python
@dataclass
class AgentOutput:
    """Agent输出结果"""
    content: str | dict          # 主要内容
    metadata: dict               # 元数据(token/耗时等)
    success: bool                # 是否成功
    error: str | None            # 错误信息
    agent_id: str                # Agent实例ID
    timestamp: datetime          # 生成时间


class BaseAgent(ABC):
    """Agent基类 - 所有Agent的抽象"""

    def __init__(self, role, goal, backstory, llm_config):
        # 核心三要素
        self.role = role              # 角色："技术面试官"
        self.goal = goal              # 目标："评估候选人技术能力"
        self.backstory = backstory    # 背景："10年经验的Tech Lead..."
        self.llm_config = llm_config  # LLM配置

    @abstractmethod
    async def execute(self, task, context) -> AgentOutput:
        """执行任务 - 子类必须实现"""
        raise NotImplementedError
```

### 2.2 设计亮点

**1. 角色-目标-背景模式**

这是参考CrewAI的核心设计，好处：
- **角色**：定义Agent的身份（面试官/评估员/顾问）
- **目标**：明确Agent的职责边界
- **背景**：影响LLM的行为风格（经验丰富的面试官 vs 刚毕业的HR）

**2. 状态管理**

```python
class AgentStatus(Enum):
    IDLE = "idle"      # 空闲
    BUSY = "busy"      # 执行中
    ERROR = "error"    # 错误
```

Agent有明确的生命周期状态，便于流程控制。

**3. 钩子函数**

```python
async def _before_execute(self, task, context):
    """执行前钩子 - 可以记录日志、更新状态"""
    self.status = AgentStatus.BUSY

async def _after_execute(self, task, result, context):
    """执行后钩子 - 可以处理结果、清理资源"""
    self.status = AgentStatus.IDLE if result.success else AgentStatus.ERROR
```

---

## 三、三大核心Agent

### 3.1 InterviewerAgent（面试官）

文件：`app/agents/interviewer.py`

**职责**：
- 生成面试问题
- 基于回答进行追问
- 控制面试节奏
- 结束面试

**代码示例**：

```python
class InterviewerAgent(BaseAgent):
    DEFAULT_ROLE = "技术面试官"
    DEFAULT_GOAL = "通过专业的技术面试，全面评估候选人的技术能力"
    DEFAULT_BACKSTORY = """
    你是一位拥有10年以上经验的技术面试官...
    你擅长通过深入的对话了解候选人的技术深度和广度...
    """

    async def execute(self, task, context):
        """根据任务类型分发处理"""
        task_type = context.get("task_type", "generate_question")

        if task_type == "generate_question":
            return await self._generate_question(task, context)
        elif task_type == "follow_up":
            return await self._follow_up(task, context)
        elif task_type == "control_pace":
            return await self._control_pace(task, context)
        # ...
```

**追问逻辑**：

```python
async def _follow_up(self, task, context):
    """基于回答进行追问"""
    messages = self._build_messages(task, context)

    # 调用LLM生成追问
    response_chunks = []
    async for chunk in self.llm_service.chat(messages=messages, stream=False):
        if chunk.type == "text" and chunk.content:
            response_chunks.append(chunk.content)

    content = "".join(response_chunks)

    # 更新对话历史
    self._update_history("interviewer", content)

    return AgentOutput(
        content=content,
        metadata={"task_type": "follow_up"},
        success=True,
    )
```

### 3.2 EvaluatorAgent（评估员）

文件：`app/agents/evaluator.py`

**职责**：
- 实时评估候选人回答
- 多维度打分（8个维度）
- 生成综合评估报告

**评估维度**：

```python
EVALUATION_DIMENSIONS = [
    "professional_knowledge",   # 专业知识
    "skill_match",              # 技能匹配度
    "language_expression",      # 语言表达
    "logical_thinking",         # 逻辑思维
    "stress_response",          # 抗压能力
    "personality",              # 性格特质
    "motivation",               # 求职动机
    "value",                    # 价值观匹配
]
```

**评估流程**：

```python
async def _evaluate_answer(self, task, context):
    """评估候选人回答"""
    messages = self._build_messages(task, context)

    # 调用LLM评估
    response_chunks = []
    async for chunk in self.llm_service.chat(messages=messages, stream=False):
        response_chunks.append(chunk.content)

    content = "".join(response_chunks)

    # 从LLM响应中提取JSON格式的评估结果
    evaluation_data = self._extract_json_from_response(content)

    return AgentOutput(
        content=content,
        metadata={
            "task_type": "evaluate_answer",
            "scores": evaluation_data.get("scores", {}),
            "strengths": evaluation_data.get("strengths", []),
            "weaknesses": evaluation_data.get("weaknesses", []),
        },
        success=True,
    )
```

**JSON提取技巧**：

```python
def _extract_json_from_response(self, content: str) -> dict:
    """从LLM响应中提取JSON

    LLM的输出可能包含Markdown代码块，需要提取处理
    """
    # 尝试直接解析
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass

    # 尝试从Markdown代码块中提取
    json_pattern = r"```(?:json)?\s*([\s\S]*?)```"
    matches = re.findall(json_pattern, content)

    for match in matches:
        try:
            return json.loads(match.strip())
        except json.JSONDecodeError:
            continue

    # 兜底：返回空字典
    return {}
```

### 3.3 CoachAgent（学习顾问）

文件：`app/agents/coach.py`

**职责**：
- 分析能力薄弱点
- 生成个性化学习计划
- 推荐学习资源

**使用场景**：
- 面试结束后，根据评估结果给出学习建议
- 用户可以主动请求学习指导

---

## 四、流程编排引擎（Flow）

### 4.1 为什么需要流程编排？

面试不是简单的问答，而是有明确流程的：

```
自我介绍 → 技术问答 → 算法题 → 项目经历 → HR问答 → 结束
    │          │          │         │         │
    └──────────┴──────────┴─────────┴─────────┘
              ↑ 可能需要跳过某些环节
              ↑ 可能需要根据表现调整难度
```

### 4.2 设计思路

参考CrewAI的Flow设计，使用**装饰器模式**定义流程：

```python
class InterviewFlow(Flow):

    @start()
    async def self_introduction(self, context):
        """自我介绍阶段 - 流程起点"""
        return "请做个简单的自我介绍"

    @listen(self_introduction)
    async def technical_round(self, prev_result, context):
        """技术问答 - 顺序执行"""
        return "技术问题..."

    @router(technical_round)
    async def adaptive_next(self, prev_result, context):
        """自适应路由 - 根据表现决定下一环节"""
        if context.get_sync("level") == "expert":
            return "system_design"  # 进入系统设计环节
        return "basic_coding"      # 进入基础编程环节
```

### 4.3 装饰器实现

文件：`app/agents/flow.py`

```python
def start():
    """标记起始步骤"""
    def decorator(func):
        func._flow_meta = {
            "step_type": StepType.START,
            "step_id": func.__name__,
        }
        return func
    return decorator

def listen(step_func):
    """标记监听前序步骤"""
    def decorator(func):
        meta = getattr(func, "_flow_meta", {})
        meta.update({
            "step_type": StepType.LISTEN,
            "step_id": func.__name__,
            "listens_to": step_func,  # 依赖的前序步骤
        })
        func._flow_meta = meta
        return func
    return decorator
```

### 4.4 流程执行

```python
class Flow(ABC):
    def _build_flow(self):
        """构建流程图 - 扫描类中所有带装饰器的方法"""
        for attr_name in dir(self):
            attr = getattr(self, attr_name)
            if callable(attr) and hasattr(attr, "_flow_meta"):
                meta = attr._flow_meta
                step_id = meta.get("step_id", attr_name)
                step_type = meta.get("step_type", StepType.TASK)

                # 确定依赖关系
                depends_on = []
                if "listens_to" in meta:
                    listened_func = meta["listens_to"]
                    depends_on = [listened_func._flow_meta.get("step_id")]

                step = FlowStep(
                    step_id=step_id,
                    name=attr_name,
                    step_type=step_type,
                    func=attr,
                    depends_on=depends_on,
                )
                self._steps[step_id] = step

    async def execute(self, context):
        """执行流程"""
        if self._start_step:
            await self._execute_step(self._start_step, context)
```

---

## 五、Agent协作模式

### 5.1 协作流程

```
候选人回答
    │
    ▼
┌─────────────────────────────────────────┐
│          并行执行（asyncio.gather）       │
│  ┌─────────────────┐ ┌────────────────┐ │
│  │ InterviewerAgent │ │ EvaluatorAgent │ │
│  │   生成追问        │ │   评估回答      │ │
│  └─────────────────┘ └────────────────┘ │
└─────────────────────────────────────────┘
    │                           │
    ▼                           ▼
追问内容                      评估分数
    │                           │
    └───────────┬───────────────┘
                ▼
         发送给候选人
```

### 5.2 代码实现

文件：`app/websockets/interview_crew.py`

```python
async def process_answer(self, answer: str, answer_type: str = "text"):
    """处理候选人回答 - 并行执行多个Agent"""

    # 并行执行评估和追问生成
    results = await asyncio.gather(
        self._evaluate_answer(answer),      # 评估员Agent
        self._generate_follow_up(answer),   # 面试官Agent
        return_exceptions=True,
    )

    evaluation_result = results[0]
    follow_up_result = results[1]

    return {
        "success": True,
        "evaluation": evaluation_result,
        "follow_up": follow_up_result,
    }
```

### 5.3 共享上下文

Agent之间通过共享上下文协作：

```python
context = {
    "task_type": "evaluate_answer",
    "scenario": "frontend_junior",
    "question": "什么是闭包？",
    "answer": "闭包是...",
    "history": [          # 对话历史
        {"role": "interviewer", "content": "..."},
        {"role": "candidate", "content": "..."},
    ],
    "current_stage": "technical",
    "candidate_info": {
        "level": "junior",
        "years_of_experience": 2,
    },
}
```

---

## 六、Prompt工程

### 6.1 Prompt设计原则

**1. 结构化**

```python
INTERVIEWER_SYSTEM_PROMPT = """你是一位专业的{role}。

你的目标：{goal}

你的背景：{backstory}

请始终以专业、友好的态度完成任务。你的回答应当：
1. 准确且有条理
2. 符合你的角色定位
3. 有助于达成既定目标
"""
```

**2. 任务模板化**

```python
EVALUATOR_TASK_TEMPLATES = {
    "evaluate_answer": """
【面试场景】{scenario}
【候选人信息】{candidate_info}
【问题】{question}
【回答】{answer}
【对话历史】{history}

请评估以上回答，按以下JSON格式输出：
{{
  "scores": {{
    "professional_knowledge": {{"score": 0-5, "comment": "..."}},
    "logical_thinking": {{"score": 0-5, "comment": "..."}},
    ...
  }},
  "strengths": ["优点1", "优点2"],
  "weaknesses": ["不足1", "不足2"]
}}
""",
}
```

### 6.2 Prompt优化技巧

| 技巧 | 说明 | 示例 |
|-----|------|------|
| Few-shot | 提供示例 | "例如：好的回答应该..." |
| 角色设定 | 明确身份 | "你是一位资深面试官..." |
| 输出格式 | 指定格式 | "按JSON格式输出..." |
| 约束条件 | 限制范围 | "评分范围0-5分..." |

---

## 七、面试常见问题

### Q1: Agent之间是如何通信的？

> 通过共享上下文（Context）通信。所有Agent接收相同的Context对象，包含对话历史、当前状态等信息。执行结果通过返回值传递。

### Q2: 如何处理Agent执行失败？

> 每个Agent有状态管理（IDLE/BUSY/ERROR），执行失败会设置ERROR状态并记录错误信息。上层可以通过try-except捕获异常，进行重试或降级处理。

### Q3: 为什么用YAML配置Agent？

> YAML配置可以热更新Agent角色、目标等属性，无需修改代码。同时方便非技术人员调整Prompt。

### Q4: 流程编排支持哪些模式？

> 支持四种模式：
> 1. `@start()` - 流程起点
> 2. `@listen(step)` - 顺序执行
> 3. `@router(step)` - 条件分支
> 4. `@parallel([steps])` - 并行执行

---

*下一篇：[RAG与推荐系统设计](03-rag-and-recommendation.md)*
