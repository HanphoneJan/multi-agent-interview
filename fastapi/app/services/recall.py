"""多路召回服务"""
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass
from collections import defaultdict
import asyncio
import random

from app.core.milvus_client import MilvusClient
from app.core.embedding import EmbeddingService
from app.core.redis_client import RedisCache
from app.core.rec_database import AsyncSessionLocal
from sqlalchemy import text


@dataclass
class RecallResult:
    """召回结果"""
    resource_id: str
    score: float
    recall_type: str  # 召回来源
    reason: str = ""  # 召回原因


class VectorRecall:
    """向量召回 - 基于 Milvus ANN 搜索"""

    def __init__(self):
        self.milvus = MilvusClient()
        self.embedding = EmbeddingService()

    async def recall(
        self,
        query_text: str,
        user_id: str,
        top_k: int = 100,
        filters: str = None
    ) -> List[RecallResult]:
        """向量召回"""
        # 生成查询向量
        query_embedding = self.embedding.encode(query_text)

        # ANN 搜索
        await self.milvus.connect()
        results = await self.milvus.search(
            query_embedding=query_embedding,
            top_k=top_k,
            filters=filters
        )
        await self.milvus.disconnect()

        return [
            RecallResult(
                resource_id=r["resource_id"],
                score=r["score"],
                recall_type="vector",
                reason=f"相似度: {r['score']:.3f}"
            )
            for r in results
        ]


class I2IRecall:
    """I2I 协同过滤召回 - 基于 ItemCF"""

    def __init__(self):
        self.redis = RedisCache()

    async def recall(
        self,
        user_id: str,
        top_k: int = 50
    ) -> List[RecallResult]:
        """I2I 召回"""
        # 获取用户历史行为
        user_history = await self._get_user_history(user_id)

        if not user_history:
            return []

        # 获取相似物品
        similar_items = await self._get_similar_items(user_history, top_k)

        return [
            RecallResult(
                resource_id=item_id,
                score=score,
                recall_type="i2i",
                reason=f"与历史物品相似: {score:.3f}"
            )
            for item_id, score in similar_items
        ]

    async def _get_user_history(self, user_id: str) -> List[str]:
        """获取用户历史交互的资源"""
        # 从 Redis 获取
        key = f"user:{user_id}:history"
        history = await self.redis.get(key)

        if history:
            return history.split(",")

        # 从数据库获取
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                text("""
                    SELECT DISTINCT resource_id
                    FROM user_events
                    WHERE user_id = :user_id
                    AND event_type IN ('click', 'complete', 'rate')
                    ORDER BY created_at DESC
                    LIMIT 20
                """),
                {"user_id": user_id}
            )
            history = [row[0] for row in result.fetchall()]

        # 缓存到 Redis
        if history:
            await self.redis.set(key, ",".join(history), expire=3600)

        return history

    async def _get_similar_items(
        self,
        item_ids: List[str],
        top_k: int
    ) -> List[tuple]:
        """获取相似物品"""
        # 从数据库获取 I2I 相似度
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                text("""
                    SELECT similar_item_id, similarity_score
                    FROM item_similarities
                    WHERE item_id = ANY(:item_ids)
                    ORDER BY similarity_score DESC
                    LIMIT :limit
                """),
                {"item_ids": item_ids, "limit": top_k}
            )

            items = [(row[0], row[1]) for row in result.fetchall()]

        return items


class HotRecall:
    """热门召回 - 基于全局热度"""

    def __init__(self):
        self.redis = RedisCache()

    async def recall(
        self,
        top_k: int = 50,
        resource_type: str = None
    ) -> List[RecallResult]:
        """热门召回"""
        # 从 Redis 获取热门列表
        key = f"hot:resources:{resource_type or 'all'}"
        hot_list = await self.redis.get(key)

        if hot_list:
            items = hot_list.split(",")
        else:
            # 从数据库获取
            async with AsyncSessionLocal() as session:
                where_clause = ""
                params = {"limit": top_k}

                if resource_type:
                    where_clause = "WHERE resource_type = :resource_type"
                    params["resource_type"] = resource_type

                result = await session.execute(
                    text(f"""
                        SELECT id::text, views
                        FROM resources
                        {where_clause}
                        ORDER BY views DESC
                        LIMIT :limit
                    """),
                    params
                )

                items = [row[0] for row in result.fetchall()]

            # 缓存
            if items:
                await self.redis.set(key, ",".join(items), expire=300)

        # 计算热度分数 (归一化)
        results = []
        for i, item_id in enumerate(items[:top_k]):
            # 排名越靠前，分数越高
            score = 1.0 - (i / len(items)) if items else 0.0
            results.append(RecallResult(
                resource_id=item_id,
                score=score,
                recall_type="hot",
                reason=f"热度排名: {i+1}"
            ))

        return results


class NewResourceRecall:
    """新资源召回 - 推荐最新添加的资源"""

    def __init__(self):
        self.redis = RedisCache()

    async def recall(
        self,
        top_k: int = 30,
        days: int = 7
    ) -> List[RecallResult]:
        """新资源召回"""
        # 从数据库获取新资源
        async with AsyncSessionLocal() as session:
            # 使用字符串格式化构建完整 SQL（PostgreSQL 不支持参数化的 INTERVAL）
            query = text(f"""
                SELECT id::text, created_at
                FROM resources
                WHERE created_at > NOW() - INTERVAL '{days} days'
                ORDER BY created_at DESC
                LIMIT {top_k}
            """)
            result = await session.execute(query)

            items = [(row[0], row[1]) for row in result.fetchall()]

        return [
            RecallResult(
                resource_id=item_id,
                score=1.0 - (i / len(items)) if items else 0.0,
                recall_type="new",
                reason="新资源"
            )
            for i, (item_id, _) in enumerate(items)
        ]


