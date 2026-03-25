"""推荐系统集成与性能 Benchmark 测试

测试内容：
1. API 接口测试
2. 端到端推荐流程
3. 并发性能测试
4. 响应时间测试
"""

import pytest
import asyncio
import time
from statistics import mean, stdev
from typing import List, Dict, Any

from app.tests.benchmark.recommendation_data import (
    TEST_USER_PROFILES,
    TEST_RESOURCES,
    calculate_tag_overlap,
    get_user_profile,
    PERSONALIZED_REC_TIME_THRESHOLD,
    REPORT_REC_TIME_THRESHOLD,
    RAG_REC_TIME_THRESHOLD,
)


pytestmark = pytest.mark.asyncio


class TestRecommendationAPI:
    """推荐 API 测试类"""

    async def test_personalized_endpoint(self, client):
        """测试个性化推荐接口"""
        test_user = get_user_profile(1001)
        assert test_user is not None

        start = time.time()
        response = await client.post(
            "/api/v1/recommendations/personalized",
            json={"limit": 5}
        )
        elapsed = time.time() - start

        print(f"\n个性化推荐 API:")
        print(f"  状态码: {response.status_code}")
        print(f"  响应时间: {elapsed:.3f}s")

        assert response.status_code == 200

        data = response.json()
        assert "recommendations" in data
        assert len(data["recommendations"]) <= 5

        # 检查推荐结构
        for rec in data["recommendations"][:3]:
            print(f"  推荐: {rec.get('name', 'N/A')[:30]}... (score: {rec.get('score', 'N/A')})")

    async def test_report_recommendation_endpoint(self, client):
        """测试报告推荐接口"""
        # 使用测试会话ID
        session_id = 1

        start = time.time()
        response = await client.get(f"/api/v1/recommendations/report/{session_id}")
        elapsed = time.time() - start

        print(f"\n报告推荐 API:")
        print(f"  状态码: {response.status_code}")
        print(f"  响应时间: {elapsed:.3f}s")

        # 可能返回 404（如果没有该会话），但不应返回 500
        assert response.status_code in [200, 404]

        if response.status_code == 200:
            data = response.json()
            assert "recommendations" in data or "weak_areas" in data

    async def test_popular_recommendations_endpoint(self, client):
        """测试热门推荐接口"""
        start = time.time()
        response = await client.get("/api/v1/recommendations/popular?limit=5")
        elapsed = time.time() - start

        print(f"\n热门推荐 API:")
        print(f"  状态码: {response.status_code}")
        print(f"  响应时间: {elapsed:.3f}s")

        assert response.status_code == 200

        data = response.json()
        assert "recommendations" in data

    async def test_jobs_recommendation_endpoint(self, client):
        """测试岗位推荐接口"""
        start = time.time()
        response = await client.get("/api/v1/recommendations/jobs")
        elapsed = time.time() - start

        print(f"\n岗位推荐 API:")
        print(f"  状态码: {response.status_code}")
        print(f"  响应时间: {elapsed:.3f}s")

        assert response.status_code == 200

        data = response.json()
        assert "jobs" in data


