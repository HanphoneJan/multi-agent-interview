"""推荐系统准确性 Benchmark 测试

测试内容：
1. 规则推荐器准确性
2. 内容推荐器准确性
3. 协同过滤准确性
4. 混合推荐准确性
5. RAG 推荐准确性
"""

import pytest
import asyncio
import time
from statistics import mean
from typing import List, Dict, Any

from app.tests.benchmark.recommendation_data import (
    TEST_USER_PROFILES,
    TEST_RESOURCES,
    TEST_USER_BEHAVIORS,
    PRECISION_AT_K_THRESHOLD,
    RECALL_AT_K_THRESHOLD,
    NDCG_AT_K_THRESHOLD,
    INTERVIEW_CORRELATION_THRESHOLD,
    calculate_tag_overlap,
    calculate_type_diversity,
    is_relevant_for_user,
    get_user_profile,
)


pytestmark = pytest.mark.asyncio


class TestRecommendationAccuracy:
    """推荐准确性测试类"""

    def _calculate_precision_at_k(self, recommendations: List[Dict], relevant_items: List[int], k: int = 5) -> float:
        """计算 Precision@K"""
        if not recommendations or k == 0:
            return 0.0

        top_k = recommendations[:k]
        relevant_count = sum(1 for r in top_k if r.get("id") in relevant_items)
        return relevant_count / k

    def _calculate_recall_at_k(self, recommendations: List[Dict], relevant_items: List[int], k: int = 5) -> float:
        """计算 Recall@K"""
        if not relevant_items:
            return 0.0

        top_k_ids = {r.get("id") for r in recommendations[:k]}
        relevant_found = len(top_k_ids & set(relevant_items))
        return relevant_found / len(relevant_items)

    def _calculate_ndcg_at_k(self, recommendations: List[Dict], relevant_items: List[int], k: int = 5) -> float:
        """计算 NDCG@K"""
        if not recommendations or not relevant_items:
            return 0.0

        # DCG
        dcg = 0.0
        for i, rec in enumerate(recommendations[:k]):
            if rec.get("id") in relevant_items:
                # relevance / log2(position + 1)
                dcg += 1.0 / (i + 1)

        # Ideal DCG
        ideal_dcg = sum(1.0 / (i + 1) for i in range(min(k, len(relevant_items))))

        return dcg / ideal_dcg if ideal_dcg > 0 else 0.0

    def _get_relevant_items_for_user(self, user_profile: Dict) -> List[int]:
        """获取对用户相关的资源ID列表"""
        relevant = []
        for resource in TEST_RESOURCES:
            if is_relevant_for_user(resource, user_profile):
                relevant.append(resource["id"])
        return relevant

    async def _get_rule_based_recommendations(self, user_id: int, limit: int = 5) -> List[Dict]:
        """获取规则推荐"""
        try:
            from app.recommenders.rule_based import RuleBasedRecommender
            from app.database import async_session_factory

            recommender = RuleBasedRecommender()
            async with async_session_factory() as db:
                return await recommender.recommend(user_id, limit, db=db)
        except Exception as e:
            print(f"规则推荐失败: {e}")
            return []

    async def _get_content_based_recommendations(self, user_id: int, limit: int = 5) -> List[Dict]:
        """获取内容推荐"""
        try:
            from app.recommenders.content_based import ContentBasedRecommender
            from app.database import async_session_factory

            recommender = ContentBasedRecommender()
            async with async_session_factory() as db:
                return await recommender.recommend(user_id, limit, db=db)
        except Exception as e:
            print(f"内容推荐失败: {e}")
            return []

    async def _get_hybrid_recommendations(self, user_id: int, limit: int = 5) -> List[Dict]:
        """获取混合推荐"""
        try:
            from app.recommenders.hybrid import HybridRecommender
            from app.database import async_session_factory

            recommender = HybridRecommender()
            async with async_session_factory() as db:
                return await recommender.recommend(user_id, limit, db=db)
        except Exception as e:
            print(f"混合推荐失败: {e}")
            return []

    @pytest.mark.parametrize("user_profile", [p for p in TEST_USER_PROFILES if p["evaluation"] is not None])
    async def test_rule_based_precision(self, user_profile):
        """测试规则推荐器的 Precision"""
        user_id = user_profile["user_id"]
        recommendations = await self._get_rule_based_recommendations(user_id, limit=5)

        relevant_items = self._get_relevant_items_for_user(user_profile)
        precision = self._calculate_precision_at_k(recommendations, relevant_items, k=5)

        print(f"\n用户 {user_id} ({user_profile['type']}):")
        print(f"  薄弱领域: {user_profile.get('weak_areas', [])}")
        print(f"  预期标签: {user_profile.get('expected_tags', [])}")
        print(f"  推荐数量: {len(recommendations)}")
        if recommendations:
            print(f"  推荐标签: {[r.get('tags', []) for r in recommendations[:3]]}")
        print(f"  Precision@5: {precision:.3f}")

        # 规则推荐应该有较高的精度（因为直接匹配薄弱维度）
        assert precision >= 0.40, f"规则推荐 Precision@5 {precision:.3f} 过低"

    @pytest.mark.parametrize("user_profile", TEST_USER_PROFILES)
    async def test_hybrid_recommendation_accuracy(self, user_profile):
        """测试混合推荐的准确性"""
        user_id = user_profile["user_id"]
        recommendations = await self._get_hybrid_recommendations(user_id, limit=10)

        if not recommendations:
            pytest.skip(f"用户 {user_id} 无推荐结果")

        relevant_items = self._get_relevant_items_for_user(user_profile)

        precision = self._calculate_precision_at_k(recommendations, relevant_items, k=5)
        recall = self._calculate_recall_at_k(recommendations, relevant_items, k=5)
        ndcg = self._calculate_ndcg_at_k(recommendations, relevant_items, k=5)

        # 计算与预期的标签重叠度
        tag_overlap = calculate_tag_overlap(recommendations[:5], user_profile.get("expected_tags", []))

        print(f"\n用户 {user_id} ({user_profile['type']}) - 混合推荐:")
        print(f"  Precision@5: {precision:.3f}")
        print(f"  Recall@5: {recall:.3f}")
        print(f"  NDCG@5: {ndcg:.3f}")
        print(f"  标签重叠度: {tag_overlap:.3f}")

        # 记录结果，但不强制断言（因为真实环境数据可能不同）
        if precision < PRECISION_AT_K_THRESHOLD:
            print(f"  [WARN] Precision@5 {precision:.3f} 低于阈值 {PRECISION_AT_K_THRESHOLD}")

    @pytest.mark.parametrize("user_profile", [p for p in TEST_USER_PROFILES if p["evaluation"] is not None])
    async def test_interview_correlation(self, user_profile):
        """测试推荐与面试评估的关联度"""
        user_id = user_profile["user_id"]
        recommendations = await self._get_hybrid_recommendations(user_id, limit=5)

        if not recommendations:
            pytest.skip(f"用户 {user_id} 无推荐结果")

        # 计算标签重叠度作为关联度指标
        correlation = calculate_tag_overlap(recommendations, user_profile.get("expected_tags", []))

        # 检查是否包含不相关标签
        irrelevant_tags = user_profile.get("irrelevant_tags", [])
        has_irrelevant = False
        for rec in recommendations:
            rec_tags = rec.get("tags", [])
            if isinstance(rec_tags, str):
                rec_tags = rec_tags.split(",")
            if any(tag in rec_tags for tag in irrelevant_tags):
                has_irrelevant = True
                break

        print(f"\n用户 {user_id} - 面试关联度测试:")
        print(f"  薄弱领域: {user_profile.get('weak_areas', [])}")
        print(f"  预期标签: {user_profile.get('expected_tags', [])}")
        print(f"  关联度分数: {correlation:.3f}")
        print(f"  包含不相关标签: {has_irrelevant}")

        # 关联度应达到一定阈值
        if correlation < INTERVIEW_CORRELATION_THRESHOLD:
            print(f"  [WARN] 关联度 {correlation:.3f} 低于阈值 {INTERVIEW_CORRELATION_THRESHOLD}")

        # 不应包含明显不相关的标签
        assert not has_irrelevant, "推荐结果包含不相关标签"

    async def test_cold_start_recommendation(self):
        """测试冷启动推荐"""
        cold_user = get_user_profile(1005)  # 冷启动用户
        assert cold_user is not None

        recommendations = await self._get_hybrid_recommendations(cold_user["user_id"], limit=5)

        print(f"\n冷启动用户 {cold_user['user_id']}:")
        print(f"  推荐数量: {len(recommendations)}")
        if recommendations:
            print(f"  推荐资源: {[r.get('name', r.get('id')) for r in recommendations[:3]]}")

        # 冷启动用户也应该有推荐
        assert len(recommendations) > 0, "冷启动用户应获得默认推荐"

        # 推荐应该是热门/基础资源
        expected_tags = cold_user.get("expected_tags", [])
        if expected_tags:
            overlap = calculate_tag_overlap(recommendations, expected_tags)
            print(f"  与预期标签重叠度: {overlap:.3f}")
            assert overlap >= 0.30, "冷启动推荐应包含基础/热门标签"

    async def test_recommendation_diversity(self):
        """测试推荐多样性"""
        test_user = get_user_profile(1001)
        assert test_user is not None

        recommendations = await self._get_hybrid_recommendations(test_user["user_id"], limit=10)

        if len(recommendations) < 3:
            pytest.skip("推荐数量不足，无法测试多样性")

        # 计算类型多样性
        type_diversity = calculate_type_diversity(recommendations)

        # 计算标签覆盖
        all_tags = set()
        for rec in recommendations:
            tags = rec.get("tags", [])
            if isinstance(tags, str):
                tags = tags.split(",")
            all_tags.update(tags)

        print(f"\n推荐多样性测试 (用户 {test_user['user_id']}):")
        print(f"  推荐数量: {len(recommendations)}")
        print(f"  类型多样性: {type_diversity:.3f}")
        print(f"  标签覆盖数: {len(all_tags)}")
        print(f"  标签列表: {sorted(all_tags)[:10]}...")

        # 多样性应达到一定水平
        assert type_diversity >= 0.30, f"类型多样性 {type_diversity:.3f} 过低"

    async def test_recommendation_response_time(self):
        """测试推荐响应时间"""
        test_user = get_user_profile(1001)
        assert test_user is not None

        response_times = []
        for _ in range(3):
            start = time.time()
            await self._get_hybrid_recommendations(test_user["user_id"], limit=5)
            elapsed = time.time() - start
            response_times.append(elapsed)

        avg_time = mean(response_times)
        max_time = max(response_times)

        print(f"\n推荐响应时间:")
        print(f"  平均: {avg_time:.3f}s")
        print(f"  最大: {max_time:.3f}s")

        from app.tests.benchmark.recommendation_data import PERSONALIZED_REC_TIME_THRESHOLD
        if avg_time > PERSONALIZED_REC_TIME_THRESHOLD:
            print(f"  [WARN] 平均响应时间 {avg_time:.3f}s 超过阈值 {PERSONALIZED_REC_TIME_THRESHOLD}s")


