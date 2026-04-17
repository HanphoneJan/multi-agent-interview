# 面试流程与模式详解

> 深入解析面试流程控制、实时/非实时模式对比、面试生命周期管理

---

## 一、面试流程是固定的吗？

### 1.1 流程配置化设计

**答案：不是固定的，支持配置化定制。**

面试流程通过 `InterviewFlow` 类配置，支持多种预设场景和自定义流程：

```python
# 预定义的面试流程配置（interview_flow.py:139-193）
FLOW_CONFIGS: dict[InterviewType, list[InterviewStage]] = {
    InterviewType.FRONTEND_JUNIOR: [
        InterviewStage.SELF_INTRO,
        InterviewStage.TECHNICAL,
        InterviewStage.CODING,
        InterviewStage.Q_AND_A,
        InterviewStage.WRAP_UP,
    ],
    InterviewType.BACKEND_SENIOR: [
        InterviewStage.SELF_INTRO,
        InterviewStage.TECHNICAL,
        InterviewStage.SYSTEM_DESIGN,  # 高级才有系统设计
        InterviewStage.CODING,
        InterviewStage.BEHAVIORAL,
        InterviewStage.Q_AND_A,
        InterviewStage.WRAP_UP,
    ],
    # ... 更多配置
}
```

### 1.2 如何判断当前面试阶段

**三种判断方式：**

| 方式 | 数据来源 | 使用场景 |
|-----|---------|---------|
| Flow 控制器状态 | `InterviewContext.current_stage` | 流程编排内部使用 |
| WebSocket 消息类型 | `STAGE_CHANGE` 消息 | 前端展示当前阶段 |
| 数据库状态 | `interview_sessions.status` | 持久化状态查询 |

**代码示例：**

```python
# 方式1：从 Flow 上下文获取（interview_flow.py:65）
@dataclass
class InterviewContext:
    current_stage: InterviewStage = InterviewStage.SELF_INTRO
    stages_completed: list[InterviewStage] = field(default_factory=list)
    stages_remaining: list[InterviewStage] = field(default_factory=list)

# 方式2：前端通过消息接收阶段变更（interview_crew.py:631-635）
await websocket.send_json({
    "type": CrewMessageType.STAGE_CHANGE,
    "stage": "technical",
    "progress": 35,
})

# 方式3：自适应路由决定下一阶段（interview_flow.py:339-356）
@router(system_design_or_coding)
async def adaptive_next(self, prev_result, context):
    if prev_result.get("stage") == "system_design":
        return "coding_round"
    elif prev_result.get("stage") == "coding":
        return "behavioral_round"
    return "q_and_a"
```

### 1.3 阶段推进机制

```
候选人回答
    │
    ▼
┌─────────────────────────────────────┐
│  1. Agent 评估回答质量               │
│     - EvaluatorAgent 打分            │
│     - 判断是否需要追问               │
└─────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────┐
│  2. 检查阶段完成条件                 │
│     - 问题数是否达标？               │
│     - 时间是否超时？                 │
│     - 候选人表现是否足够？           │
└─────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────┐
│  3. 决定下一步                       │
│     - 同阶段继续追问                 │
│     - 进入下一阶段                   │
│     - 结束面试                       │
└─────────────────────────────────────┘
```

---

## 二、实时面试 vs 非实时面试

### 2.1 两个模式的对比

| 维度 | 实时面试 (Realtime) | 非实时面试 (Non-realtime) |
|-----|--------------------|-------------------------|
| **端点** | `/ws/interview/realtime/{session_id}` | `/ws/interview/{session_id}` |
| **模型** | Qwen3-Omni (端到端) | Qwen3-Omni HTTP API |
| **延迟** | <500ms (流式) | 1-3秒 (整句生成) |
| **音频处理** | 前端直接传输 PCM | 前端 ASR 后传文本 |
| **追问机制** | 模型自动判断 | Agent 显式生成 |
| **适用场景** | 高沉浸感、自然对话 | 弱网环境、低延迟要求 |

### 2.2 为什么要两个模式？

**技术原因：**

1. **网络环境差异**
   - 实时模式需要稳定的高带宽连接（音频+视频流）
   - 非实时模式对网络要求较低，文本传输更稳定

2. **设备性能差异**
   - 实时模式依赖客户端音频采集/播放能力
   - 非实时模式前端做 ASR，减轻服务端压力

3. **成本考虑**
   - 实时模式调用 Qwen3-Omni Realtime API，成本较高
   - 非实时模式使用 HTTP API，可按需调用

**业务原因：**

```
用户场景分析：
├── 正式面试准备 → 需要实时模式（体验真实）
├── 通勤路上练习 → 非实时模式（省流量）
├── 网络不稳定时 → 非实时模式（更可靠）
└── 快速测试功能 → 非实时模式（响应快）
```

### 2.3 设计差异详解

#### 2.3.1 WebSocket 消息协议差异

