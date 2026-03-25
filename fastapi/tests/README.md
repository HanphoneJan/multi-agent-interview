# FastAPI 测试目录

本文档说明 FastAPI 项目的测试组织结构。

## 目录结构

```
tests/
├── README.md                    # 本文档
├── unit/                        # 单元测试
│   ├── test_500_cors.py         # CORS 500错误测试
│   ├── test_cors.py             # CORS 配置测试
│   ├── test_recommendation_api.py # 推荐 API 测试
│   ├── test_syntax_and_structure.py # 语法结构测试
│   └── test_vector_system.py    # 向量系统测试
└── integration/                 # 集成测试
    ├── test_connections.py      # 连接测试
    ├── test_endpoints.py        # API 端点测试
    ├── test_full_integration.py # 完整集成测试
    ├── test_integration.py      # 基础集成测试
    ├── test_local_realtime.py   # 本地实时测试
    ├── test_nonrealtime_interview.py # 非实时面试测试
    ├── test_qwen3_omni.py       # Qwen3-Omni 测试
    ├── test_qwen3_omni_direct.py # Qwen3-Omni 直连测试
    ├── test_qwen3_omni_http.py  # Qwen3-Omni HTTP 测试
    ├── test_qwen3_omni_http_quick.py # Qwen3-Omni 快速测试
    └── test_websocket_endpoint.py # WebSocket 端点测试
```

## 应用内测试

应用核心业务逻辑的测试位于 `app/tests/` 目录：

```
app/tests/
├── agents/                      # Agent 系统测试
├── benchmark/                   # 基准测试
├── test_api/                    # API 接口测试
├── test_core/                   # 核心功能测试
├── test_recommenders/           # 推荐算法测试
├── test_services/               # 服务层测试
├── test_av_services.py          # 音视频服务测试
├── test_celery_tasks.py         # Celery 任务测试
├── test_integration_realtime_dialogue.py # 实时对话集成测试
├── test_interview_crew_integration.py    # Crew 模式集成测试
├── test_tasks.py                # 任务队列测试
└── test_websockets.py           # WebSocket 测试
```

## 运行测试

```bash
# 运行所有测试
uv run pytest

# 运行单元测试
uv run pytest tests/unit/ -v

# 运行集成测试
uv run pytest tests/integration/ -v

# 运行应用内测试
uv run pytest app/tests/ -v
```
