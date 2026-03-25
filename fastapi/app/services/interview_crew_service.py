"""Interview Crew Service

封装 Agent Crew 调用，提供简洁的 API 接口。
用于管理 Crew 模式面试的业务逻辑。
"""

import json
import uuid
from datetime import datetime, timezone
from typing import Any, Optional
from dataclasses import dataclass, field

from sqlalchemy import select, insert, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents import (
    InterviewerAgent,
    EvaluatorAgent,
    CoachAgent,
    Task,
    TaskPriority,
)
from app.agents.interview_flow import InterviewFlow, InterviewContext, InterviewType
from app.agents.config import get_scenario, get_agent_config
from app.utils.log_helper import get_logger

logger = get_logger("services.interview_crew")


@dataclass
class CrewSessionConfig:
    """Crew 会话配置"""
    scenario_id: str = "frontend_junior"
    interview_type: InterviewType = InterviewType.CUSTOM
    candidate_level: str = "junior"
    enable_coach: bool = False
    enable_realtime_evaluation: bool = True
    max_duration_minutes: int = 60
    custom_questions: list[str] = field(default_factory=list)


@dataclass
class CrewSessionState:
    """Crew 会话状态"""
    session_id: str
    user_id: int
    status: str = "created"  # created, active, paused, completed, error
    current_stage: str = ""
    progress_percent: float = 0.0
    questions_asked: int = 0
    answers_received: int = 0
    evaluations_count: int = 0
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    metadata: dict[str, Any] = field(default_factory=dict)