**实时模式（interview_realtime.py:48-70）：**
```python
# 客户端 -> 服务端
{
    "type": "audio",           # 实时音频流
    "data": "base64_pcm",      # 16kHz PCM 数据
    "timestamp": 123456
}

# 服务端 -> 客户端
{
    "type": "audio",           # AI 语音输出
    "data": "base64_pcm",      # 24kHz PCM 数据
    "format": "pcm"
}
```

**非实时模式（interview.py, interview_crew.py）：**
```python
# 客户端 -> 服务端
{
    "type": "text",
    "text": "用户输入的文本"     # 前端 ASR 结果
}

# 服务端 -> 客户端
{
    "type": "stream_chunk",    # 文本流式输出
    "content": "AI 回答片段"
}
```

#### 2.3.2 服务端架构差异

**实时模式架构：**
```
前端 (UniApp)
    │ WebSocket
    ▼
Qwen3-Omni Realtime Client
    │ 直接转发
    ▼
通义千问 Realtime API
    - 端到端音频理解
    - 自动语音合成
    - 自然打断支持
```

**非实时模式架构：**
```
前端 (UniApp)
    │ WebSocket
    ▼
InterviewCrew Session
    ├── InterviewerAgent (生成问题)
    ├── EvaluatorAgent (评估回答)
    └── CoachAgent (学习建议)
    │
    ▼
Qwen3-Omni HTTP API
    - 文本输入输出
    - 支持语音合成
```

#### 2.3.3 数据库存储差异

```python
# interview_scenarios 表区分场景类型
class InterviewScenario:
    is_realtime: bool  # True = 实时面试, False = 非实时

# 连接时校验（interview_realtime.py:122-128）
if not session_dict.get("scenario_is_realtime"):
    await websocket.close(
        reason="Non-realtime interviews must use /ws/interview endpoint"
    )
```

---

## 三、启动面试和结束面试的过程

### 3.1 启动面试流程

#### 3.1.1 整体流程图

```
用户点击"开始面试"
    │
    ▼
┌─────────────────────────────────────────────┐
│ 1. 创建面试会话 (FastAPI API)                │
│    POST /api/interviews/sessions/            │
│    返回: session_id, scenario_config         │
└─────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────┐
│ 2. 建立 WebSocket 连接                       │
│    实时模式: /ws/interview/realtime/{id}     │
│    非实时模式: /ws/interview/{id}            │
└─────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────┐
│ 3. 发送 start 消息                           │
│    携带: scenario, voice, style 等配置       │
└─────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────┐
│ 4. 服务端初始化                               │
│    ├─ 验证 token 和 session                  │
│    ├─ 初始化 Agent / Omni Client             │
│    ├─ 加载场景配置                           │
│    └─ 更新数据库状态为 in_progress           │
└─────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────┐
│ 5. 生成第一个问题                             │
│    实时: Omni 自动生成开场白                  │
│    非实时: InterviewerAgent 生成问题          │
└─────────────────────────────────────────────┘
```

#### 3.1.2 代码详解：非实时模式启动

```python
# interview.py:226-356
async def handle_start_interview(session_id, user_id, db):
    """处理面试开始"""

    # 1. 获取用户面试官设置（语音、风格等）
    interviewer_settings = await get_user_interviewer_settings(db, user_id)
    voice = get_voice_for_settings(interviewer_settings)

    # 2. 更新数据库状态
    await db.execute(
        update(interview_sessions)
        .where(interview_sessions.c.id == int(session_id))
        .values(
            status="in_progress",
            start_time=datetime.now(timezone.utc)
        )
    )
    await db.commit()

    # 3. 生成第一个问题（使用 Qwen3-Omni）
    system_prompt = qwen3_service.build_interview_system_prompt(...)
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": "请生成开场问题..."}
    ]

    # 4. 流式返回结果
    async for chunk in qwen3_service.chat(messages, voice=voice, stream=True):
        if chunk.type == "text":
            await manager.send_stream_chunk(session_id, user_id, chunk.content)
        elif chunk.type == "audio":
            await manager.send_message({"type": "audio_delta", "audio": chunk.audio_data})
```

#### 3.1.3 代码详解：实时模式启动

```python
# interview_realtime.py:343-388
elif msg_type == "start":
    # 初始化 Qwen3-Omni 客户端
    config = RealtimeConfig(
        voice=message.get("voice", "Chelsie"),
        enable_audio=True,
    )
    omni_client = await get_or_create_client(session_id, system_prompt, config)

    # 启动事件转发任务
    forward_task = asyncio.create_task(forward_omni_events())
    heartbeat_task = asyncio.create_task(send_heartbeat())

    interview_started = True

    # 更新数据库
    await db.execute(
        update(interview_sessions)
        .where(interview_sessions.c.id == int(session_id))
        .values(
            status="in_progress",
            start_time=datetime.now(timezone.utc)
        )
    )
    await db.commit()

    # 触发 AI 开始面试
    await omni_client.create_response()
```

### 3.2 结束面试流程