class TestEndToEndRecommendation:
    """端到端推荐流程测试"""

    async def test_complete_recommendation_flow(self):
        """
        完整流程测试：
        1. 模拟用户面试评估
        2. 获取个性化推荐
        3. 验证推荐与薄弱维度相关
        """
        from app.services.recommendation_service import RecommendationService
        from app.database import async_session_factory

        test_user = get_user_profile(1001)  # Python 薄弱用户
        assert test_user is not None

        print(f"\n端到端推荐流程测试 (用户 {test_user['user_id']}):")

        async with async_session_factory() as db:
            service = RecommendationService()

            # 获取推荐
            start = time.time()
            recommendations = await service.get_recommendations_for_user(
                db, test_user["user_id"], limit=5
            )
            elapsed = time.time() - start

            print(f"  推荐数量: {len(recommendations)}")
            print(f"  响应时间: {elapsed:.3f}s")

            # 验证推荐结构
            for i, rec in enumerate(recommendations[:3]):
                print(f"  推荐 {i+1}: {rec.get('name', 'N/A')[:30]}...")
                assert "score" in rec, "推荐应包含分数"
                assert "reason" in rec, "推荐应包含理由"

            # 验证与薄弱维度的关联
            overlap = calculate_tag_overlap(recommendations, test_user.get("expected_tags", []))
            print(f"  标签重叠度: {overlap:.3f}")

            assert len(recommendations) > 0, "应返回推荐结果"
            assert overlap >= 0.30, f"推荐关联度 {overlap:.3f} 过低"

    async def test_recommendation_with_interview_context(self):
        """测试结合面试上下文的推荐"""
        from app.services.recommendation_service import RecommendationService
        from app.database import async_session_factory

        # 测试不同薄弱维度的用户
        test_cases = [
            (1001, ["Python", "数据结构"]),  # 编程薄弱
            (1002, ["沟通技巧", "压力管理"]),  # 软技能薄弱
        ]

        for user_id, expected_keywords in test_cases:
            user_profile = get_user_profile(user_id)
            if not user_profile:
                continue

            print(f"\n面试上下文推荐测试 (用户 {user_id}):")

            async with async_session_factory() as db:
                service = RecommendationService()
                recommendations = await service.get_recommendations_for_user(
                    db, user_id, limit=5
                )

                # 检查推荐理由中是否包含相关关键词
                matched = 0
                for rec in recommendations:
                    reason = rec.get("reason", "").lower()
                    if any(kw.lower() in reason for kw in expected_keywords):
                        matched += 1

                match_rate = matched / len(recommendations) if recommendations else 0
                print(f"  关键词匹配率: {match_rate:.1%}")
                print(f"  推荐理由示例: {recommendations[0].get('reason', 'N/A')[:60]}..." if recommendations else "  无推荐")


class TestRecommendationPerformance:
    """推荐性能测试类"""

    async def test_personalized_response_time(self):
        """测试个性化推荐响应时间"""
        from app.services.recommendation_service import RecommendationService
        from app.database import async_session_factory

        test_user = get_user_profile(1001)
        assert test_user is not None

        response_times = []

        async with async_session_factory() as db:
            service = RecommendationService()

            for _ in range(5):
                start = time.time()
                await service.get_recommendations_for_user(
                    db, test_user["user_id"], limit=5
                )
                elapsed = time.time() - start
                response_times.append(elapsed)

        avg_time = mean(response_times)
        max_time = max(response_times)
        min_time = min(response_times)

        print(f"\n个性化推荐性能:")
        print(f"  平均响应时间: {avg_time:.3f}s")
        print(f"  最大响应时间: {max_time:.3f}s")
        print(f"  最小响应时间: {min_time:.3f}s")

        # 断言检查
        assert avg_time < PERSONALIZED_REC_TIME_THRESHOLD, \
            f"平均响应时间 {avg_time:.3f}s 超过阈值 {PERSONALIZED_REC_TIME_THRESHOLD}s"

    async def test_concurrent_recommendations(self):
        """测试并发推荐性能"""
        from app.services.recommendation_service import RecommendationService
        from app.database import async_session_factory

        test_users = [p for p in TEST_USER_PROFILES if p["evaluation"] is not None][:3]

        async def get_recommendations_for_user(user_id: int) -> tuple[int, float, bool]:
            """获取推荐并返回结果"""
            try:
                async with async_session_factory() as db:
                    service = RecommendationService()
                    start = time.time()
                    result = await service.get_recommendations_for_user(db, user_id, limit=5)
                    elapsed = time.time() - start
                    return user_id, elapsed, len(result) > 0
            except Exception as e:
                print(f"  用户 {user_id} 推荐失败: {e}")
                return user_id, 0.0, False

        print(f"\n并发推荐测试 ({len(test_users)} 用户):")

        start = time.time()
        tasks = [get_recommendations_for_user(u["user_id"]) for u in test_users]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        total_elapsed = time.time() - start

        success_count = sum(1 for r in results if isinstance(r, tuple) and r[2])
        response_times = [r[1] for r in results if isinstance(r, tuple)]

        print(f"  总时间: {total_elapsed:.3f}s")
        print(f"  成功数: {success_count}/{len(test_users)}")
        if response_times:
            print(f"  平均响应时间: {mean(response_times):.3f}s")

        # 并发成功率应高
        assert success_count / len(test_users) >= 0.80, "并发成功率过低"

    async def test_recommendation_caching(self):
        """测试推荐结果缓存效果"""
        from app.services.recommendation_service import RecommendationService
        from app.database import async_session_factory

        test_user = get_user_profile(1001)
        assert test_user is not None

        async with async_session_factory() as db:
            service = RecommendationService()

            # 第一次调用（可能无缓存）
            start1 = time.time()
            result1 = await service.get_recommendations_for_user(
                db, test_user["user_id"], limit=5
            )
            time1 = time.time() - start1

            # 第二次调用（应有缓存）
            start2 = time.time()
            result2 = await service.get_recommendations_for_user(
                db, test_user["user_id"], limit=5
            )
            time2 = time.time() - start2

        print(f"\n推荐缓存效果:")
        print(f"  首次调用: {time1:.3f}s")
        print(f"  二次调用: {time2:.3f}s")
        print(f"  加速比: {time1/time2:.2f}x" if time2 > 0 else "  无法计算")

        # 两次结果应一致
        assert len(result1) == len(result2), "缓存前后结果数量应一致"


