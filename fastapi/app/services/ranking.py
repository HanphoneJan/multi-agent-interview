"""排序层服务 - 特征工程与模型推理"""
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
import numpy as np
import asyncio

from app.core.rec_database import AsyncSessionLocal
from app.core.redis_client import RedisCache
from sqlalchemy import text


@dataclass
class FeatureVector:
    """特征向量"""
    user_id: str
    resource_id: str

    # 用户特征
    user_features: Dict[str, Any] = field(default_factory=dict)

    # 资源特征
    resource_features: Dict[str, Any] = field(default_factory=dict)

    # 交叉特征
    cross_features: Dict[str, Any] = field(default_factory=dict)

    # 上下文特征
    context_features: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RankedResult:
    """排序结果"""
    resource_id: str
    score: float
    features: Dict[str, Any] = field(default_factory=dict)
    reason: str = ""


class FeatureService:
    """特征服务"""

    def __init__(self):
        self.redis = RedisCache()

    async def extract_features(
        self,
        user_id: str,
        resource_ids: List[str]
    ) -> List[FeatureVector]:
        """提取特征"""
        # 并发获取各类特征
        user_feat_task = self._get_user_features(user_id)
        resource_feat_task = self._get_resource_features(resource_ids)
        interaction_feat_task = self._get_interaction_features(user_id, resource_ids)

        user_features, resource_features, interaction_features = await asyncio.gather(
            user_feat_task,
            resource_feat_task,
            interaction_feat_task
        )

        # 构建特征向量
        vectors = []
        for res_id in resource_ids:
            vector = FeatureVector(
                user_id=user_id,
                resource_id=res_id,
                user_features=user_features,
                resource_features=resource_features.get(res_id, {}),
                cross_features=interaction_features.get(res_id, {})
            )
            vectors.append(vector)

        return vectors

    async def _get_user_features(self, user_id: str) -> Dict[str, Any]:
        """获取用户特征"""
        # 尝试从 Redis 获取
        cache_key = f"features:user:{user_id}"
        cached = await self.redis.get(cache_key)

        if cached:
            return eval(cached)  # 简单处理，生产环境应使用 json

        # 从数据库获取
        async with AsyncSessionLocal() as session:
            # 用户画像
            profile_result = await session.execute(
                text("""
                    SELECT
                        preferred_difficulty,
                        preferred_types,
                        total_views,
                        total_completes,
                        avg_rating
                    FROM user_profiles
                    WHERE user_id = :user_id
                """),
                {"user_id": user_id}
            )
            profile = profile_result.fetchone()

            # 用户行为统计
            stats_result = await session.execute(
                text("""
                    SELECT
                        COUNT(DISTINCT resource_id) as unique_resources,
                        COUNT(*) as total_events
                    FROM user_events
                    WHERE user_id = :user_id
                    AND created_at > NOW() - INTERVAL '30 days'
                """),
                {"user_id": user_id}
            )
            stats = stats_result.fetchone()

        features = {
            "preferred_difficulty": profile[0] if profile else None,
            "preferred_types": profile[1] if profile else [],
            "total_views": profile[2] if profile else 0,
            "total_completes": profile[3] if profile else 0,
            "avg_rating": float(profile[4]) if profile and profile[4] else 0.0,
            "unique_resources_30d": stats[0] if stats else 0,
            "total_events_30d": stats[1] if stats else 0,
        }

        # 缓存
        await self.redis.set(cache_key, str(features), expire=300)

        return features

    async def _get_resource_features(
        self,
        resource_ids: List[str]
    ) -> Dict[str, Dict[str, Any]]:
        """获取资源特征"""
        if not resource_ids:
            return {}

        async with AsyncSessionLocal() as session:
            result = await session.execute(
                text("""
                    SELECT
                        id::text,
                        resource_type,
                        difficulty,
                        tags,
                        views,
                        completions,
                        rating,
                        created_at
                    FROM resources
                    WHERE id::text = ANY(:resource_ids)
                """),
                {"resource_ids": resource_ids}
            )

            features = {}
            for row in result.fetchall():
                features[row[0]] = {
                    "resource_type": row[1],
                    "difficulty": row[2],
                    "tags": row[3] or [],
                    "views": row[4] or 0,
                    "completions": row[5] or 0,
                    "rating": float(row[6]) if row[6] else 0.0,
                    "created_at": row[7].isoformat() if row[7] else None,
                }

        return features

    async def _get_interaction_features(
        self,
        user_id: str,
        resource_ids: List[str]
    ) -> Dict[str, Dict[str, Any]]:
        """获取用户-资源交互特征"""
        if not resource_ids:
            return {}

        async with AsyncSessionLocal() as session:
            result = await session.execute(
                text("""
                    SELECT
                        resource_id,
                        COUNT(*) as event_count,
                        MAX(created_at) as last_interaction
                    FROM user_events
                    WHERE user_id = :user_id
                    AND resource_id = ANY(:resource_ids)
                    GROUP BY resource_id
                """),
                {"user_id": user_id, "resource_ids": resource_ids}
            )

            features = {}
            for row in result.fetchall():
                features[row[0]] = {
                    "has_interacted": True,
                    "event_count": row[1],
                    "last_interaction": row[2].isoformat() if row[2] else None,
                }

        # 填充未交互的资源
        for res_id in resource_ids:
            if res_id not in features:
                features[res_id] = {
                    "has_interacted": False,
                    "event_count": 0,
                    "last_interaction": None,
                }

        return features


