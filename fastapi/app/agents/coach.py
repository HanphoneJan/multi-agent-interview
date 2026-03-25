"""Coach Agent

学习顾问 Agent 实现，负责分析薄弱点、生成学习计划和推荐资源。
"""

import json
from typing import Any

from app.agents.base import BaseAgent, AgentOutput, LLMConfig
from app.agents.task import Task
from app.agents.prompts.coach import (
    COACH_SYSTEM_PROMPT,
    COACH_TASK_TEMPLATES,
)
from app.services.qwen3_omni_http_service import Qwen3OmniHTTPService
from app.utils.log_helper import get_logger

logger = get_logger("agents.coach")


class CoachAgent(BaseAgent):
    """学习顾问 Agent

    职责：
    - 分析候选人薄弱点
    - 生成个性化学习建议
    - 推荐学习资源

    Example:
        agent = CoachAgent()
        result = await agent.execute(task, context)
        learning_plan = result.content
    """

    # 默认角色配置
    DEFAULT_ROLE = "技术学习顾问"
    DEFAULT_GOAL = "帮助候选人识别能力薄弱点，制定个性化学习计划，推荐合适的学习资源"
    DEFAULT_BACKSTORY = """你是一位经验丰富的技术学习顾问和职业发展导师，曾在多家知名科技公司负责技术培训和人才培养。
你擅长分析技术人员的能力短板，能够根据个人情况制定切实可行的学习计划。
你熟悉各种技术学习资源，能够为不同水平的学员推荐最合适的学习材料。"""

    def __init__(
        self,
        role: str | None = None,
        goal: str | None = None,
        backstory: str | None = None,
        llm_config: LLMConfig | None = None,
        agent_id: str | None = None,
    ):
        super().__init__(
            role=role or self.DEFAULT_ROLE,
            goal=goal or self.DEFAULT_GOAL,
            backstory=backstory or self.DEFAULT_BACKSTORY,
            llm_config=llm_config,
            agent_id=agent_id,
        )
        self.llm_service = Qwen3OmniHTTPService()
        self._recommendation_history: list[dict[str, Any]] = []

    async def execute(self, task: Task, context: dict[str, Any]) -> AgentOutput:
        """执行任务

        Args:
            task: 要执行的任务
            context: 执行上下文

        Returns:
            AgentOutput: 执行结果
        """
        await self._before_execute(task, context)

        try:
            # 根据任务类型选择处理方法
            task_type = context.get("task_type", "analyze_weaknesses")

            if task_type == "analyze_weaknesses":
                result = await self._analyze_weaknesses(task, context)
            elif task_type == "generate_learning_plan":
                result = await self._generate_learning_plan(task, context)
            elif task_type == "recommend_resources":
                result = await self._recommend_resources(task, context)
            elif task_type == "career_guidance":
                result = await self._career_guidance(task, context)
            else:
                result = await self._default_execute(task, context)

            await self._after_execute(task, result, context)
            return result

        except Exception as e:
            await self._on_error(task, e, context)
            return AgentOutput(
                content="",
                success=False,
                error=str(e),
                agent_id=self.agent_id,
            )

    def _build_messages(
        self, task: Task, context: dict[str, Any]
    ) -> list[dict[str, str]]:
        """构建 LLM 消息列表

        Args:
            task: 任务定义
            context: 执行上下文

        Returns:
            list[dict[str, str]]: 消息列表
        """
        # 构建系统 Prompt
        system_prompt = COACH_SYSTEM_PROMPT.format(
            role=self.role,
            goal=self.goal,
            backstory=self.backstory,
        )

        # 构建任务 Prompt
        task_type = context.get("task_type", "analyze_weaknesses")
        template = COACH_TASK_TEMPLATES.get(
            task_type, COACH_TASK_TEMPLATES["analyze_weaknesses"]
        )

        # 格式化模板
        template_vars = {
            "scenario": context.get("scenario", "技术面试"),
            "candidate_info": json.dumps(context.get("candidate_info", {}), ensure_ascii=False),
            "evaluation_results": json.dumps(context.get("evaluation_results", {}), ensure_ascii=False),
            "answers_summary": context.get("answers_summary", ""),
            "weaknesses": json.dumps(context.get("weaknesses", []), ensure_ascii=False),
            "target_position": context.get("target_position", ""),
            "available_time": context.get("available_time", "每周10小时"),
            "improvement_areas": json.dumps(context.get("improvement_areas", []), ensure_ascii=False),
            "current_level": context.get("current_level", "初级"),
            "learning_preferences": json.dumps(context.get("learning_preferences", []), ensure_ascii=False),
            "career_goals": context.get("career_goals", ""),
        }

        task_prompt = template.format(**template_vars)

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": task_prompt},
        ]

        return messages

    async def _analyze_weaknesses(
        self, task: Task, context: dict[str, Any]
    ) -> AgentOutput:
        """分析能力薄弱点

        Args:
            task: 任务定义
            context: 执行上下文

        Returns:
            AgentOutput: 薄弱点分析
        """
        messages = self._build_messages(task, context)

        response_chunks = []
        async for chunk in self.llm_service.chat(
            messages=messages,
            stream=False,
        ):
            if chunk.type == "text" and chunk.content:
                response_chunks.append(chunk.content)

        content = "".join(response_chunks)

        # 存储推荐历史
        self._recommendation_history.append({
            "task_type": "analyze_weaknesses",
            "content": content,
        })

        return AgentOutput(
            content=content,
            metadata={"task_type": "analyze_weaknesses"},
            success=True,
            agent_id=self.agent_id,
        )

    async def _generate_learning_plan(
        self, task: Task, context: dict[str, Any]
    ) -> AgentOutput:
        """生成个性化学习计划

        Args:
            task: 任务定义
            context: 执行上下文

        Returns:
            AgentOutput: 学习计划
        """
        messages = self._build_messages(task, context)

        response_chunks = []
        async for chunk in self.llm_service.chat(
            messages=messages,
            stream=False,
        ):
            if chunk.type == "text" and chunk.content:
                response_chunks.append(chunk.content)

        content = "".join(response_chunks)

        # 存储推荐历史
        self._recommendation_history.append({
            "task_type": "generate_learning_plan",
            "content": content,
        })

        return AgentOutput(
            content=content,
            metadata={"task_type": "generate_learning_plan"},
            success=True,
            agent_id=self.agent_id,
        )

    async def _recommend_resources(
        self, task: Task, context: dict[str, Any]
    ) -> AgentOutput:
        """推荐学习资源

        Args:
            task: 任务定义
            context: 执行上下文

        Returns:
            AgentOutput: 资源推荐
        """
        messages = self._build_messages(task, context)

        response_chunks = []
        async for chunk in self.llm_service.chat(
            messages=messages,
            stream=False,
        ):
            if chunk.type == "text" and chunk.content:
                response_chunks.append(chunk.content)

        content = "".join(response_chunks)

        # 存储推荐历史
        self._recommendation_history.append({
            "task_type": "recommend_resources",
            "content": content,
        })

        return AgentOutput(
            content=content,
            metadata={"task_type": "recommend_resources"},
            success=True,
            agent_id=self.agent_id,
        )

    async def _career_guidance(
        self, task: Task, context: dict[str, Any]
    ) -> AgentOutput:
        """职业发展指导

        Args:
            task: 任务定义
            context: 执行上下文

        Returns:
            AgentOutput: 职业指导
        """
        messages = self._build_messages(task, context)

        response_chunks = []
        async for chunk in self.llm_service.chat(
            messages=messages,
            stream=False,
        ):
            if chunk.type == "text" and chunk.content:
                response_chunks.append(chunk.content)

        content = "".join(response_chunks)

        # 存储推荐历史
        self._recommendation_history.append({
            "task_type": "career_guidance",
            "content": content,
        })

        return AgentOutput(
            content=content,
            metadata={"task_type": "career_guidance"},
            success=True,
            agent_id=self.agent_id,
        )

    async def _default_execute(
        self, task: Task, context: dict[str, Any]
    ) -> AgentOutput:
        """默认执行方法

        Args:
            task: 任务定义
            context: 执行上下文

        Returns:
            AgentOutput: 执行结果
        """
        messages = self._build_messages(task, context)

        response_chunks = []
        async for chunk in self.llm_service.chat(
            messages=messages,
            stream=False,
        ):
            if chunk.type == "text" and chunk.content:
                response_chunks.append(chunk.content)

        content = "".join(response_chunks)

        return AgentOutput(
            content=content,
            success=True,
            agent_id=self.agent_id,
        )

    def get_recommendation_history(self) -> list[dict[str, Any]]:
        """获取推荐历史

        Returns:
            list[dict[str, Any]]: 推荐历史
        """
        return self._recommendation_history.copy()

    def clear_history(self) -> None:
        """清空推荐历史"""
        self._recommendation_history.clear()