class InterviewCrewService:
    """面试 Crew 服务

    封装 Crew 模式面试的核心业务逻辑，提供简洁的 API 接口。

    Example:
        service = InterviewCrewService(db)
        session = await service.create_session(user_id, config)
        question = await service.generate_question(session.session_id)
        result = await service.process_answer(session.session_id, answer)
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self._sessions: dict[str, dict[str, Any]] = {}

    async def create_session(
        self,
        user_id: int,
        config: CrewSessionConfig,
    ) -> CrewSessionState:
        """创建新的 Crew 面试会话

        Args:
            user_id: 用户 ID
            config: 会话配置

        Returns:
            CrewSessionState: 会话状态
        """
        session_id = f"crew_{uuid.uuid4().hex[:12]}"

        # 加载场景配置
        scenario_config = get_scenario(config.scenario_id)
        if scenario_config:
            # 根据场景配置调整
            agents_needed = scenario_config.get("agents", ["interviewer", "evaluator"])
            config.enable_coach = "coach" in agents_needed

        # 初始化 Agent
        interviewer = InterviewerAgent()
        evaluator = EvaluatorAgent()
        coach = CoachAgent() if config.enable_coach else None

        # 初始化流程
        flow = InterviewFlow(
            interview_type=config.interview_type,
            candidate_level=config.candidate_level,
        )

        # 初始化上下文
        interview_context = InterviewContext(
            interview_id=session_id,
            interview_type=config.interview_type,
            candidate_id=str(user_id),
            candidate_level=config.candidate_level,
        )

        # 存储会话
        self._sessions[session_id] = {
            "session_id": session_id,
            "user_id": user_id,
            "config": config,
            "interviewer": interviewer,
            "evaluator": evaluator,
            "coach": coach,
            "flow": flow,
            "interview_context": interview_context,
            "conversation_history": [],
            "evaluations": [],
            "current_question": None,
            "current_answer": None,
            "state": CrewSessionState(session_id=session_id, user_id=user_id),
        }

        logger.info(f"Created Crew session: {session_id} for user: {user_id}")

        return self._sessions[session_id]["state"]

    async def start_session(self, session_id: str) -> CrewSessionState:
        """开始会话

        Args:
            session_id: 会话 ID

        Returns:
            CrewSessionState: 更新后的会话状态
        """
        session = self._get_session(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")

        state = session["state"]
        state.status = "active"
        state.started_at = datetime.now(timezone.utc)

        # 初始化流程
        flow = session["flow"]
        interview_context = session["interview_context"]

        logger.info(f"Started Crew session: {session_id}")

        return state

    async def generate_question(
        self,
        session_id: str,
        context_override: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """生成面试问题

        Args:
            session_id: 会话 ID
            context_override: 可选的上下文覆盖

        Returns:
            dict: 包含问题和元数据
        """
        session = self._get_session(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")

        interviewer = session["interviewer"]
        interview_context = session["interview_context"]
        config = session["config"]

        # 构建上下文
        context = {
            "task_type": "generate_question",
            "scenario": config.scenario_id,
            "candidate_info": {
                "level": config.candidate_level,
                "user_id": session["user_id"],
            },
            "history": session["conversation_history"],
            "current_stage": interview_context.current_stage.value if interview_context else "unknown",
        }

        if context_override:
            context.update(context_override)

        # 创建任务
        task = Task(
            description="生成下一个面试问题",
            expected_output="面试问题和考察点",
            agent_role="interviewer",
            priority=TaskPriority.HIGH,
        )

        # 执行
        result = await interviewer.execute(task, context)

        if result.success:
            question = result.content if isinstance(result.content, str) else str(result.content)
            session["current_question"] = question

            # 更新对话历史
            session["conversation_history"].append({
                "role": "interviewer",
                "content": question,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })

            # 更新状态
            state = session["state"]
            state.questions_asked += 1

            return {
                "success": True,
                "question": question,
                "metadata": result.metadata,
                "agent": "interviewer",
            }
        else:
            return {
                "success": False,
                "error": result.error or "Failed to generate question",
            }

    async def process_answer(
        self,
        session_id: str,
        answer: str,
        answer_type: str = "text",
    ) -> dict[str, Any]:
        """处理候选人回答

        Args:
            session_id: 会话 ID
            answer: 回答内容
            answer_type: 回答类型

        Returns:
            dict: 包含评估结果和追问
        """
        session = self._get_session(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")

        session["current_answer"] = answer

        # 添加到对话历史
        session["conversation_history"].append({
            "role": "candidate",
            "content": answer,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "type": answer_type,
        })

        # 更新状态
        state = session["state"]
        state.answers_received += 1

        # 执行评估
        evaluation = await self._evaluate_answer(session_id, answer)

        # 生成追问
        follow_up = await self._generate_follow_up(session_id, answer)

        return {
            "success": True,
            "evaluation": evaluation,
            "follow_up": follow_up,
        }

    async def _evaluate_answer(
        self,
        session_id: str,
        answer: str,
    ) -> dict[str, Any]:
        """评估回答"""
        session = self._get_session(session_id)
        if not session:
            return {"error": "Session not found"}

        evaluator = session["evaluator"]
        config = session["config"]

        if not config.enable_realtime_evaluation:
            return {"skipped": True, "reason": "Real-time evaluation disabled"}

        context = {
            "task_type": "evaluate_answer",
            "scenario": config.scenario_id,
            "question": session.get("current_question", ""),
            "answer": answer,
            "history": session["conversation_history"],
        }

        task = Task(
            description="评估候选人回答",
            expected_output="JSON 格式的评估结果",
            agent_role="evaluator",
            priority=TaskPriority.NORMAL,
        )

        result = await evaluator.execute(task, context)

        if result.success:
            evaluation = {
                "question": session.get("current_question", ""),
                "answer": answer,
                "evaluation": result.metadata,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            session["evaluations"].append(evaluation)

            # 更新状态
            state = session["state"]
            state.evaluations_count += 1

            return {
                "success": True,
                "scores": result.metadata.get("scores", {}),
                "strengths": result.metadata.get("strengths", []),
                "weaknesses": result.metadata.get("weaknesses", []),
            }
        else:
            return {"success": False, "error": result.error}

    async def _generate_follow_up(
        self,
        session_id: str,
        answer: str,
    ) -> dict[str, Any]:
        """生成追问"""
        session = self._get_session(session_id)
        if not session:
            return {"error": "Session not found"}

        interviewer = session["interviewer"]
        config = session["config"]

        context = {
            "task_type": "follow_up",
            "scenario": config.scenario_id,
            "current_question": session.get("current_question", ""),
            "candidate_answer": answer,
            "history": session["conversation_history"],
        }

        task = Task(
            description="基于回答进行追问",
            expected_output="追问内容",
            agent_role="interviewer",
            priority=TaskPriority.NORMAL,
        )

        result = await interviewer.execute(task, context)

        if result.success:
            return {
                "success": True,
                "follow_up": result.content if isinstance(result.content, str) else str(result.content),
            }
        else:
            return {"success": False, "error": result.error}

    async def generate_coaching(self, session_id: str) -> dict[str, Any]:
        """生成学习建议

        Args:
            session_id: 会话 ID

        Returns:
            dict: 学习建议
        """
        session = self._get_session(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")

        coach = session.get("coach")
        if not coach:
            return {"error": "Coach agent not enabled"}

        if not session["evaluations"]:
            return {"error": "No evaluations available"}

        config = session["config"]

        context = {
            "task_type": "analyze_weaknesses",
            "scenario": config.scenario_id,
            "candidate_info": {
                "level": config.candidate_level,
                "user_id": session["user_id"],
            },
            "evaluation_results": session["evaluations"],
            "answers_summary": self._summarize_answers(session["conversation_history"]),
        }

        task = Task(
            description="分析能力薄弱点并提供学习建议",
            expected_output="学习建议和计划",
            agent_role="coach",
            priority=TaskPriority.LOW,
        )

        result = await coach.execute(task, context)

        if result.success:
            return {
                "success": True,
                "coaching": result.content if isinstance(result.content, str) else str(result.content),
                "agent": "coach",
            }
        else:
            return {"success": False, "error": result.error}

    async def generate_learning_plan(
        self,
        session_id: str,
        target_position: str,
        available_time: str = "每周10小时",
    ) -> dict[str, Any]:
        """生成学习计划

        Args:
            session_id: 会话 ID
            target_position: 目标岗位
            available_time: 可用学习时间

        Returns:
            dict: 学习计划
        """
        session = self._get_session(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")

        coach = session.get("coach")
        if not coach:
            return {"error": "Coach agent not enabled"}

        config = session["config"]

        # 提取薄弱点
        weaknesses = []
        for eval_data in session.get("evaluations", []):
            eval_meta = eval_data.get("evaluation", {})
            weaknesses.extend(eval_meta.get("weaknesses", []))

        context = {
            "task_type": "generate_learning_plan",
            "scenario": config.scenario_id,
            "candidate_info": {
                "level": config.candidate_level,
                "user_id": session["user_id"],
            },
            "weaknesses": weaknesses,
            "target_position": target_position,
            "available_time": available_time,
        }

        task = Task(
            description="生成个性化学习计划",
            expected_output="学习计划",
            agent_role="coach",
            priority=TaskPriority.NORMAL,
        )

        result = await coach.execute(task, context)

        if result.success:
            return {
                "success": True,
                "learning_plan": result.content if isinstance(result.content, str) else str(result.content),
            }
        else:
            return {"success": False, "error": result.error}

    async def end_session(self, session_id: str) -> dict[str, Any]:
        """结束会话

        Args:
            session_id: 会话 ID

        Returns:
            dict: 会话总结
        """
        session = self._get_session(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")

        state = session["state"]
        state.status = "completed"
        state.ended_at = datetime.now(timezone.utc)

        # 生成最终报告
        final_report = await self._generate_final_report(session_id)

        result = {
            "session_id": session_id,
            "status": "completed",
            "duration": self._calculate_duration(session),
            "questions_asked": state.questions_asked,
            "answers_received": state.answers_received,
            "evaluations_count": state.evaluations_count,
            "final_report": final_report,
        }

        # 清理会话
        del self._sessions[session_id]

        logger.info(f"Ended Crew session: {session_id}")

        return result

    async def _generate_final_report(self, session_id: str) -> dict[str, Any]:
        """生成最终评估报告"""
        session = self._get_session(session_id)
        if not session:
            return {"error": "Session not found"}

        evaluator = session["evaluator"]
        config = session["config"]

        if not session["evaluations"]:
            return {"error": "No evaluations available"}

        context = {
            "task_type": "generate_report",
            "scenario": config.scenario_id,
            "interview_duration": self._calculate_duration(session),
            "evaluations": session["evaluations"],
            "history_summary": self._summarize_answers(session["conversation_history"]),
        }

        task = Task(
            description="生成综合评估报告",
            expected_output="JSON 格式的评估报告",
            agent_role="evaluator",
            priority=TaskPriority.HIGH,
        )

        result = await evaluator.execute(task, context)

        if result.success:
            return {
                "success": True,
                "report": result.metadata,
                "content": result.content if isinstance(result.content, str) else str(result.content),
            }
        else:
            return {"success": False, "error": result.error}

    def get_session_state(self, session_id: str) -> Optional[CrewSessionState]:
        """获取会话状态

        Args:
            session_id: 会话 ID

        Returns:
            CrewSessionState: 会话状态，如果不存在返回 None
        """
        session = self._get_session(session_id)
        if session:
            return session["state"]
        return None

    def get_session_progress(self, session_id: str) -> dict[str, Any]:
        """获取会话进度

        Args:
            session_id: 会话 ID

        Returns:
            dict: 进度信息
        """
        session = self._get_session(session_id)
        if not session:
            return {"error": "Session not found"}

        state = session["state"]
        flow = session.get("flow")

        progress = {
            "session_id": session_id,
            "status": state.status,
            "current_stage": state.current_stage,
            "progress_percent": state.progress_percent,
            "questions_asked": state.questions_asked,
            "answers_received": state.answers_received,
            "evaluations_count": state.evaluations_count,
        }

        if flow:
            progress.update(flow.get_progress())

        return progress

    def pause_session(self, session_id: str) -> CrewSessionState:
        """暂停会话

        Args:
            session_id: 会话 ID

        Returns:
            CrewSessionState: 更新后的状态
        """
        session = self._get_session(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")

        state = session["state"]
        state.status = "paused"

        return state

    def resume_session(self, session_id: str) -> CrewSessionState:
        """恢复会话

        Args:
            session_id: 会话 ID

        Returns:
            CrewSessionState: 更新后的状态
        """
        session = self._get_session(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")

        state = session["state"]
        if state.status == "paused":
            state.status = "active"

        return state

    def _get_session(self, session_id: str) -> Optional[dict[str, Any]]:
        """获取会话数据"""
        return self._sessions.get(session_id)

    def _summarize_answers(self, conversation_history: list[dict]) -> str:
        """总结回答历史"""
        summaries = []
        for item in conversation_history:
            if item.get("role") == "candidate":
                content = item.get("content", "")[:100]
                summaries.append(content)
        return " | ".join(summaries) if summaries else "无回答"

    def _calculate_duration(self, session: dict[str, Any]) -> str:
        """计算会话时长"""
        state = session["state"]
        if not state.started_at:
            return "0分钟"

        end_time = state.ended_at or datetime.now(timezone.utc)
        duration = (end_time - state.started_at).total_seconds()

        minutes = int(duration // 60)
        seconds = int(duration % 60)

        if minutes > 0:
            return f"{minutes}分{seconds}秒"
        return f"{seconds}秒"

    def list_active_sessions(self) -> list[CrewSessionState]:
        """列出所有活动会话

        Returns:
            list[CrewSessionState]: 活动会话列表
        """
        return [
            session["state"]
            for session in self._sessions.values()
            if session["state"].status in ["active", "paused"]
        ]

    async def get_available_scenarios(self) -> list[dict[str, Any]]:
        """获取可用场景列表

        Returns:
            list: 场景列表
        """
        from app.agents.config import get_all_scenarios

        scenarios = get_all_scenarios()
        return [
            {
                "id": key,
                "name": value.get("name", key),
                "description": value.get("description", ""),
                "target_level": value.get("target_level", "any"),
                "agents": value.get("agents", []),
            }
            for key, value in scenarios.items()
        ]
