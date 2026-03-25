"""Task 模块测试"""

import pytest
from datetime import datetime

from app.agents.task import Task, TaskStatus, TaskPriority, TaskResult


class TestTask:
    """测试 Task 类"""

    def test_task_creation(self):
        """测试创建 Task"""
        task = Task(
            description="Test task",
            expected_output="Test output",
            agent_role="interviewer",
        )

        assert task.description == "Test task"
        assert task.expected_output == "Test output"
        assert task.agent_role == "interviewer"
        assert task.status == TaskStatus.PENDING
        assert task.priority == TaskPriority.NORMAL
        assert task.task_id
        assert isinstance(task.created_at, datetime)

    def test_task_auto_id(self):
        """测试自动生成的 task_id"""
        task = Task(description="Test", expected_output="Test", agent_role="test")
        assert task.task_id.startswith("task_")
        assert len(task.task_id) == 13  # task_ + 8 chars

    def test_task_status_transitions(self):
        """测试任务状态转换"""
        task = Task(description="Test", expected_output="Test", agent_role="test")

        assert task.is_pending() is True
        assert task.is_running() is False
        assert task.is_completed() is False

        task.mark_running()
        assert task.status == TaskStatus.RUNNING
        assert task.is_running() is True
        assert task.started_at is not None

        task.mark_completed("result")
        assert task.status == TaskStatus.COMPLETED
        assert task.is_completed() is True
        assert task.result == "result"
        assert task.completed_at is not None

    def test_task_mark_failed(self):
        """测试标记任务失败"""
        task = Task(description="Test", expected_output="Test", agent_role="test")

        task.mark_failed("Error occurred")

        assert task.status == TaskStatus.FAILED
        assert task.is_failed() is True
        assert task.error == "Error occurred"
        assert task.completed_at is not None

    def test_task_mark_cancelled(self):
        """测试标记任务取消"""
        task = Task(description="Test", expected_output="Test", agent_role="test")

        task.mark_cancelled()

        assert task.status == TaskStatus.CANCELLED
        assert task.completed_at is not None

    def test_task_get_duration(self):
        """测试获取任务时长"""
        task = Task(description="Test", expected_output="Test", agent_role="test")

        # 未开始时返回 None
        assert task.get_duration() is None

        # 开始后返回时长
        task.mark_running()
        import time
        time.sleep(0.01)  # 等待一小段时间
        duration = task.get_duration()
        assert duration is not None
        assert duration > 0

    def test_task_to_dict(self):
        """测试转换为字典"""
        task = Task(
            description="Test task",
            expected_output="Output",
            agent_role="test",
            priority=TaskPriority.HIGH,
        )

        task.mark_running()
        task.mark_completed("result")

        data = task.to_dict()

        assert data["task_id"] == task.task_id
        assert data["description"] == "Test task"
        assert data["status"] == "completed"
        assert data["priority"] == "HIGH"
        assert data["result"] == "result"
        assert "duration" in data


class TestTaskPriority:
    """测试 TaskPriority 枚举"""

    def test_priority_values(self):
        """测试优先级值"""
        assert TaskPriority.LOW.value == 1
        assert TaskPriority.NORMAL.value == 2
        assert TaskPriority.HIGH.value == 3
        assert TaskPriority.CRITICAL.value == 4

    def test_priority_comparison(self):
        """测试优先级比较"""
        assert TaskPriority.CRITICAL.value > TaskPriority.HIGH.value
        assert TaskPriority.HIGH.value > TaskPriority.NORMAL.value
        assert TaskPriority.NORMAL.value > TaskPriority.LOW.value


class TestTaskResult:
    """测试 TaskResult 类"""

    def test_task_result_creation(self):
        """测试创建 TaskResult"""
        result = TaskResult(
            task_id="task_123",
            output="Test output",
            success=True,
            metadata={"key": "value"},
        )

        assert result.task_id == "task_123"
        assert result.output == "Test output"
        assert result.success is True
        assert result.metadata == {"key": "value"}
        assert isinstance(result.timestamp, datetime)

    def test_task_result_default_values(self):
        """测试默认值"""
        result = TaskResult(task_id="task_123", output="Test")

        assert result.success is True
        assert result.metadata == {}
        assert isinstance(result.timestamp, datetime)

    def test_task_result_to_dict(self):
        """测试转换为字典"""
        result = TaskResult(
            task_id="task_123",
            output={"key": "value"},
            success=True,
            metadata={"meta": "data"},
        )

        data = result.to_dict()

        assert data["task_id"] == "task_123"
        assert data["output"] == {"key": "value"}
        assert data["success"] is True
        assert data["metadata"] == {"meta": "data"}
        assert "timestamp" in data