#### 3.2.1 整体流程图

```
用户点击"结束面试" / 超时自动结束
    │
    ▼
┌─────────────────────────────────────────────┐
│ 1. 接收 end 消息                             │
└─────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────┐
│ 2. 更新数据库状态                             │
│    - status = "completed"                    │
│    - is_finished = True                      │
│    - end_time = now()                        │
└─────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────┐
│ 3. 计算面试统计                               │
│    - 总时长 (end - start)                    │
│    - 问题数量                                │
│    - 对话轮数                                │
└─────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────┐
│ 4. 发送结束消息给前端                         │
│    - 总结信息                                │
│    - 报告生成状态                            │
└─────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────┐
│ 5. 触发异步任务（Crew 模式）                  │
│    - 生成评估报告                            │
│    - 生成学习建议                            │
│    - RAG 推荐学习资源                        │
└─────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────┐
│ 6. 清理资源                                   │
│    - 关闭 WebSocket                          │
│    - 释放 Agent 实例                         │
│    - 清理临时文件                            │
└─────────────────────────────────────────────┘
```

#### 3.2.2 代码详解：结束面试

```python
# interview_crew.py:697-704 / interview_realtime.py:491-558
async def handle_end_interview(session_id, user_id, db, ...):
    """处理面试结束"""

    # 1. 更新数据库
    await db.execute(
        update(interview_sessions)
        .where(interview_sessions.c.id == int(session_id))
        .values(
            status="completed",
            is_finished=True,
            end_time=datetime.now(timezone.utc)
        )
    )
    await db.commit()

    # 2. 计算面试时长
    result = await db.execute(
        select(interview_sessions.c.start_time, interview_sessions.c.end_time)
        .where(interview_sessions.c.id == int(session_id))
    )
    row = result.first()
    duration_seconds = int((row.end_time - row.start_time).total_seconds())

    # 3. 统计问题数量
    questions_count = len([
        m for m in conversation_history
        if m.get("role") == "assistant"
    ])

    # 4. 发送结束消息
    await manager.send_message({
        "type": "end",
        "summary": {
            "overall_evaluation": "面试已完成",
            "duration": duration_seconds,
            "duration_formatted": f"{duration_seconds // 60}分{duration_seconds % 60}秒",
            "questions_count": questions_count,
            "message": "评估报告正在生成中，请稍后查看"
        }
    }, session_id, user_id)

    # 5. 触发异步任务生成报告
    try:
        from app.workers.tasks import generate_report_task
        generate_report_task.delay(session_id, user_id)
    except Exception as e:
        logger.error(f"触发报告生成任务失败: {e}")
```

#### 3.2.3 状态机图

```
                    ┌─────────────┐
                    │   created   │
                    └──────┬──────┘
                           │ 用户点击开始
                           ▼
                    ┌─────────────┐
      ┌────────────│  in_progress │◄──────────┐
      │            └──────┬──────┘           │
      │                   │                  │
   用户暂停               │              用户恢复
      │                   │                  │
      ▼                   │                  ▼
┌─────────────┐           │         ┌─────────────┐
│   paused    │───────────┘         │  completed  │
└─────────────┘    用户结束面试     └─────────────┘
                                           │
                                           ▼
                                    ┌─────────────┐
                                    │ report_ready│
                                    └─────────────┘
```

---

## 四、面试话术建议

### 4.1 问题1：面试流程是固定的吗？

**建议回答：**

> 不是固定的。我们的面试流程采用配置化设计，通过 `InterviewFlow` 类支持多种预设场景，比如前端初级、后端高级、算法面试等，每种场景的流程环节不同。高级岗位会有系统设计环节，初级岗位则侧重基础编程。流程推进是通过装饰器模式编排的，支持条件分支和自适应调整。

### 4.2 问题2：实时和非实时面试有什么区别？

**建议回答：**

> 我们设计了两种模式来适应不同场景。实时面试使用 Qwen3-Omni 端到端模型，支持流式音频输入输出，延迟在 500ms 以内，体验更自然，适合正式面试准备；非实时面试使用 HTTP API，前端做 ASR 后传文本，响应时间 1-3 秒，但对网络要求低，适合弱网环境。两种模式在数据库层面通过 `is_realtime` 字段区分，连接时会校验端点匹配。

### 4.3 问题3：启动和结束面试的过程？

**建议回答：**

> 启动流程分为四步：首先前端调用 FastAPI API 创建会话获取 session_id，然后建立 WebSocket 连接，接着发送 start 消息携带场景配置，服务端初始化 Agent、更新数据库状态为 in_progress，最后生成第一个问题返回给前端。
>
> 结束流程也分四步：接收 end 消息后，更新数据库状态为 completed 并记录 end_time，计算面试时长和问题数量，发送总结消息给前端，最后触发异步任务生成评估报告和推荐资源，同时清理 WebSocket 连接和临时资源。

---

*文档版本: v1.0 | 最后更新: 2026-04-09*
