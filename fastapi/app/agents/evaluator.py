"""Evaluator Agent

评估员 Agent 实现，负责实时评估候选人回答和生成评估报告。
"""

import json
import re
from typing import Any

from app.agents.base import BaseAgent, AgentOutput, LLMConfig
from app.agents.task import Task
from app.agents.prompts.evaluator import (
    EVALUATOR_SYSTEM_PROMPT,
    EVALUATOR_TASK_TEMPLATES,
)
from app.services.qwen3_omni_http_service import Qwen3OmniHTTPService
from app.utils.log_helper import get_logger

logger = get_logger("agents.evaluator")


class EvaluatorAgent(BaseAgent):
    """评估员 Agent

    职责：
    - 实时评估候选人回答
    - 多维度打分（技术、表达、逻辑等）
    - 生成详细评估报告

    Example:
        agent = EvaluatorAgent()
        result = await agent.execute(task, context)
        scores = result.metadata.get("scores", {})
    """

    # 默认角色配置
    DEFAULT_ROLE = "面试评估员"
    DEFAULT_GOAL = "客观、公正地评估候选人的面试表现，提供多维度评分和详细反馈"
    DEFAULT_BACKSTORY = """你是一位资深的技术人才评估专家，拥有丰富的人力资源和技术面试评估经验。
你擅长从多个维度全面评估候选人，包括技术能力、沟通表达、逻辑思维等方面。
你的评估客观公正，能够为招聘决策提供有价值的参考意见。"""

    # 评估维度
    EVALUATION_DIMENSIONS = [
        "professional_knowledge",
        "skill_match",
        "language_expression",
        "logical_thinking",
        "stress_response",
        "personality",
        "motivation",
        "value",
    ]

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
        self._evaluation_history: list[dict[str, Any]] = []

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
            task_type = context.get("task_type", "evaluate_answer")

            if task_type == "evaluate_answer":
                result = await self._evaluate_answer(task, context)
            elif task_type == "evaluate_technical":
                result = await self._evaluate_technical(task, context)
            elif task_type == "generate_report":
                result = await self._generate_report(task, context)
            elif task_type == "real_time_feedback":
                result = await self._real_time_feedback(task, context)
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
        system_prompt = EVALUATOR_SYSTEM_PROMPT.format(
            role=self.role,
            goal=self.goal,
            backstory=self.backstory,
        )

        # 构建任务 Prompt
        task_type = context.get("task_type", "evaluate_answer")
        template = EVALUATOR_TASK_TEMPLATES.get(
            task_type, EVALUATOR_TASK_TEMPLATES["evaluate_answer"]
        )

        # 格式化模板
        template_vars = {
            "scenario": context.get("scenario", "技术面试"),
            "candidate_info": json.dumps(context.get("candidate_info", {}), ensure_ascii=False),
            "question": context.get("question", ""),
            "answer": context.get("answer", ""),
            "history": json.dumps(context.get("history", []), ensure_ascii=False),
            "technical_question": context.get("technical_question", ""),
            "expected_points": json.dumps(context.get("expected_points", []), ensure_ascii=False),
            "interview_duration": context.get("interview_duration", "30分钟"),
            "evaluations": json.dumps(context.get("evaluations", []), ensure_ascii=False),
            "history_summary": context.get("history_summary", ""),
            "current_round": context.get("current_round", 1),
            "latest_answer": context.get("latest_answer", ""),
            "evaluation_history": json.dumps(context.get("evaluation_history", []), ensure_ascii=False),
        }

        task_prompt = template.format(**template_vars)

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": task_prompt},
        ]

        return messages

    def _extract_json_from_response(self, content: str) -> dict[str, Any]:
        """从 LLM 响应中提取 JSON

        Args:
            content: LLM 响应内容

        Returns:
            dict[str, Any]: 解析后的 JSON 数据
        """
        # 尝试直接解析
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            pass

        # 尝试从 Markdown 代码块中提取
        json_pattern = r"```(?:json)?\s*([\s\S]*?)```"
        matches = re.findall(json_pattern, content)

        for match in matches:
            try:
                return json.loads(match.strip())
            except json.JSONDecodeError:
                continue

        # 尝试查找 JSON 对象
        json_pattern = r"\{[\s\S]*\}"
        matches = re.findall(json_pattern, content)

        for match in matches:
            try:
                return json.loads(match.strip())
            except json.JSONDecodeError:
                continue

        # 如果都无法解析，返回空字典
        logger.warning(f"Failed to extract JSON from response: {content[:200]}...")
        return {}

    async def _evaluate_answer(
        self, task: Task, context: dict[str, Any]
    ) -> AgentOutput:
        """评估候选人回答

        Args:
            task: 任务定义
            context: 执行上下文

        Returns:
            AgentOutput: 评估结果
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

        # 提取 JSON 数据
        evaluation_data = self._extract_json_from_response(content)

        # 存储评估历史
        self._evaluation_history.append({
            "question": context.get("question", ""),
            "answer": context.get("answer", ""),
            "evaluation": evaluation_data,
        })

        return AgentOutput(
            content=content,
            metadata={
                "task_type": "evaluate_answer",
                "scores": evaluation_data.get("scores", {}),
                "strengths": evaluation_data.get("strengths", []),
                "weaknesses": evaluation_data.get("weaknesses", []),
            },
            success=True,
            agent_id=self.agent_id,
        )

    async def _evaluate_technical(
        self, task: Task, context: dict[str, Any]
    ) -> AgentOutput:
        """技术能力专项评估

        Args:
            task: 任务定义
            context: 执行上下文

        Returns:
            AgentOutput: 技术评估结果
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

        # 提取 JSON 数据
        evaluation_data = self._extract_json_from_response(content)

        return AgentOutput(
            content=content,
            metadata={
                "task_type": "evaluate_technical",
                "technical_score": evaluation_data.get("technical_score", 0),
                "detailed_feedback": evaluation_data.get("detailed_feedback", ""),
            },
            success=True,
            agent_id=self.agent_id,
        )

    async def _generate_report(
        self, task: Task, context: dict[str, Any]
    ) -> AgentOutput:
        """生成综合评估报告

        Args:
            task: 任务定义
            context: 执行上下文

        Returns:
            AgentOutput: 综合评估报告
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

        # 提取 JSON 数据
        report_data = self._extract_json_from_response(content)

        return AgentOutput(
            content=content,
            metadata={
                "task_type": "generate_report",
                "overall_score": report_data.get("overall_score", 0),
                "recommendation": report_data.get("recommendation", {}),
                "position_match": report_data.get("position_match", {}),
            },
            success=True,
            agent_id=self.agent_id,
        )

    async def _real_time_feedback(
        self, task: Task, context: dict[str, Any]
    ) -> AgentOutput:
        """实时评估反馈

        Args:
            task: 任务定义
            context: 执行上下文

        Returns:
            AgentOutput: 实时反馈
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

        # 提取 JSON 数据
        feedback_data = self._extract_json_from_response(content)

        return AgentOutput(
            content=content,
            metadata={
                "task_type": "real_time_feedback",
                "quick_score": feedback_data.get("quick_score", 0),
                "follow_up_suggestions": feedback_data.get("follow_up_suggestions", []),
                "next_direction": feedback_data.get("next_direction", ""),
            },
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

    def get_evaluation_history(self) -> list[dict[str, Any]]:
        """获取评估历史

        Returns:
            list[dict[str, Any]]: 评估历史
        """
        return self._evaluation_history.copy()

    def clear_history(self) -> None:
        """清空评估历史"""
        self._evaluation_history.clear()

    def calculate_average_scores(self) -> dict[str, float]:
        """计算各维度的平均分数

        Returns:
            dict[str, float]: 平均分数
        """
        if not self._evaluation_history:
            return {}

        dimension_totals: dict[str, list[float]] = {
            dim: [] for dim in self.EVALUATION_DIMENSIONS
        }

        for record in self._evaluation_history:
            evaluation = record.get("evaluation", {})
            scores = evaluation.get("scores", {})

            for dim in self.EVALUATION_DIMENSIONS:
                dim_data = scores.get(dim, {})
                if isinstance(dim_data, dict):
                    score = dim_data.get("score", 0)
                else:
                    score = dim_data

                if score:
                    dimension_totals[dim].append(float(score))

        averages = {}
        for dim, scores in dimension_totals.items():
            if scores:
                averages[dim] = sum(scores) / len(scores)
            else:
                averages[dim] = 0.0

        return averages
