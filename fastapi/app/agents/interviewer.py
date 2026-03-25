"""Interviewer Agent

面试官 Agent 实现，负责生成面试问题、追问和控制面试节奏。
"""

import json
from typing import Any, AsyncIterator

from app.agents.base import BaseAgent, AgentOutput, LLMConfig
from app.agents.task import Task
from app.agents.prompts.interviewer import (
    INTERVIEWER_SYSTEM_PROMPT,
    INTERVIEWER_TASK_TEMPLATES,
)
from app.services.qwen3_omni_http_service import Qwen3OmniHTTPService
from app.utils.log_helper import get_logger

logger = get_logger("agents.interviewer")


class InterviewerAgent(BaseAgent):
    """面试官 Agent

    职责：
    - 根据场景生成面试问题
    - 基于候选人回答进行追问
    - 控制面试节奏

    Example:
        agent = InterviewerAgent()
        result = await agent.execute(task, context)
    """

    # 默认角色配置
    DEFAULT_ROLE = "技术面试官"
    DEFAULT_GOAL = "通过专业的技术面试，全面评估候选人的技术能力和综合素质"
    DEFAULT_BACKSTORY = """你是一位拥有10年以上经验的技术面试官，曾在多家知名科技公司担任技术负责人。
你擅长通过深入的对话了解候选人的技术深度和广度，能够营造轻松的面试氛围，
让候选人充分展示自己的能力。你注重考察候选人的思维方式、解决问题的能力和学习潜力。"""

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
        self._conversation_history: list[dict[str, Any]] = []

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
            task_type = context.get("task_type", "generate_question")

            if task_type == "generate_question":
                result = await self._generate_question(task, context)
            elif task_type == "follow_up":
                result = await self._follow_up(task, context)
            elif task_type == "control_pace":
                result = await self._control_pace(task, context)
            elif task_type == "wrap_up":
                result = await self._wrap_up(task, context)
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

    async def execute_stream(
        self, task: Task, context: dict[str, Any]
    ) -> AsyncIterator[str]:
        """流式执行任务

        Args:
            task: 要执行的任务
            context: 执行上下文

        Yields:
            str: 流式输出的文本片段
        """
        await self._before_execute(task, context)

        try:
            messages = self._build_messages(task, context)

            async for chunk in self.llm_service.chat(
                messages=messages,
                stream=True,
            ):
                if chunk.type == "text" and chunk.content:
                    yield chunk.content

            self.status = self.__class__.__base__.__bases__[0].IDLE  # type: ignore

        except Exception as e:
            await self._on_error(task, e, context)
            yield f"[错误: {str(e)}]"

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
        system_prompt = INTERVIEWER_SYSTEM_PROMPT.format(
            role=self.role,
            goal=self.goal,
            backstory=self.backstory,
        )

        # 构建任务 Prompt
        task_type = context.get("task_type", "generate_question")
        template = INTERVIEWER_TASK_TEMPLATES.get(
            task_type, INTERVIEWER_TASK_TEMPLATES["generate_question"]
        )
        task_prompt = template.format(
            scenario=context.get("scenario", "技术面试"),
            candidate_info=json.dumps(context.get("candidate_info", {}), ensure_ascii=False),
            history=json.dumps(context.get("history", []), ensure_ascii=False),
            current_stage=context.get("current_stage", "技术面试"),
            current_question=context.get("current_question", ""),
            candidate_answer=context.get("candidate_answer", ""),
            elapsed_time=context.get("elapsed_time", "0分钟"),
            completed_stages=json.dumps(context.get("completed_stages", []), ensure_ascii=False),
            remaining_stages=json.dumps(context.get("remaining_stages", []), ensure_ascii=False),
            history_summary=context.get("history_summary", ""),
            interview_duration=context.get("interview_duration", "30分钟"),
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": task_prompt},
        ]

        return messages

    async def _generate_question(
        self, task: Task, context: dict[str, Any]
    ) -> AgentOutput:
        """生成面试问题

        Args:
            task: 任务定义
            context: 执行上下文

        Returns:
            AgentOutput: 生成的面试问题
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

        # 更新对话历史
        self._update_history("interviewer", content)

        return AgentOutput(
            content=content,
            metadata={"task_type": "generate_question"},
            success=True,
            agent_id=self.agent_id,
        )

    async def _follow_up(self, task: Task, context: dict[str, Any]) -> AgentOutput:
        """基于回答进行追问

        Args:
            task: 任务定义
            context: 执行上下文

        Returns:
            AgentOutput: 追问内容
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

        # 更新对话历史
        self._update_history("interviewer", content)

        return AgentOutput(
            content=content,
            metadata={"task_type": "follow_up"},
            success=True,
            agent_id=self.agent_id,
        )

    async def _control_pace(self, task: Task, context: dict[str, Any]) -> AgentOutput:
        """控制面试节奏

        Args:
            task: 任务定义
            context: 执行上下文

        Returns:
            AgentOutput: 节奏控制建议
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
            metadata={"task_type": "control_pace"},
            success=True,
            agent_id=self.agent_id,
        )

    async def _wrap_up(self, task: Task, context: dict[str, Any]) -> AgentOutput:
        """结束面试

        Args:
            task: 任务定义
            context: 执行上下文

        Returns:
            AgentOutput: 结束语
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
            metadata={"task_type": "wrap_up"},
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

    def _update_history(self, role: str, content: str) -> None:
        """更新对话历史

        Args:
            role: 角色（interviewer/candidate）
            content: 内容
        """
        self._conversation_history.append({
            "role": role,
            "content": content,
        })

        # 限制历史长度，保留最近20轮
        if len(self._conversation_history) > 40:
            self._conversation_history = self._conversation_history[-40:]

    def get_conversation_history(self) -> list[dict[str, Any]]:
        """获取对话历史

        Returns:
            list[dict[str, Any]]: 对话历史
        """
        return self._conversation_history.copy()

    def clear_history(self) -> None:
        """清空对话历史"""
        self._conversation_history.clear()
