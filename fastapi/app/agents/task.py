"""任务定义模块

定义 Agent 执行的任务结构和状态管理。
"""
from dataclasses import dataclass, field
from typing import Any
from enum import Enum
import uuid
from datetime import datetime


class TaskStatus(Enum):
    """任务状态枚举"""
    PENDING = "pending"      # 等待执行
    RUNNING = "running"      # 执行中
    COMPLETED = "completed"  # 已完成
    FAILED = "failed"        # 执行失败
    CANCELLED = "cancelled"  # 已取消


class TaskPriority(Enum):
    """任务优先级枚举"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class Task:
    """任务定义

    表示一个需要 Agent 执行的具体任务。

    Attributes:
        description: 任务描述
        expected_output: 期望输出格式/内容
        agent_role: 执行该任务的 Agent 角色
        task_id: 任务唯一标识
        status: 当前状态
        priority: 优先级
        context: 任务相关的上下文数据
        created_at: 创建时间
        started_at: 开始执行时间
        completed_at: 完成时间
        result: 执行结果
        error: 错误信息
    """
    description: str
    expected_output: str
    agent_role: str
    task_id: str = ""
    status: TaskStatus = TaskStatus.PENDING
    priority: TaskPriority = TaskPriority.NORMAL
    context: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    result: Any = None
    error: str | None = None

    def __post_init__(self):
        if not self.task_id:
            self.task_id = f"task_{str(uuid.uuid4())[:8]}"

    def mark_running(self) -> None:
        """标记任务为执行中"""
        self.status = TaskStatus.RUNNING
        self.started_at = datetime.utcnow()

    def mark_completed(self, result: Any) -> None:
        """标记任务为已完成"""
        self.status = TaskStatus.COMPLETED
        self.completed_at = datetime.utcnow()
        self.result = result

    def mark_failed(self, error: str) -> None:
        """标记任务为失败"""
        self.status = TaskStatus.FAILED
        self.completed_at = datetime.utcnow()
        self.error = error

    def mark_cancelled(self) -> None:
        """标记任务为已取消"""
        self.status = TaskStatus.CANCELLED
        self.completed_at = datetime.utcnow()

    def is_pending(self) -> bool:
        """检查任务是否待执行"""
        return self.status == TaskStatus.PENDING

    def is_running(self) -> bool:
        """检查任务是否执行中"""
        return self.status == TaskStatus.RUNNING

    def is_completed(self) -> bool:
        """检查任务是否已完成"""
        return self.status == TaskStatus.COMPLETED

    def is_failed(self) -> bool:
        """检查任务是否失败"""
        return self.status == TaskStatus.FAILED

    def get_duration(self) -> float | None:
        """获取任务执行时长（秒）

        Returns:
            执行时长，如果任务未开始则返回 None
        """
        if self.started_at is None:
            return None

        end_time = self.completed_at or datetime.utcnow()
        return (end_time - self.started_at).total_seconds()

    def to_dict(self) -> dict[str, Any]:
        """转换为字典表示"""
        return {
            "task_id": self.task_id,
            "description": self.description,
            "expected_output": self.expected_output,
            "agent_role": self.agent_role,
            "status": self.status.value,
            "priority": self.priority.name,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration": self.get_duration(),
            "result": self.result,
            "error": self.error,
        }


@dataclass
class TaskResult:
    """任务执行结果

    用于在 Agent 之间传递任务执行结果。

    Attributes:
        task_id: 关联的任务 ID
        output: 输出内容
        success: 是否成功
        metadata: 元数据
        timestamp: 生成时间
    """
    task_id: str
    output: str | dict[str, Any]
    success: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典表示"""
        return {
            "task_id": self.task_id,
            "output": self.output,
            "success": self.success,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
        }
