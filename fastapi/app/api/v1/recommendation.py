"""推荐系统 API"""
import json
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


# ========== API 端点 ==========

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
