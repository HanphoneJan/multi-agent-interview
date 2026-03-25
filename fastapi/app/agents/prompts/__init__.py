"""Agent Prompts Module

包含所有 Agent 的系统 Prompt 和任务 Prompt 模板。
"""

from app.agents.prompts.interviewer import INTERVIEWER_SYSTEM_PROMPT, INTERVIEWER_TASK_TEMPLATES
from app.agents.prompts.evaluator import EVALUATOR_SYSTEM_PROMPT, EVALUATOR_TASK_TEMPLATES
from app.agents.prompts.coach import COACH_SYSTEM_PROMPT, COACH_TASK_TEMPLATES

__all__ = [
    "INTERVIEWER_SYSTEM_PROMPT",
    "INTERVIEWER_TASK_TEMPLATES",
    "EVALUATOR_SYSTEM_PROMPT",
    "EVALUATOR_TASK_TEMPLATES",
    "COACH_SYSTEM_PROMPT",
    "COACH_TASK_TEMPLATES",
]
