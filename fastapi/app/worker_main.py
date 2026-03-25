"""Worker 服务入口"""
import asyncio
from datetime import datetime

from app.core import get_redis, close_redis, RedisStreamQueue, Task


async def handle_user_event(task: Task):
    """处理用户事件"""
    payload = task.payload
    user_id = payload.get("user_id")
    event_type = payload.get("event_type")
    
    print(f"[{datetime.now()}] 处理事件: {event_type}, 用户: {user_id}")
    
    # TODO: 实现具体的事件处理逻辑
    # 1. 更新用户实时特征
    # 2. 更新资源热度
    # 3. 记录到数据库


async def handle_feature_update(task: Task):
    """处理特征更新"""
    print(f"[{datetime.now()}] 更新特征")
    # TODO: 实现特征更新逻辑


async def handle_model_training(task: Task):
    """处理模型训练"""
    print(f"[{datetime.now()}] 开始模型训练")
    # TODO: 实现模型训练逻辑


# 任务处理器映射
TASK_HANDLERS = {
    "user_event": handle_user_event,
    "feature_update": handle_feature_update,
    "model_training": handle_model_training,
}


async def process_task(task: Task):
    """分发任务到对应处理器"""
    handler = TASK_HANDLERS.get(task.type)
    if handler:
        await handler(task)
    else:
        print(f"未知任务类型: {task.type}")


async def worker_main():
    """Worker 主循环"""
    print(f"[{datetime.now()}] Worker 启动")
    
    # 初始化 Redis
    redis = await get_redis()
    
    # 创建队列
    queue = RedisStreamQueue(redis)
    await queue.ensure_group()
    
    print(f"[{datetime.now()}] 开始消费队列: {queue.stream_name}")
    
    while True:
        try:
            # 1. 处理新消息
            processed = await queue.consume(
                handler=process_task,
                count=10,
                block_ms=5000
            )
            
            if processed > 0:
                print(f"处理完成: {processed} 条消息")
            
            # 2. 处理超时任务（故障恢复）
            if processed == 0:
                claimed = await queue.claim_pending(
                    handler=process_task,
                    min_idle_ms=60000,
                    count=5
                )
                if claimed > 0:
                    print(f"认领并处理: {claimed} 条超时消息")
        
        except Exception as e:
            print(f"Worker 错误: {e}")
            await asyncio.sleep(5)


if __name__ == "__main__":
    try:
        asyncio.run(worker_main())
    except KeyboardInterrupt:
        print("\nWorker 停止")
        # 清理
        asyncio.run(close_redis())