class TestRecommendationRobustness:
    """推荐系统鲁棒性测试"""

    async def test_invalid_user_id(self):
        """测试无效用户ID处理"""
        from app.services.recommendation_service import RecommendationService
        from app.database import async_session_factory

        async with async_session_factory() as db:
            service = RecommendationService()

            # 使用不存在的用户ID
            recommendations = await service.get_recommendations_for_user(
                db, user_id=99999, limit=5
            )

            print(f"\n无效用户ID测试:")
            print(f"  推荐数量: {len(recommendations)}")

            # 应返回空列表或默认推荐，不应报错
            assert isinstance(recommendations, list), "应返回列表"

    async def test_empty_database(self):
        """测试空数据库情况"""
        # 此测试需要特殊设置，暂时跳过
        pytest.skip("需要空数据库环境")

    async def test_recommendation_stability(self):
        """测试推荐结果稳定性"""
        from app.services.recommendation_service import RecommendationService
        from app.database import async_session_factory

        test_user = get_user_profile(1001)
        assert test_user is not None

        results = []

        async with async_session_factory() as db:
            service = RecommendationService()

            # 多次获取推荐
            for _ in range(3):
                recs = await service.get_recommendations_for_user(
                    db, test_user["user_id"], limit=5
                )
                results.append([r.get("id") for r in recs])

        print(f"\n推荐稳定性测试:")
        print(f"  第1次: {results[0]}")
        print(f"  第2次: {results[1]}")
        print(f"  第3次: {results[2]}")

        # 多次推荐应基本一致（规则推荐应完全一致）
        overlap_1_2 = len(set(results[0]) & set(results[1])) / len(results[0]) if results[0] else 0
        print(f"  第1、2次重叠率: {overlap_1_2:.1%}")

        assert overlap_1_2 >= 0.60, "推荐结果应相对稳定"


async def run_recommendation_integration_benchmark():
    """运行推荐集成 benchmark"""
    print("\n" + "="*70)
    print("推荐系统集成与性能 Benchmark")
    print("="*70)

    # API 测试
    print("\n[API 测试]")
    print("  (需要运行中的服务器)")

    # 端到端测试
    print("\n[端到端测试]")
    try:
        e2e_test = TestEndToEndRecommendation()
        await e2e_test.test_complete_recommendation_flow()
        print("  ✓ 通过")
    except Exception as e:
        print(f"  ✗ 失败: {e}")

    # 性能测试
    print("\n[性能测试]")
    try:
        perf_test = TestRecommendationPerformance()
        await perf_test.test_personalized_response_time()
        print("  ✓ 响应时间测试通过")
    except Exception as e:
        print(f"  ✗ 响应时间测试失败: {e}")

    try:
        await perf_test.test_concurrent_recommendations()
        print("  ✓ 并发测试通过")
    except Exception as e:
        print(f"  ✗ 并发测试失败: {e}")

    # 鲁棒性测试
    print("\n[鲁棒性测试]")
    try:
        robust_test = TestRecommendationRobustness()
        await robust_test.test_invalid_user_id()
        print("  ✓ 无效用户ID测试通过")
    except Exception as e:
        print(f"  ✗ 无效用户ID测试失败: {e}")


if __name__ == "__main__":
    asyncio.run(run_recommendation_integration_benchmark())
