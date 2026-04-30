# Multi-Agent-Interview

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org) [![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green.svg)](https://fastapi.tiangolo.com) [![Vue](https://img.shields.io/badge/Vue-3.0+-brightgreen.svg)](https://vuejs.org) [![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> 基于 Multi-Agent 架构的智能面试系统，模拟真实技术面试场景，提供个性化学习推荐

## 功能特性

### 智能面试

- **AI 面试官** - 基于候选人水平动态调整难度，支持技术问答、算法题、项目经历等多种题型
- **实时评估** - 8 维度评估体系（专业知识、逻辑思维、编码能力、沟通表达等）
- **智能追问** - 根据回答质量自动追问，模拟真实面试互动

### 个性化学习

- **RAG 推荐** - 结合向量检索和 LLM 生成个性化学习建议
- **薄弱点分析** - 基于面试表现识别知识盲点
- **学习路径规划** - 智能推荐学习资源和顺序

### 多端支持

- **微信小程序** - 原生体验，随时随地练习
- **H5 网页** - 无需安装，即开即用
- **WebSocket 实时通信** - 低延迟对话体验

---

## 系统架构

```
+-------------------------------------------------------------+
|                        前端层 (UniApp)                       |
|         微信小程序 / H5 / App 三端统一开发                     |
+-------------------------------------------------------------+
                              |
                              v
+-------------------------------------------------------------+
|                      API 网关层 (FastAPI)                    |
|              RESTful API / WebSocket 实时通信                 |
+-------------------------------------------------------------+
                              |
                              v
+-------------------------------------------------------------+
|                     Multi-Agent 核心层                       |
|                                                              |
|   +--------------+  +--------------+  +--------------+     |
|   | Interviewer  |  |  Evaluator   |  |    Coach     |     |
|   |   Agent      |  |    Agent     |  |    Agent     |     |
|   |   (面试官)    |  |   (评估员)    |  |   (学习顾问)  |     |
|   +--------------+  +--------------+  +--------------+     |
|          |                  |                  |           |
|          +------------------+------------------+           |
|                             v                              |
|              +-------------------------+                   |
|              |    Flow Controller      |                   |
|              |    (流程编排引擎)        |                   |
|              +-------------------------+                   |
+-------------------------------------------------------------+
                              |
           +------------------+------------------+
           v                  v                  v
+---------------+   +---------------+   +---------------+
|   推荐系统     |   |   LLM 服务    |   |   数据存储    |
|  +- RAG       |   |  +- OpenAI    |   |  +- PostgreSQL|
|  +- 混合推荐   |   |    兼容 API   |   |  +- Milvus    |
|  +- 规则推荐   |   |  +- DashScope |   |  +- Redis     |
|  +- 协同过滤   |   |    多模态     |   |               |
|               |   |  +- 讯飞 TTS   |   |               |
+---------------+   +---------------+   +---------------+
```

### 技术栈

| 层级       | 技术                   | 说明                    |
| ---------- | ---------------------- | ----------------------- |
| 前端       | UniApp + Vue 3 + Pinia | 跨平台应用框架          |
| 后端       | FastAPI                | 高性能异步 API          |
| Agent 框架 | 自研（参考 CrewAI）    | 轻量级 Multi-Agent 框架 |
| LLM        | OpenAI 兼容 API        | 统一接口，支持多家模型  |
| 向量数据库 | Milvus                 | 语义检索                |
| 关系数据库 | PostgreSQL             | 业务数据存储            |
| 缓存       | Redis                  | 会话/缓存               |
| 消息队列   | Celery                 | 异步任务处理            |

---

## 快速开始

### 环境要求

- Python 3.11+
- PostgreSQL 14+
- Redis 6+
- Node.js 18+ (前端开发)

### 1. 克隆项目

```bash
git clone https://github.com/yourusername/ai-interview-agent.git
cd ai-interview-agent
```

### 2. 后端配置

```bash
cd fastapi

# 使用 uv 安装依赖（推荐）
uv sync

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，配置数据库和 API 密钥

# 运行数据库迁移
uv run alembic upgrade head

# 启动服务（推荐）
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. 配置 LLM

编辑 `.env` 文件，配置 LLM API：

```bash
# ---- 统一 LLM 配置（推荐） ----
# 支持任何 OpenAI 兼容的 API：DeepSeek、智谱、月之暗面、OpenAI 等
LLM_API_KEY=your-api-key
LLM_BASE_URL=https://api.deepseek.com/v1
LLM_MODEL=deepseek-chat

# ---- DashScope 多模态专属配置 ----
# Qwen3-Omni 实时音视频、Qwen-VL 视觉分析等专用
DASHSCOPE_API_KEY=your-dashscope-key
DASHSCOPE_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
```

### 4. 验证配置

```bash
# 快速测试各云服务 key 是否有效
uv run python scripts/verify_env.py
```

### 5. 前端配置

```bash
cd uniapp

# 安装依赖
pnpm install

# H5 开发
pnpm dev:h5

# 微信小程序开发
pnpm dev:mp-weixin
```

### 6. Docker 一键部署

```bash
docker-compose up --build
```

---

## 环境变量配置

### 必需配置

| 变量 | 说明 | 示例 |
|------|------|------|
| `DATABASE_URL` | PostgreSQL 连接字符串 | `postgresql+asyncpg://...` |
| `REDIS_URL` | Redis 连接地址 | `redis://localhost:6379/0` |
| `LLM_API_KEY` | 统一 LLM API Key | `sk-...` |
| `LLM_BASE_URL` | LLM API 基础地址 | `https://api.openai.com/v1` |
| `JWT_SECRET_KEY` | JWT 签名密钥 | 随机字符串 |

### 可选配置

| 变量 | 说明 | 是否必需 |
|------|------|----------|
| `DASHSCOPE_API_KEY` | Qwen3-Omni / Qwen-VL 多模态 | 仅多模态功能 |
| `ALIYUN_ACCESS_KEY` | OSS 对象存储 | 否（当前未使用） |
| `ALIYUN_ASR_APPKEY` | 语音识别 | 否（ASR 已迁移到前端） |
| `XFYUN_APP_ID` | 讯飞 TTS | 否（可用 mock 模式） |
| `SMTP_*` | 邮件服务 | 否（验证码功能） |
| `WECHAT_APP_ID` | 微信小程序登录 | 仅微信小程序 |

完整配置说明见 [`.env.example`](fastapi/.env.example)。

---

## 核心亮点

### 1. 自研 Agent 框架

参考 CrewAI 设计理念，但更加轻量灵活：

- **角色-目标-背景** 模式定义 Agent
- **流程编排引擎** 支持顺序/分支/并行执行
- **共享上下文** 实现多 Agent 协作

```python
# 示例：定义一个面试官 Agent
@start()
async def introduce(self, context: Context):
    return "请简单介绍一下你自己"

@listen(introduce)
async def evaluate_answer(self, answer: str, context: Context):
    # 并行执行评估和追问
    results = await asyncio.gather(
        self.evaluator.evaluate(answer),
        self.interviewer.follow_up(answer)
    )
    return results
```

### 2. 统一 LLM 客户端

所有文本 LLM 调用使用统一的 OpenAI 兼容接口，通过环境变量灵活切换模型：

```python
from app.core.llm_client import get_llm_client

client = get_llm_client()
response = await client.chat(messages=[
    {"role": "user", "content": "请评价这段代码"}
])
```

支持流式输出、JSON 结构化解析，fallback 链自动处理 key 优先级。

### 3. RAG + 混合推荐

多路召回架构，融合 4 种推荐策略：

| 策略     | 权重 | 用途                           |
| -------- | ---- | ------------------------------ |
| 规则推荐 | 50%  | 基于薄弱点匹配标签，解决冷启动 |
| 内容推荐 | 30%  | 基于 Embedding 相似度          |
| 协同过滤 | 20%  | 基于用户行为相似度             |
| RAG      | 动态 | 面试后生成个性化推荐理由       |

---

## 文档

| 文档                                                          | 内容                 | 阅读时间 |
| ------------------------------------------------------------- | -------------------- | -------- |
| [架构总览](docs/technical/01-architecture-overview.md)           | 系统整体架构、技术栈 | 15 分钟  |
| [Agent 系统设计](docs/technical/02-agent-system-design.md)       | Multi-Agent 架构详解 | 20 分钟  |
| [RAG 与推荐系统](docs/technical/03-rag-and-recommendation.md)    | 推荐算法实现         | 20 分钟  |
| [核心概念指南](docs/technical/04-core-concepts-for-beginners.md) | Agent/RAG 概念解释   | 15 分钟  |
| [面试准备指南](docs/technical/05-interview-preparation.md)       | 面试话术、常见问题   | 25 分钟  |

更多文档请查看 [docs/](docs/) 目录。
