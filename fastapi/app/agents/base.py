"""Agent 基类框架

提供所有 Agent 的基础抽象类和通用功能。
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, AsyncIterator
from enum import Enum
import uuid
from datetime import datetime

from app.agents.task import Task
from app.utils.log_helper import get_logger

logger = get_logger("agents.base")


class AgentStatus(Enum):
    """Agent 状态枚举"""
    IDLE = "idle"
    BUSY = "busy"
    ERROR = "error"


@dataclass
class AgentOutput:
    """Agent 输出结果

    Attributes:
        content: 主要内容（文本或结构化数据）
        metadata: 元数据（如 token 使用量、耗时等）
        success: 是否成功
        error: 错误信息（如果失败）
        agent_id: Agent 实例 ID
        timestamp: 生成时间
    """
    content: str | dict[str, Any]
    metadata: dict[str, Any] = field(default_factory=dict)
    success: bool = True
    error: str | None = None
    agent_id: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self):
        if not self.agent_id:
            self.agent_id = str(uuid.uuid4())[:8]


@dataclass
class LLMConfig:
    """LLM 配置

    Attributes:
        model: 模型名称
        temperature: 温度参数
        max_tokens: 最大 token 数
        top_p: 核采样参数
        api_key: API 密钥（可选，默认从环境变量读取）
        base_url: API 基础 URL（可选）
    """
    model: str = "qwen-plus"
    temperature: float = 0.7
    max_tokens: int = 2048
    top_p: float = 0.9
    api_key: str | None = None
    base_url: str | None = None


class BaseAgent(ABC):
    """Agent 基类

    所有具体 Agent（面试官、评估员、学习顾问）的抽象基类。
    遵循 CrewAI 模式，每个 Agent 有明确的角色、目标和背景设定。

    Attributes:
        role: Agent 角色名称
        goal: Agent 目标描述
        backstory: Agent 背景故事（影响其行为风格）
        llm_config: LLM 配置
        agent_id: Agent 唯一标识
        status: 当前状态
    """

    def __init__(
        self,
        role: str,
        goal: str,
        backstory: str,
        llm_config: LLMConfig | None = None,
        agent_id: str | None = None,
    ):
        self.role = role
        self.goal = goal
        self.backstory = backstory
        self.llm_config = llm_config or LLMConfig()
        self.agent_id = agent_id or str(uuid.uuid4())[:8]
        self.status = AgentStatus.IDLE
        self._execution_count = 0

        logger.info(
            f"Agent initialized: {self.role} (id={self.agent_id})"
        )

    @abstractmethod
    async def execute(self, task: Task, context: dict[str, Any]) -> AgentOutput:
        """执行任务的抽象方法

        Args:
            task: 要执行的任务
            context: 执行上下文（包含面试状态、历史记录等）

        Returns:
            AgentOutput: 执行结果
        """
        raise NotImplementedError

    async def execute_stream(
        self, task: Task, context: dict[str, Any]
    ) -> AsyncIterator[str]:
        """流式执行任务（可选实现）

        默认实现为非流式，子类可重写以支持流式输出。

        Args:
            task: 要执行的任务
            context: 执行上下文

        Yields:
            str: 流式输出的文本片段
        """
        result = await self.execute(task, context)
        if isinstance(result.content, str):
            yield result.content
        else:
            yield str(result.content)

    def build_system_prompt(self) -> str:
        """构建系统 Prompt

        基于角色、目标和背景故事构建系统级 Prompt。

        Returns:
            str: 系统 Prompt
        """
        return f"""你是一位专业的 {self.role}。

你的目标：{self.goal}

你的背景：{self.backstory}

请始终以专业、友好的态度完成任务。你的回答应当：
1. 准确且有条理
2. 符合你的角色定位
3. 有助于达成既定目标
"""

    def build_task_prompt(self, task: Task, context: dict[str, Any]) -> str:
        """构建任务 Prompt

        Args:
            task: 任务定义
            context: 执行上下文

        Returns:
            str: 完整的任务 Prompt
        """
        context_str = self._format_context(context)

        return f"""## 任务描述

{task.description}

## 期望输出

{task.expected_output}

## 上下文信息

{context_str}

## 要求

请基于以上信息，以 {self.role} 的身份完成任务。
"""

    def _format_context(self, context: dict[str, Any]) -> str:
        """格式化上下文信息

        Args:
            context: 上下文字典

        Returns:
            str: 格式化后的字符串
        """
        if not context:
            return "暂无上下文信息"

        lines = []
        for key, value in context.items():
            if isinstance(value, (list, dict)):
                import json
                value_str = json.dumps(value, ensure_ascii=False, indent=2)
                lines.append(f"- {key}:\n{value_str}")
            else:
                lines.append(f"- {key}: {value}")

        return "\n".join(lines) if lines else "暂无上下文信息"

    def get_status(self) -> AgentStatus:
        """获取 Agent 当前状态"""
        return self.status

    def is_available(self) -> bool:
        """检查 Agent 是否可用"""
        return self.status == AgentStatus.IDLE

    def get_stats(self) -> dict[str, Any]:
        """获取 Agent 统计信息"""
        return {
            "agent_id": self.agent_id,
            "role": self.role,
            "status": self.status.value,
            "execution_count": self._execution_count,
            "llm_model": self.llm_config.model,
        }

    async def _before_execute(self, task: Task, context: dict[str, Any]) -> None:
        """执行前钩子（可重写）"""
        self.status = AgentStatus.BUSY
        self._execution_count += 1
        logger.info(
            f"Agent {self.role} (id={self.agent_id}) starting task: {task.task_id}"
        )

    async def _after_execute(
        self, task: Task, result: AgentOutput, context: dict[str, Any]
    ) -> None:
        """执行后钩子（可重写）"""
        self.status = AgentStatus.IDLE if result.success else AgentStatus.ERROR
        logger.info(
            f"Agent {self.role} (id={self.agent_id}) completed task: {task.task_id}, "
            f"success={result.success}"
        )

    async def _on_error(self, task: Task, error: Exception, context: dict[str, Any]) -> None:
        """错误处理钩子（可重写）"""
        self.status = AgentStatus.ERROR
        logger.error(
            f"Agent {self.role} (id={self.agent_id}) error in task {task.task_id}: {error}"
        )
