"""推荐系统 API"""
import json
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from app.services.recall import MultiPathRecall
from app.services.ranking import RankingService

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


# ========== 请求/响应模型 ==========

class PersonalizedRequest(BaseModel):
    """个性化推荐请求"""
    user_id: str
    query: Optional[str] = None
    top_k: int = 10
    diversity: bool = True


class RecommendationItem(BaseModel):
    """推荐项"""
    resource_id: str
    score: float
    reason: str


class RecommendationResponse(BaseModel):
    """推荐响应"""
    user_id: str
    items: List[RecommendationItem]
    total: int


# ========== API 端点 ==========

@router.post("/personalized", response_model=RecommendationResponse)
async def get_personalized_recommendations(request: PersonalizedRequest):
    """
    获取个性化推荐

    流程：
    1. 多路召回（向量、I2I、热门、新资源、规则）
    2. 特征工程与排序
    3. 多样性重排
    """
    try:
        # 召回
        recall_service = MultiPathRecall()
        recalled = await recall_service.recall(
            user_id=request.user_id,
            query_text=request.query,
            top_k=200
        )

        if not recalled:
            return RecommendationResponse(
                user_id=request.user_id,
                items=[],
                total=0
            )

        # 排序
        ranking_service = RankingService()
        resource_ids = [r.resource_id for r in recalled]

        if request.diversity:
            ranked = await ranking_service.rank_with_diversity(
                user_id=request.user_id,
                resource_ids=resource_ids,
                top_k=request.top_k
            )
        else:
            ranked = await ranking_service.rank(
                user_id=request.user_id,
                resource_ids=resource_ids
            )
            ranked = ranked[:request.top_k]

        # 构建响应
        items = [
            RecommendationItem(
                resource_id=r.resource_id,
                score=r.score,
                reason=r.reason
            )
            for r in ranked
        ]

        return RecommendationResponse(
            user_id=request.user_id,
            items=items,
            total=len(items)
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/similar")
async def get_similar_resources(
    resource_id: str,
    top_k: int = Query(default=10, ge=1, le=50)
):
    """获取相似资源（基于向量）"""
    from app.core.milvus_client import MilvusClient
    from app.core.embedding import EmbeddingService
    from app.core.rec_database import AsyncSessionLocal
    from sqlalchemy import text

    try:
        # 获取资源信息
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                text("""
                    SELECT name, tags, difficulty, resource_type
                    FROM resources
                    WHERE id::text = :resource_id
                """),
                {"resource_id": resource_id}
            )
            resource = result.fetchone()

        if not resource:
            raise HTTPException(status_code=404, detail="Resource not found")

        # 构建查询文本
        embed_service = EmbeddingService()
        resource_dict = {
            "name": resource[0],
            "tags": resource[1] or [],
            "difficulty": resource[2],
            "resource_type": resource[3]
        }
        query_text = embed_service.build_resource_text(resource_dict)
        query_embedding = embed_service.encode(query_text)

        # 向量搜索
        milvus = MilvusClient()
        await milvus.connect()
        results = await milvus.search(
            query_embedding=query_embedding,
            top_k=top_k + 1  # 多取一个，排除自身
        )
        await milvus.disconnect()

        # 排除自身
        filtered = [r for r in results if r["resource_id"] != resource_id][:top_k]

        return {
            "resource_id": resource_id,
            "similar": [
                {
                    "resource_id": r["resource_id"],
                    "score": r["score"],
                    "type": r["resource_type"],
                    "difficulty": r["difficulty"]
                }
                for r in filtered
            ]
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/hot")
async def get_hot_resources(
    resource_type: Optional[str] = None,
    top_k: int = Query(default=20, ge=1, le=100)
):
    """获取热门资源"""
    from app.services.recall import HotRecall

    try:
        hot_recall = HotRecall()
        results = await hot_recall.recall(
            top_k=top_k,
            resource_type=resource_type
        )

        return {
            "resource_type": resource_type or "all",
            "items": [
                {
                    "resource_id": r.resource_id,
                    "score": r.score,
                    "reason": r.reason
                }
                for r in results
            ]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/new")
async def get_new_resources(
    days: int = Query(default=7, ge=1, le=30),
    top_k: int = Query(default=20, ge=1, le=100)
):
    """获取新资源"""
    from app.services.recall import NewResourceRecall

    try:
        new_recall = NewResourceRecall()
        results = await new_recall.recall(top_k=top_k, days=days)

        return {
            "days": days,
            "items": [
                {
                    "resource_id": r.resource_id,
                    "score": r.score,
                    "reason": r.reason
                }
                for r in results
            ]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== 事件上报 API ==========

class EventRequest(BaseModel):
    """用户行为事件"""
    user_id: str
    resource_id: str
    event_type: str  # view, click, complete, rate, share
    session_id: Optional[str] = None
    metadata: Optional[dict] = None


@router.post("/events")
async def report_event(request: EventRequest):
    """上报用户行为事件"""
    from app.core.stream_queue import RedisStreamQueue
    from app.core.rec_database import AsyncSessionLocal
    from sqlalchemy import text

    try:
        # 写入 PostgreSQL
        async with AsyncSessionLocal() as session:
            await session.execute(
                text("""
                    INSERT INTO user_events
                    (user_id, resource_id, event_type, session_id, metadata)
                    VALUES (:user_id, :resource_id, :event_type, :session_id, :metadata)
                """),
                {
                    "user_id": request.user_id,
                    "resource_id": request.resource_id,
                    "event_type": request.event_type,
                    "session_id": request.session_id,
                    "metadata": json.dumps(request.metadata) if request.metadata else None
                }
            )
            await session.commit()

        # 发布到 Redis Stream（异步处理）
        try:
            stream = RedisStreamQueue()
            await stream.connect()
            await stream.publish({
                "type": "user_event",
                "user_id": request.user_id,
                "resource_id": request.resource_id,
                "event_type": request.event_type
            })
            await stream.close()
        except Exception:
            # Stream 失败不影响主流程
            pass

        return {"status": "success"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
