# AI Interview Agent - 技术文档

> 本项目技术文档，帮助理解系统架构并准备Agent开发岗位面试

## 📚 文档清单

| 文档 | 内容 | 阅读时间 |
|-----|------|---------|
| [01-架构总览](01-architecture-overview.md) | 系统整体架构、技术栈、核心亮点 | 15分钟 |
| [02-Agent系统设计](02-agent-system-design.md) | Multi-Agent架构、流程编排引擎详解 | 20分钟 |
| [03-RAG与推荐系统](03-rag-and-recommendation.md) | RAG实现、向量化、混合推荐 | 20分钟 |
| [04-小白概念指南](04-core-concepts-for-beginners.md) | Agent/RAG/Embedding等概念大白话解释 | 15分钟 |
| [05-面试准备指南](05-interview-preparation.md) | 面试话术、常见问题、技术亮点 | 25分钟 |

## 🎯 推荐阅读顺序

### 如果你是小白（零基础）

1. **先读** [04-小白概念指南](04-core-concepts-for-beginners.md)
   - 理解Agent、RAG、Embedding等概念
   - 不用看代码，先建立直觉

2. **再读** [01-架构总览](01-architecture-overview.md)
   - 了解系统整体架构
   - 知道项目有哪些亮点

3. **最后** [05-面试准备指南](05-interview-preparation.md)
   - 准备面试话术
   - 背诵常见问题的回答

### 如果你有一定基础

1. [01-架构总览](01-architecture-overview.md) - 快速了解项目
2. [02-Agent系统设计](02-agent-system-design.md) - 深入核心架构
3. [03-RAG与推荐系统](03-rag-and-recommendation.md) - 理解算法实现
4. [05-面试准备指南](05-interview-preparation.md) - 准备面试

## 💡 核心亮点速览

### 1. 自研Agent框架
- 参考CrewAI设计，轻量灵活
- 支持角色-目标-背景模式
- 实现流程编排引擎（顺序/分支/并行）

### 2. Multi-Agent协作
- InterviewerAgent：提问、追问
- EvaluatorAgent：实时评估（8维度）
- CoachAgent：学习建议

### 3. RAG推荐系统
- 向量检索 + LLM生成推荐理由
- Milvus向量数据库
- 384维Embedding

### 4. 混合推荐
- 4种策略：RAG + 规则 + 内容 + 协同
- 多路召回 + 加权融合
- 多样性重排

## 📊 项目数据

| 指标 | 数值 |
|-----|------|
| 代码行数 | 15,000+ |
| Agent数量 | 3个核心Agent |
| 推荐策略 | 4种 |
| 评估维度 | 8维度 |
| 向量维度 | 384维 |
| 技术栈 | FastAPI + 通义千问 + Milvus |

## 🎤 面试话术速记

### 1分钟版本
```
我开发了一个AI面试Agent系统，核心是Multi-Agent架构，包含面试官、
评估员、学习顾问三个Agent。我采用自研的Agent框架，支持流程编排。
推荐模块实现了RAG+混合推荐。技术栈是FastAPI + 通义千问 + Milvus。
```

### 3分钟版本
```
我开发的AI面试Agent系统，目标是模拟真实技术面试。

核心架构：Multi-Agent设计，三个Agent协作完成任务。

技术亮点：
1. 自研Agent框架，支持流程编排（顺序/分支/并行）
2. 推荐系统采用多路召回，融合RAG+规则+内容+协同
3. RAG推荐结合向量检索和LLM生成推荐理由

技术栈：FastAPI + 通义千问 + Milvus + PostgreSQL
```

## 🔗 相关链接

- [项目根目录README](../../README.md)
- [CLAUDE.md](../../CLAUDE.md) - 项目开发规范
- [FastAPI文档](../../fastapi/docs/)

## ⚠️ 注意事项

1. **不要直接背诵代码**：理解原理，用自己的话表达
2. **承认不懂的地方**：诚实比硬撑更重要
3. **展示学习意愿**：对于不了解的，表达学习的兴趣
4. **准备好项目演示**：如果可能，现场演示效果更好

---

祝你面试成功！
