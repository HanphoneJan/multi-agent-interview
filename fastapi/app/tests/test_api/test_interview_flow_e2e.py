"""完整面试流程 E2E 测试（无语音）

从注册到评估报告的端到端流程，纯 API 调用，不依赖前端与语音。
运行时可加 -s 参数查看步骤输出：pytest app/tests/test_api/test_interview_flow_e2e.py -v -s
"""
import uuid
import pytest
from httpx import AsyncClient


def _log(step: int, msg: str, data: dict | None = None):
    """输出步骤信息，便于观察测试过程"""
    sep = "=" * 60
    print(f"\n{sep}")
    print(f"  [步骤 {step}] {msg}")
    if data:
        for k, v in data.items():
            print(f"    -> {k}: {v}")
    print(sep)


@pytest.mark.asyncio
async def test_complete_interview_flow_without_voice(async_client: AsyncClient):
    """
    完整面试流程 E2E 测试（无语音、不对接前端）

    流程：注册 → 获取用户 → 创建/获取场景 → 创建会话 → 添加问题
         → 暂停/恢复 → 结束会话 → 创建评估报告 → 获取推荐 → 查看报告列表
    """
    headers = {}
    user_id = None

    # ─── 1. 注册 ─────────────────────────────────────────────────
    suffix = uuid.uuid4().hex[:8]
    reg_data = {
        "username": f"flow_{suffix}",
        "email": f"flow_{suffix}@example.com",
        "password": "testpass123",
        "name": "E2E 流程测试用户",
    }
    r1 = await async_client.post("/api/v1/users/register", json=reg_data)
    assert r1.status_code == 201, f"注册失败: {r1.text}"
    tokens = r1.json()
    headers["Authorization"] = f"Bearer {tokens['access_token']}"
    _log(1, "用户注册成功", {"username": reg_data["username"], "token": tokens["access_token"][:20] + "..."})

    # ─── 2. 获取当前用户信息 ──────────────────────────────────────
    r2 = await async_client.get("/api/v1/users/me", headers=headers)
    assert r2.status_code == 200, f"获取用户信息失败: {r2.text}"
    user = r2.json()
    user_id = user["id"]
    _log(2, "获取当前用户", {"user_id": user_id, "username": user.get("username")})

    # ─── 3. 获取或创建面试场景 ─────────────────────────────────────
    r3 = await async_client.get("/api/v1/interviews/scenarios?limit=10")
    assert r3.status_code == 200, f"获取场景列表失败: {r3.text}"
    scenarios = r3.json().get("items", [])
    if scenarios:
        scenario_id = scenarios[0]["id"]
        _log(3, "使用已有场景", {"scenario_id": scenario_id, "name": scenarios[0]["name"]})
    else:
        scenario_data = {
            "name": "E2E 流程测试场景",
            "technology_field": "Python",
            "description": "端到端测试用场景",
            "is_realtime": True,
        }
        r3b = await async_client.post("/api/v1/interviews/scenarios", json=scenario_data)
        assert r3b.status_code == 201, f"创建场景失败: {r3b.text}"
        scenario_id = r3b.json()["id"]
        _log(3, "创建新场景", {"scenario_id": scenario_id, "name": scenario_data["name"]})

    # ─── 4. 创建面试会话 ───────────────────────────────────────────
    r4 = await async_client.post(
        "/api/v1/interviews/sessions",
        headers=headers,
        json={"scenario_id": scenario_id},
    )
    assert r4.status_code == 201, f"创建会话失败: {r4.text}"
    session = r4.json()
    session_id = session["id"]
    _log(4, "创建面试会话", {"session_id": session_id, "status": session.get("status")})

    # ─── 5. 添加面试问题 ──────────────────────────────────────────
    questions = [
        ("请简单介绍一下你自己", 1),
        ("描述一个你参与过的重要项目", 2),
        ("你如何解决技术难题？", 3),
    ]
    for q_text, q_num in questions:
        r5 = await async_client.post(
            f"/api/v1/interviews/sessions/{session_id}/questions",
            json={"question_text": q_text, "question_number": q_num},
        )
        assert r5.status_code == 201, f"添加问题失败: {r5.text}"
    _log(5, "添加面试问题", {"count": len(questions), "questions": [q[0][:15] + "..." for q in questions]})

    # ─── 6. 将会话置为进行中 → 暂停 → 恢复 ─────────────────────────────
    r6_start = await async_client.put(
        f"/api/v1/interviews/sessions/{session_id}",
        json={"status": "in_progress"},
    )
    assert r6_start.status_code == 200, f"更新为进行中失败: {r6_start.text}"
    _log(6, "将会话置为进行中", {"status": r6_start.json().get("status")})

    r6a = await async_client.put(f"/api/v1/interviews/sessions/{session_id}/pause")
    assert r6a.status_code == 200, f"暂停失败: {r6a.text}"
    _log(6, "暂停会话", {"status": r6a.json().get("status")})

    r6b = await async_client.put(f"/api/v1/interviews/sessions/{session_id}/resume")
    assert r6b.status_code == 200, f"恢复失败: {r6b.text}"
    _log(6, "恢复会话", {"status": r6b.json().get("status")})

    # ─── 7. 结束会话 ───────────────────────────────────────────────
    r7 = await async_client.post(f"/api/v1/interviews/sessions/{session_id}/end")
    assert r7.status_code == 200, f"结束会话失败: {r7.text}"
    _log(7, "结束面试会话", {"status": r7.json().get("status")})

    # ─── 8. 创建评估报告 ───────────────────────────────────────────
    eval_data = {
        "session_id": session_id,
        "user_id": user_id,
        "overall_evaluation": "候选人整体表现良好，技术基础扎实，表达清晰。",
        "help": "建议加强系统设计方面的准备，多做模拟面试。",
        "recommendation": "通过",
        "overall_score": "78",
        "professional_knowledge": "75",
        "skill_match": "80",
        "language_expression": "75",
        "logical_thinking": "70",
        "stress_response": "82",
        "personality": "78",
        "motivation": "85",
        "value": "80",
    }
    r8 = await async_client.post(
        "/api/v1/evaluations/reports",
        headers=headers,
        json=eval_data,
    )
    assert r8.status_code == 201, f"创建评估报告失败: {r8.text}"
    report = r8.json()
    _log(8, "创建评估报告", {"report_id": report.get("id"), "overall_score": report.get("overall_score"), "recommendation": report.get("recommendation")})

    # ─── 9. 获取个性化推荐 ──────────────────────────────────────────
    r9 = await async_client.post(
        "/api/v1/recommendations/personalized",
        headers=headers,
        json={"limit": 5},
    )
    assert r9.status_code == 200, f"获取推荐失败: {r9.text}"
    rec_data = r9.json()
    rec_count = len(rec_data.get("recommendations", []))
    _log(9, "获取个性化推荐", {"count": rec_count, "type": rec_data.get("type", "unknown")})

    # ─── 9b. 获取 RAG 报告推荐（根据面试报告推荐学习资源） ────────────────
    r9b = await async_client.get(
        f"/api/v1/recommendations/report/{session_id}",
        headers=headers,
        params={"limit": 5},
    )
    assert r9b.status_code == 200, f"获取 RAG 报告推荐失败: {r9b.text}"
    rag_data = r9b.json()
    weak_count = len(rag_data.get("weak_areas", []))
    rec_items = rag_data.get("recommendations", [])
    _log(9, "RAG 报告推荐", {"weak_areas": weak_count, "recommendations": len(rec_items), "overall_advice": bool(rag_data.get("overall_advice"))})

    # ─── 10. 查看评估报告列表 ───────────────────────────────────────
    r10 = await async_client.get(
        "/api/v1/evaluations/reports?limit=10",
        headers=headers,
    )
    assert r10.status_code == 200, f"获取报告列表失败: {r10.text}"
    reports = r10.json().get("items", [])
    _log(10, "查看评估报告列表", {"total": len(reports), "latest_score": reports[0].get("overall_score") if reports else "N/A"})

    print("\n" + "=" * 60)
    print("  [OK] 完整面试流程 E2E 测试通过")
    print("=" * 60 + "\n")
