# 🤖 AI Interview Agent

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org) [![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green.svg)](https://fastapi.tiangolo.com) [![Vue](https://img.shields.io/badge/Vue-3.0+-brightgreen.svg)](https://vuejs.org) [![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> 基于 Multi-Agent 架构的智能面试系统，模拟真实技术面试场景，提供个性化学习推荐

## ✨ 功能特性

### 🎯 智能面试

- **AI 面试官** - 基于候选人水平动态调整难度，支持技术问答、算法题、项目经历等多种题型
- **实时评估** - 8 维度评估体系（专业知识、逻辑思维、编码能力、沟通表达等）
- **智能追问** - 根据回答质量自动追问，模拟真实面试互动

### 📚 个性化学习

- **RAG 推荐** - 结合向量检索和 LLM 生成个性化学习建议
- **薄弱点分析** - 基于面试表现识别知识盲点
- **学习路径规划** - 智能推荐学习资源和顺序

### 💻 多端支持

- **微信小程序** - 原生体验，随时随地练习
- **H5 网页** - 无需安装，即开即用
- **WebSocket 实时通信** - 低延迟对话体验

---

## 🏗️ 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                        前端层 (UniApp)                       │
│         微信小程序 / H5 / App 三端统一开发                     │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      API 网关层 (FastAPI)                    │
│              RESTful API / WebSocket 实时通信                 │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     Multi-Agent 核心层                       │
│                                                              │
│   ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│   │ Interviewer  │  │  Evaluator   │  │    Coach     │     │
│   │   Agent      │  │    Agent     │  │    Agent     │     │
│   │   (面试官)    │  │   (评估员)    │  │   (学习顾问)  │     │
│   └──────────────┘  └──────────────┘  └──────────────┘     │
│          │                  │                  │           │
│          └──────────────────┼──────────────────┘           │
│                             ▼                              │
│              ┌─────────────────────────┐                   │
│              │    Flow Controller      │                   │
│              │    (流程编排引擎)        │                   │
│              └─────────────────────────┘                   │
└─────────────────────────────────────────────────────────────┘
                              │
           ┌──────────────────┼──────────────────┐
           ▼                  ▼                  ▼
┌───────────────┐   ┌───────────────┐   ┌───────────────┐
│   推荐系统     │   │   LLM 服务    │   │   数据存储    │
│  ├─ RAG       │   │  ├─ 通义千问   │   │  ├─ PostgreSQL│
│  ├─ 混合推荐   │   │  ├─ 流式输出   │   │  ├─ Milvus    │
│  ├─ 规则推荐   │   │  └─ 多模态    │   │  └─ Redis     │
│  └─ 协同过滤   │   │               │   │               │
└───────────────┘   └───────────────┘   └───────────────┘
```

### 技术栈

| 层级       | 技术                   | 说明                    |
| ---------- | ---------------------- | ----------------------- |
| 前端       | UniApp + Vue 3 + Pinia | 跨平台应用框架          |
| 后端       | FastAPI                | 高性能异步 API          |
| Agent 框架 | 自研（参考 CrewAI）    | 轻量级 Multi-Agent 框架 |
| LLM        | 通义千问 (qwen-plus)   | 对话/评估/推荐          |
| 向量数据库 | Milvus                 | 语义检索                |
| 关系数据库 | PostgreSQL             | 业务数据存储            |
| 缓存       | Redis                  | 会话/缓存               |
| 消息队列   | Celery                 | 异步任务处理            |

---

## 🚀 快速开始

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

# 启动服务
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. 前端配置

```bash
cd uniapp

# 安装依赖
pnpm install

# H5 开发
pnpm dev:h5

# 微信小程序开发
pnpm dev:mp-weixin
```

### 4. Docker 一键部署

```bash
docker-compose up --build
```

---

## 💡 核心亮点

### 1️⃣ 自研 Agent 框架

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

### 2️⃣ RAG + 混合推荐

多路召回架构，融合 4 种推荐策略：

| 策略     | 权重 | 用途                           |
| -------- | ---- | ------------------------------ |
| 规则推荐 | 50%  | 基于薄弱点匹配标签，解决冷启动 |
| 内容推荐 | 30%  | 基于 Embedding 相似度          |
| 协同过滤 | 20%  | 基于用户行为相似度             |
| RAG      | 动态 | 面试后生成个性化推荐理由       |

### 3️⃣ 实时多 Agent 协作

WebSocket 实时通信，并行执行优化性能：

- 响应时间从 4 秒优化到 1.5 秒
- 流式输出提升用户体验
- 优雅降级处理 LLM 失败

---

## 📖 文档

| 文档                                                          | 内容                 | 阅读时间 |
| ------------------------------------------------------------- | -------------------- | -------- |
| [架构总览](docs/technical/01-architecture-overview.md)           | 系统整体架构、技术栈 | 15 分钟  |
| [Agent 系统设计](docs/technical/02-agent-system-design.md)       | Multi-Agent 架构详解 | 20 分钟  |
| [RAG 与推荐系统](docs/technical/03-rag-and-recommendation.md)    | 推荐算法实现         | 20 分钟  |
| [核心概念指南](docs/technical/04-core-concepts-for-beginners.md) | Agent/RAG 概念解释   | 15 分钟  |
| [面试准备指南](docs/technical/05-interview-preparation.md)       | 面试话术、常见问题   | 25 分钟  |

更多文档请查看 [docs/](docs/) 目录。