class RankingModel:
    """排序模型（简化版，实际应使用 DeepFM 等）"""

    def __init__(self):
        self.feature_weights = {
            # 用户特征权重
            "user_avg_rating": 0.1,
            "user_activity": 0.05,

            # 资源特征权重
            "resource_rating": 0.25,
            "resource_popularity": 0.15,
            "resource_freshness": 0.1,

            # 交叉特征权重
            "difficulty_match": 0.2,
            "type_match": 0.15,
            "has_interacted": -0.5,  # 已交互的降低权重，避免重复
        }

    def predict(self, features: FeatureVector) -> float:
        """预测分数"""
        score = 0.5  # 基础分

        # 资源评分
        res_rating = features.resource_features.get("rating", 0)
        score += res_rating * self.feature_weights["resource_rating"]

        # 资源热度
        views = features.resource_features.get("views", 0)
        popularity = min(views / 10000, 1.0)  # 归一化
        score += popularity * self.feature_weights["resource_popularity"]

        # 难度匹配
        user_diff = features.user_features.get("preferred_difficulty")
        res_diff = features.resource_features.get("difficulty")
        if user_diff and res_diff:
            diff_match = 1.0 if user_diff == res_diff else 0.5
            score += diff_match * self.feature_weights["difficulty_match"]

        # 类型匹配
        user_types = set(features.user_features.get("preferred_types", []))
        res_tags = set(features.resource_features.get("tags", []))
        if user_types and res_tags:
            type_match = len(user_types & res_tags) / len(user_types)
            score += type_match * self.feature_weights["type_match"]

        # 交互历史
        has_interacted = features.cross_features.get("has_interacted", False)
        if has_interacted:
            score += self.feature_weights["has_interacted"]

        # 限制在 0-1 范围内
        return max(0.0, min(1.0, score))

    def predict_batch(self, feature_vectors: List[FeatureVector]) -> List[float]:
        """批量预测"""
        return [self.predict(fv) for fv in feature_vectors]


class RankingService:
    """排序服务"""

    def __init__(self):
        self.feature_service = FeatureService()
        self.model = RankingModel()

    async def rank(
        self,
        user_id: str,
        resource_ids: List[str]
    ) -> List[RankedResult]:
        """
        排序推荐结果

        Args:
            user_id: 用户ID
            resource_ids: 召回的资源ID列表

        Returns:
            排序后的结果列表
        """
        if not resource_ids:
            return []

        # 提取特征
        feature_vectors = await self.feature_service.extract_features(
            user_id, resource_ids
        )

        # 模型预测
        scores = self.model.predict_batch(feature_vectors)

        # 构建结果
        results = []
        for fv, score in zip(feature_vectors, scores):
            results.append(RankedResult(
                resource_id=fv.resource_id,
                score=score,
                features={
                    "user": fv.user_features,
                    "resource": fv.resource_features,
                    "cross": fv.cross_features
                }
            ))

        # 按分数排序
        results.sort(key=lambda x: x.score, reverse=True)

        return results

    async def rank_with_diversity(
        self,
        user_id: str,
        resource_ids: List[str],
        top_k: int = 10
    ) -> List[RankedResult]:
        """
        带多样性的排序

        使用 MMR (Maximal Marginal Relevance) 算法
        """
        # 先进行基础排序
        ranked = await self.rank(user_id, resource_ids)

        if len(ranked) <= top_k:
            return ranked

        # MMR 多样性重排
        selected = []
        candidates = ranked.copy()

        lambda_param = 0.5  # 相关性 vs 多样性的平衡参数

        while len(selected) < top_k and candidates:
            if not selected:
                # 选择第一个：最高相关性的
                best = candidates[0]
            else:
                # 选择 MMR 分数最高的
                best_mmr_score = -float('inf')
                best = None

                for cand in candidates:
                    # 相关性
                    rel_score = cand.score

                    # 多样性（与已选结果的最大相似度）
                    max_sim = 0.0
                    for sel in selected:
                        sim = self._compute_similarity(cand, sel)
                        max_sim = max(max_sim, sim)

                    # MMR 分数
                    mmr_score = lambda_param * rel_score - (1 - lambda_param) * max_sim

                    if mmr_score > best_mmr_score:
                        best_mmr_score = mmr_score
                        best = cand

            selected.append(best)
            candidates.remove(best)

        return selected

    def _compute_similarity(
        self,
        r1: RankedResult,
        r2: RankedResult
    ) -> float:
        """计算两个结果的相似度（基于特征）"""
        f1 = r1.features.get("resource", {})
        f2 = r2.features.get("resource", {})

        # 类型相同
        type_sim = 1.0 if f1.get("resource_type") == f2.get("resource_type") else 0.0

        # 标签重叠
        tags1 = set(f1.get("tags", []))
        tags2 = set(f2.get("tags", []))
        tag_sim = len(tags1 & tags2) / max(len(tags1 | tags2), 1)

        # 难度相同
        diff_sim = 1.0 if f1.get("difficulty") == f2.get("difficulty") else 0.0

        return (type_sim + tag_sim + diff_sim) / 3.0