class RuleRecall:
    """规则召回 - 基于用户画像"""

    def __init__(self):
        pass

    async def recall(
        self,
        user_id: str,
        top_k: int = 50
    ) -> List[RecallResult]:
        """基于用户画像的规则召回"""
        # 获取用户画像
        user_profile = await self._get_user_profile(user_id)

        if not user_profile:
            return []

        results = []

        # 根据偏好难度召回
        preferred_difficulty = user_profile.get("preferred_difficulty")
        if preferred_difficulty:
            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    text("""
                        SELECT id::text, rating
                        FROM resources
                        WHERE difficulty = :difficulty
                        ORDER BY rating DESC
                        LIMIT :limit
                    """),
                    {"difficulty": preferred_difficulty, "limit": top_k // 2}
                )

                for i, (res_id, rating) in enumerate(result.fetchall()):
                    results.append(RecallResult(
                        resource_id=res_id,
                        score=rating / 5.0 if rating else 0.5,
                        recall_type="rule",
                        reason=f"偏好难度: {preferred_difficulty}"
                    ))

        # 根据偏好标签召回
        preferred_types = user_profile.get("preferred_types", [])
        if preferred_types:
            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    text("""
                        SELECT id::text, rating
                        FROM resources
                        WHERE tags && :types
                        ORDER BY rating DESC
                        LIMIT :limit
                    """),
                    {"types": preferred_types, "limit": top_k // 2}
                )

                for i, (res_id, rating) in enumerate(result.fetchall()):
                    results.append(RecallResult(
                        resource_id=res_id,
                        score=rating / 5.0 if rating else 0.5,
                        recall_type="rule",
                        reason=f"偏好类型"
                    ))

        return results

    async def _get_user_profile(self, user_id: str) -> Dict[str, Any]:
        """获取用户画像"""
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                text("""
                    SELECT preferred_difficulty, preferred_types
                    FROM user_profiles
                    WHERE user_id = :user_id
                """),
                {"user_id": user_id}
            )

            row = result.fetchone()
            if row:
                return {
                    "preferred_difficulty": row[0],
                    "preferred_types": row[1] or []
                }
            return {}


class MultiPathRecall:
    """多路召回聚合器"""

    def __init__(self):
        self.vector_recall = VectorRecall()
        self.i2i_recall = I2IRecall()
        self.hot_recall = HotRecall()
        self.new_recall = NewResourceRecall()
        self.rule_recall = RuleRecall()

        # 各路权重
        self.weights = {
            "vector": 1.0,
            "i2i": 0.8,
            "hot": 0.5,
            "new": 0.4,
            "rule": 0.7
        }

    async def recall(
        self,
        user_id: str,
        query_text: str = None,
        top_k: int = 200
    ) -> List[RecallResult]:
        """
        多路召回

        Args:
            user_id: 用户ID
            query_text: 查询文本（用于向量召回）
            top_k: 最终召回数量

        Returns:
            合并后的召回结果列表
        """
        # 并发执行各路召回
        tasks = []

        # 向量召回
        if query_text:
            tasks.append(self._recall_with_fallback(
                self.vector_recall.recall(query_text, user_id, top_k=100),
                "vector"
            ))

        # I2I 召回
        tasks.append(self._recall_with_fallback(
            self.i2i_recall.recall(user_id, top_k=50),
            "i2i"
        ))

        # 热门召回
        tasks.append(self._recall_with_fallback(
            self.hot_recall.recall(top_k=50),
            "hot"
        ))

        # 新资源召回
        tasks.append(self._recall_with_fallback(
            self.new_recall.recall(top_k=30),
            "new"
        ))

        # 规则召回
        tasks.append(self._recall_with_fallback(
            self.rule_recall.recall(user_id, top_k=50),
            "rule"
        ))

        # 等待所有召回完成
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 合并结果
        all_results = []
        for recall_type, result in zip(
            ["vector", "i2i", "hot", "new", "rule"][:len(results)],
            results
        ):
            if isinstance(result, list):
                all_results.extend(result)
            elif isinstance(result, Exception):
                print(f"[WARN] {recall_type} recall failed: {result}")

        # 去重并排序
        merged = self._merge_results(all_results)

        return merged[:top_k]

    async def _recall_with_fallback(
        self,
        coro,
        recall_type: str
    ) -> List[RecallResult]:
        """带异常处理的召回"""
        try:
            return await coro
        except Exception as e:
            print(f"[WARN] {recall_type} recall failed: {e}")
            return []

    def _merge_results(self, results: List[RecallResult]) -> List[RecallResult]:
        """
        合并多路召回结果

        策略:
        1. 去重（同一资源取最高分）
        2. 加权融合
        3. 多样性保证
        """
        # 按资源ID分组，取最高分和来源
        resource_scores = defaultdict(list)
        resource_sources = defaultdict(set)

        for r in results:
            resource_scores[r.resource_id].append(r.score * self.weights.get(r.recall_type, 1.0))
            resource_sources[r.resource_id].add(r.recall_type)

        # 计算融合分数
        merged = []
        for res_id, scores in resource_scores.items():
            # 多路命中加分
            source_bonus = len(resource_sources[res_id]) * 0.1
            final_score = max(scores) + source_bonus

            merged.append(RecallResult(
                resource_id=res_id,
                score=min(final_score, 1.0),  # 限制在 0-1
                recall_type="merged",
                reason=f"来源: {', '.join(resource_sources[res_id])}"
            ))

        # 按分数排序
        merged.sort(key=lambda x: x.score, reverse=True)

        return merged

    def update_weights(self, weights: Dict[str, float]):
        """更新各路权重"""
        self.weights.update(weights)
