"""Redis Stream 任务队列实现"""
import json
import asyncio
from typing import Callable, Dict, Any, List
from dataclasses import dataclass
from datetime import datetime
import redis.asyncio as redis

from app.core.config import get_settings

settings = get_settings()


@dataclass
class Task:
    """任务对象"""
    id: str
    type: str
    payload: Dict[str, Any]
    created_at: datetime


class RedisStreamQueue:
    """
    Redis Stream 任务队列
    - 支持消费者组
    - 支持 ACK 确认
    - 支持故障恢复（Pending List 重试）
    """
    
    def __init__(
        self,
        redis_client: redis.Redis,
        stream_name: str = None,
        group_name: str = None
    ):
        self.redis = redis_client
        self.stream_name = stream_name or settings.REDIS_STREAM_NAME
        self.group_name = group_name or settings.REDIS_GROUP_NAME
        self.consumer_name = f"consumer-{id(self)}"
    
    async def ensure_group(self):
        """确保消费者组存在"""
        try:
            await self.redis.xgroup_create(
                self.stream_name,
                self.group_name,
                id='0',  # 从开头消费
                mkstream=True
            )
        except redis.ResponseError as e:
            if "already exists" not in str(e).lower():
                raise
    
    async def publish(self, task_type: str, payload: Dict[str, Any]) -> str:
        """发布任务到队列"""
        message = {
            "type": task_type,
            "payload": json.dumps(payload),
            "created_at": datetime.now().isoformat()
        }
        message_id = await self.redis.xadd(self.stream_name, message)
        return message_id
    
    async def consume(
        self,
        handler: Callable[[Task], Any],
        count: int = 10,
        block_ms: int = 5000
    ) -> int:
        """
        消费任务
        
        Args:
            handler: 任务处理函数
            count: 一次最多读取多少条
            block_ms: 阻塞等待时间（毫秒）
            
        Returns:
            处理的任务数量
        """
        # 读取新消息
        messages = await self.redis.xreadgroup(
            groupname=self.group_name,
            consumername=self.consumer_name,
            streams={self.stream_name: '>'},  # '>' 表示读取新消息
            count=count,
            block=block_ms
        )
        
        processed = 0
        
        for stream_name, msgs in messages:
            for msg_id, fields in msgs:
                try:
                    # 解析任务
                    task = Task(
                        id=msg_id,
                        type=fields.get("type", ""),
                        payload=json.loads(fields.get("payload", "{}")),
                        created_at=datetime.fromisoformat(fields.get("created_at", datetime.now().isoformat()))
                    )
                    
                    # 处理任务
                    await handler(task)
                    
                    # 确认完成（ACK）
                    await self.redis.xack(self.stream_name, self.group_name, msg_id)
                    processed += 1
                    
                except Exception as e:
                    # 处理失败，不 ACK，等待重试
                    print(f"Task {msg_id} failed: {e}")
                    # 可以在这里记录失败日志或发送到死信队列
        
        return processed
    
    async def claim_pending(
        self,
        handler: Callable[[Task], Any],
        min_idle_ms: int = 60000,  # 1分钟未ACK则认为超时
        count: int = 10
    ) -> int:
        """
        认领并处理超时任务（故障恢复）
        
        用于处理：
        - Worker 崩溃后未 ACK 的任务
        - 处理超时的任务
        """
        # 查看 Pending List
        pending = await self.redis.xpending_range(
            self.stream_name,
            self.group_name,
            min='-',
            max='+',
            count=count
        )
        
        if not pending:
            return 0
        
        processed = 0
        
        for item in pending:
            msg_id = item["message_id"]
            idle_time = item["time_since_delivered"]
            
            # 只处理超时的任务
            if idle_time < min_idle_ms:
                continue
            
            try:
                # 认领这个任务
                claimed = await self.redis.xclaim(
                    self.stream_name,
                    self.group_name,
                    self.consumer_name,
                    min_idle_time=min_idle_ms,
                    message_ids=[msg_id]
                )
                
                for _, fields in claimed:
                    try:
                        task = Task(
                            id=msg_id,
                            type=fields.get("type", ""),
                            payload=json.loads(fields.get("payload", "{}")),
                            created_at=datetime.fromisoformat(fields.get("created_at", datetime.now().isoformat()))
                        )
                        
                        await handler(task)
                        await self.redis.xack(self.stream_name, self.group_name, msg_id)
                        processed += 1
                        
                    except Exception as e:
                        print(f"Retry task {msg_id} failed: {e}")
            
            except Exception as e:
                print(f"Claim task {msg_id} failed: {e}")
        
        return processed
    
    async def get_stats(self) -> Dict[str, Any]:
        """获取队列统计信息"""
        try:
            info = await self.redis.xinfo_stream(self.stream_name)
            groups = await self.redis.xinfo_groups(self.stream_name)
            
            return {
                "length": info.get("length", 0),
                "consumer_groups": len(groups),
                "last_generated_id": info.get("last-generated-id"),
                "first_entry": str(info.get("first-entry", "")),
                "last_entry": str(info.get("last-entry", "")),
            }
        except redis.ResponseError:
            # Stream 不存在
            return {"length": 0, "consumer_groups": 0}
