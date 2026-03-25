"""AI Interview Agent System - CrewAI Mode

多 Agent 协作系统，引入 CrewAI 的角色化、任务编排和流程控制模式。
"""

from app.agents.base import BaseAgent, AgentOutput, LLMConfig, AgentStatus
from app.agents.task import Task, TaskStatus, TaskPriority, TaskResult
from app.agents.flow import Flow, FlowStep, StepType, FlowContext, start, listen, router, parallel, task
from app.agents.interviewer import InterviewerAgent
from app.agents.evaluator import EvaluatorAgent
from app.agents.coach import CoachAgent

__all__ = [
    # Base classes
    "BaseAgent",
    "AgentOutput",
    "LLMConfig",
    "AgentStatus",
    # Task classes
    "Task",
    "TaskStatus",
    "TaskPriority",
    "TaskResult",
    # Flow classes
    "Flow",
    "FlowStep",
    "StepType",
    "FlowContext",
    "start",
    "listen",
    "router",
    "parallel",
    "task",
    # Agent implementations
    "InterviewerAgent",
    "EvaluatorAgent",
    "CoachAgent",
]