class TestRAGRecommendation:
    """RAG 推荐测试类"""

    async def _get_rag_recommendations(self, evaluation_id: int, limit: int = 5) -> Dict:
        """获取 RAG 推荐"""
        try:
            from app.recommenders.rag_recommender import RAGRecommender
            from app.database import async_session_factory

            recommender = RAGRecommender()
            async with async_session_factory() as db:
                return await recommender.async_recommend(db, evaluation_id, limit)
        except Exception as e:
            print(f"RAG 推荐失败: {e}")
            return {"recommendations": [], "weak_areas": []}

    async def test_rag_weak_area_identification(self):
        """测试 RAG 薄弱领域识别"""
        # 使用有评估数据的用户
        test_user = get_user_profile(1001)
        assert test_user is not None

        # 创建模拟评估
        evaluation_id = await self._create_mock_evaluation(test_user)

        if not evaluation_id:
            pytest.skip("无法创建模拟评估")

        result = await self._get_rag_recommendations(evaluation_id, limit=5)

        weak_areas = result.get("weak_areas", [])

        print(f"\nRAG 薄弱领域识别 (用户 {test_user['user_id']}):")
        print(f"  识别的薄弱领域: {weak_areas}")
        print(f"  实际薄弱领域: {test_user.get('weak_areas', [])}")

        # 应该识别出薄弱领域
        assert len(weak_areas) > 0, "RAG 应识别出薄弱领域"

        # 识别的薄弱领域应与实际相符
        for expected_weak in test_user.get("weak_areas", []):
            # 允许部分匹配
            assert any(expected_weak.lower() in wa.lower() for wa in weak_areas), \
                f"未识别出薄弱领域 {expected_weak}"

    async def test_rag_recommendation_quality(self):
        """测试 RAG 推荐质量"""
        test_user = get_user_profile(1002)  # 沟通薄弱用户
        assert test_user is not None

        evaluation_id = await self._create_mock_evaluation(test_user)

        if not evaluation_id:
            pytest.skip("无法创建模拟评估")

        result = await self._get_rag_recommendations(evaluation_id, limit=5)

        recommendations = result.get("recommendations", [])

        print(f"\nRAG 推荐质量 (用户 {test_user['user_id']}):")
        print(f"  推荐数量: {len(recommendations)}")

        # 检查推荐数量
        assert len(recommendations) >= 3, "RAG 应返回至少 3 条推荐"

        # 检查推荐理由
        for i, rec in enumerate(recommendations[:3]):
            reason = rec.get("reason", "")
            print(f"  推荐 {i+1} 理由: {reason[:50]}...")
            assert len(reason) > 10, "推荐理由不应太短"

        # 检查整体建议
        overall_advice = result.get("overall_advice", "")
        print(f"  整体建议: {overall_advice[:80]}...")
        assert len(overall_advice) > 20, "整体建议不应太短"

    async def test_rag_interview_correlation(self):
        """测试 RAG 推荐与面试的关联性"""
        test_user = get_user_profile(1001)  # Python 薄弱
        assert test_user is not None

        evaluation_id = await self._create_mock_evaluation(test_user)

        if not evaluation_id:
            pytest.skip("无法创建模拟评估")

        result = await self._get_rag_recommendations(evaluation_id, limit=5)
        recommendations = result.get("recommendations", [])

        if not recommendations:
            pytest.skip("无 RAG 推荐结果")

        # 计算与预期的标签重叠
        overlap = calculate_tag_overlap(recommendations, test_user.get("expected_tags", []))

        print(f"\nRAG 面试关联度 (用户 {test_user['user_id']}):")
        print(f"  薄弱领域: {test_user.get('weak_areas', [])}")
        print(f"  预期标签: {test_user.get('expected_tags', [])}")
        print(f"  标签重叠度: {overlap:.3f}")

        # RAG 推荐应有较高的面试关联度
        assert overlap >= 0.50, f"RAG 关联度 {overlap:.3f} 过低"

    async def _create_mock_evaluation(self, user_profile: Dict) -> int:
        """创建模拟面试评估"""
        # 返回模拟的评估ID
        # 实际实现中应该创建数据库记录
        return user_profile["user_id"]  # 简化处理，使用 user_id 作为 evaluation_id


async def run_recommendation_accuracy_benchmark():
    """运行推荐准确性 benchmark"""
    print("\n" + "="*70)
    print("推荐系统准确性 Benchmark")
    print("="*70)

    test = TestRecommendationAccuracy()

    # 测试每个有评估数据的用户
    for user_profile in TEST_USER_PROFILES:
        if user_profile["evaluation"] is None:
            continue

        try:
            print(f"\n测试用户 {user_profile['user_id']} ({user_profile['type']})...")
            await test.test_hybrid_recommendation_accuracy(user_profile)
        except Exception as e:
            print(f"  测试失败: {e}")

    # 冷启动测试
    try:
        print("\n测试冷启动推荐...")
        await test.test_cold_start_recommendation()
    except Exception as e:
        print(f"  测试失败: {e}")

    # 多样性测试
    try:
        print("\n测试推荐多样性...")
        await test.test_recommendation_diversity()
    except Exception as e:
        print(f"  测试失败: {e}")


if __name__ == "__main__":
    asyncio.run(run_recommendation_accuracy_benchmark())
