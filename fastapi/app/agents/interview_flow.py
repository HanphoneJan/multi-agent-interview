"""Interview Flow - 面试流程编排

基于 Flow 基类实现的面试专用流程控制器。
支持多种面试场景的流程编排，包括技术面试、行为面试等。
"""

from typing import Any
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

from app.agents.flow import Flow, FlowContext, start, listen, router, task
from app.agents.base import AgentOutput
from app.utils.log_helper import get_logger

logger = get_logger("agents.interview_flow")


class InterviewStage(Enum):
    """面试阶段枚举"""
    SELF_INTRO = "self_intro"               # 自我介绍
    TECHNICAL = "technical"                  # 技术面试
    BEHAVIORAL = "behavioral"                # 行为面试
    SYSTEM_DESIGN = "system_design"          # 系统设计
    CODING = "coding"                        # 编程测试
    PRACTICAL = "practical"                  # 实战问题
    Q_AND_A = "q_and_a"                      # 问答环节
    WRAP_UP = "wrap_up"                      # 结束面试


class InterviewType(Enum):
    """面试类型枚举"""
    FRONTEND_JUNIOR = "frontend_junior"      # 前端初级
    FRONTEND_SENIOR = "frontend_senior"      # 前端高级
    BACKEND_JUNIOR = "backend_junior"        # 后端初级
    BACKEND_SENIOR = "backend_senior"        # 后端高级
    FULLSTACK = "fullstack"                  # 全栈
    ALGORITHM = "algorithm"                  # 算法
    BEHAVIORAL = "behavioral"                # 行为面试
    CUSTOM = "custom"                        # 自定义


@dataclass
class InterviewContext:
    """面试上下文

    包含面试过程中的所有状态和数据。

    Attributes:
        interview_id: 面试会话 ID
        interview_type: 面试类型
        candidate_id: 候选人 ID
        candidate_level: 候选人级别 (junior/mid/senior/expert)
        current_stage: 当前阶段
        stages_completed: 已完成的阶段
        stages_remaining: 剩余阶段
        conversation_history: 对话历史
        evaluations: 评估结果
        metadata: 元数据
    """
    interview_id: str
    interview_type: InterviewType = InterviewType.CUSTOM
    candidate_id: str = ""
    candidate_level: str = "junior"
    current_stage: InterviewStage = InterviewStage.SELF_INTRO
    stages_completed: list[InterviewStage] = field(default_factory=list)
    stages_remaining: list[InterviewStage] = field(default_factory=list)
    conversation_history: list[dict[str, Any]] = field(default_factory=list)
    evaluations: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    started_at: datetime = field(default_factory=datetime.utcnow)
    ended_at: datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "interview_id": self.interview_id,
            "interview_type": self.interview_type.value,
            "candidate_id": self.candidate_id,
            "candidate_level": self.candidate_level,
            "current_stage": self.current_stage.value,
            "stages_completed": [s.value for s in self.stages_completed],
            "stages_remaining": [s.value for s in self.stages_remaining],
            "conversation_history": self.conversation_history,
            "evaluations": self.evaluations,
            "metadata": self.metadata,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "ended_at": self.ended_at.isoformat() if self.ended_at else None,
        }

    def advance_stage(self) -> InterviewStage | None:
        """推进到下一阶段"""
        if self.stages_remaining:
            self.current_stage = self.stages_remaining.pop(0)
            self.stages_completed.append(self.current_stage)
            return self.current_stage
        return None

    def add_message(self, role: str, content: str, metadata: dict[str, Any] | None = None) -> None:
        """添加对话消息"""
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": metadata or {},
        }
        self.conversation_history.append(message)

    def add_evaluation(self, stage: InterviewStage, evaluation: dict[str, Any]) -> None:
        """添加评估结果"""
        self.evaluations.append({
            "stage": stage.value,
            "evaluation": evaluation,
            "timestamp": datetime.utcnow().isoformat(),
        })

    def end_interview(self) -> None:
        """结束面试"""
        self.ended_at = datetime.utcnow()
        self.current_stage = InterviewStage.WRAP_UP


class InterviewFlow(Flow):
    """面试流程控制器

    编排完整的面试流程，包括开场、技术面试、行为面试、结束等环节。
    支持根据候选人表现动态调整流程。

    Example:
        flow = InterviewFlow(
            interview_type=InterviewType.BACKEND_SENIOR,
            candidate_level="senior"
        )
        context = InterviewContext(interview_id="int_001")
        await flow.execute(context)
    """

    # 预定义的面试流程配置
    FLOW_CONFIGS: dict[InterviewType, list[InterviewStage]] = {
        InterviewType.FRONTEND_JUNIOR: [
            InterviewStage.SELF_INTRO,
            InterviewStage.TECHNICAL,
            InterviewStage.CODING,
            InterviewStage.Q_AND_A,
            InterviewStage.WRAP_UP,
        ],
        InterviewType.FRONTEND_SENIOR: [
            InterviewStage.SELF_INTRO,
            InterviewStage.TECHNICAL,
            InterviewStage.SYSTEM_DESIGN,
            InterviewStage.CODING,
            InterviewStage.BEHAVIORAL,
            InterviewStage.Q_AND_A,
            InterviewStage.WRAP_UP,
        ],
        InterviewType.BACKEND_JUNIOR: [
            InterviewStage.SELF_INTRO,
            InterviewStage.TECHNICAL,
            InterviewStage.CODING,
            InterviewStage.Q_AND_A,
            InterviewStage.WRAP_UP,
        ],
        InterviewType.BACKEND_SENIOR: [
            InterviewStage.SELF_INTRO,
            InterviewStage.TECHNICAL,
            InterviewStage.SYSTEM_DESIGN,
            InterviewStage.CODING,
            InterviewStage.BEHAVIORAL,
            InterviewStage.Q_AND_A,
            InterviewStage.WRAP_UP,
        ],
        InterviewType.FULLSTACK: [
            InterviewStage.SELF_INTRO,
            InterviewStage.TECHNICAL,
            InterviewStage.SYSTEM_DESIGN,
            InterviewStage.CODING,
            InterviewStage.PRACTICAL,
            InterviewStage.Q_AND_A,
            InterviewStage.WRAP_UP,
        ],
        InterviewType.ALGORITHM: [
            InterviewStage.SELF_INTRO,
            InterviewStage.CODING,
            InterviewStage.Q_AND_A,
            InterviewStage.WRAP_UP,
        ],
        InterviewType.BEHAVIORAL: [
            InterviewStage.SELF_INTRO,
            InterviewStage.BEHAVIORAL,
            InterviewStage.Q_AND_A,
            InterviewStage.WRAP_UP,
        ],
    }

    def __init__(
        self,
        interview_type: InterviewType = InterviewType.CUSTOM,
        candidate_level: str = "junior",
        custom_stages: list[InterviewStage] | None = None,
    ):
        self.interview_type = interview_type
        self.candidate_level = candidate_level
        self.custom_stages = custom_stages
        self._interview_context: InterviewContext | None = None
        super().__init__(name=f"InterviewFlow_{interview_type.value}")

    def _get_stages(self) -> list[InterviewStage]:
        """获取面试阶段列表"""
        if self.custom_stages:
            return self.custom_stages
        return self.FLOW_CONFIGS.get(
            self.interview_type,
            [
                InterviewStage.SELF_INTRO,
                InterviewStage.TECHNICAL,
                InterviewStage.Q_AND_A,
                InterviewStage.WRAP_UP,
            ]
        )

    @start()
    async def initialize(self, context: FlowContext) -> dict[str, Any]:
        """初始化面试流程

        设置面试上下文，确定面试阶段序列。
        """
        stages = self._get_stages()

        # 从上下文中获取或创建 InterviewContext
        if "interview_context" in context.data:
            self._interview_context = context.data["interview_context"]
        else:
            interview_id = context.data.get("interview_id", "unknown")
            self._interview_context = InterviewContext(
                interview_id=interview_id,
                interview_type=self.interview_type,
                candidate_level=self.candidate_level,
                stages_remaining=stages[1:] if len(stages) > 1 else [],
            )
            context.data["interview_context"] = self._interview_context

        logger.info(
            f"Interview flow initialized: type={self.interview_type.value}, "
            f"stages={[s.value for s in stages]}"
        )

        return {
            "status": "initialized",
            "interview_type": self.interview_type.value,
            "stages": [s.value for s in stages],
            "candidate_level": self.candidate_level,
        }

    @listen(initialize)
    async def self_introduction(self, prev_result: dict[str, Any], context: FlowContext) -> dict[str, Any]:
        """自我介绍阶段

        面试官开场白，候选人自我介绍。
        """
        if self._interview_context:
            self._interview_context.current_stage = InterviewStage.SELF_INTRO

        logger.info("Executing stage: self_introduction")

        return {
            "stage": "self_introduction",
            "action": "generate_question",
            "question_type": "self_intro",
            "instruction": "请候选人进行自我介绍，了解其背景和经历",
        }

    @listen(self_introduction)
    async def technical_round(self, prev_result: dict[str, Any], context: FlowContext) -> dict[str, Any]:
        """技术面试阶段

        根据面试类型和候选人级别进行技术问题提问。
        """
        if self._interview_context:
            self._interview_context.current_stage = InterviewStage.TECHNICAL
            self._interview_context.advance_stage()

        logger.info("Executing stage: technical_round")

        # 根据级别调整技术难度
        difficulty = {
            "junior": "基础",
            "mid": "中等",
            "senior": "深入",
            "expert": "专家级",
        }.get(self.candidate_level, "中等")

        return {
            "stage": "technical_round",
            "action": "generate_question",
            "question_type": "technical",
            "difficulty": difficulty,
            "instruction": f"进行{difficulty}难度的技术面试",
        }

    @listen(technical_round)
    async def system_design_or_coding(self, prev_result: dict[str, Any], context: FlowContext) -> dict[str, Any]:
        """系统设计或编程测试阶段

        根据面试类型决定是进行系统设计还是编程测试。
        """
        stages = self._get_stages()

        if InterviewStage.SYSTEM_DESIGN in stages and self.candidate_level in ["senior", "expert"]:
            if self._interview_context:
                self._interview_context.current_stage = InterviewStage.SYSTEM_DESIGN

            logger.info("Executing stage: system_design")

            return {
                "stage": "system_design",
                "action": "generate_question",
                "question_type": "system_design",
                "instruction": "进行系统设计面试，考察架构设计能力",
            }

        elif InterviewStage.CODING in stages:
            if self._interview_context:
                self._interview_context.current_stage = InterviewStage.CODING

            logger.info("Executing stage: coding")

            return {
                "stage": "coding",
                "action": "generate_question",
                "question_type": "coding",
                "instruction": "进行编程测试，考察编码能力",
            }

        return {
            "stage": "skip",
            "reason": "Not applicable for this interview type or candidate level",
        }

    @router(system_design_or_coding)
    async def adaptive_next(self, prev_result: dict[str, Any], context: FlowContext) -> str:
        """自适应下一步

        根据候选人表现决定下一步流程。
        """
        stages = self._get_stages()

        # 如果刚完成系统设计，检查是否需要编程测试
        if prev_result.get("stage") == "system_design" and InterviewStage.CODING in stages:
            return "coding_round"

        # 如果刚完成编程测试，检查是否需要行为面试
        if prev_result.get("stage") == "coding" and InterviewStage.BEHAVIORAL in stages:
            return "behavioral_round"

        # 否则进入问答环节
        return "q_and_a"

    @task()
    async def coding_round(self, context: FlowContext) -> dict[str, Any]:
        """编程测试阶段"""
        if self._interview_context:
            self._interview_context.current_stage = InterviewStage.CODING

        logger.info("Executing stage: coding_round")

        return {
            "stage": "coding",
            "action": "generate_question",
            "question_type": "coding",
            "instruction": "进行编程测试",
        }

    @task()
    async def behavioral_round(self, context: FlowContext) -> dict[str, Any]:
        """行为面试阶段"""
        if self._interview_context:
            self._interview_context.current_stage = InterviewStage.BEHAVIORAL

        logger.info("Executing stage: behavioral_round")

        return {
            "stage": "behavioral",
            "action": "generate_question",
            "question_type": "behavioral",
            "instruction": "进行行为面试，了解候选人的软技能和团队协作能力",
        }

    @listen(adaptive_next)
    async def q_and_a(self, prev_result: dict[str, Any], context: FlowContext) -> dict[str, Any]:
        """问答环节

        候选人提问，面试官解答。
        """
        if self._interview_context:
            self._interview_context.current_stage = InterviewStage.Q_AND_A

        logger.info("Executing stage: q_and_a")

        return {
            "stage": "q_and_a",
            "action": "invite_questions",
            "instruction": "邀请候选人提问",
        }

    @listen(q_and_a)
    async def wrap_up(self, prev_result: dict[str, Any], context: FlowContext) -> dict[str, Any]:
        """结束面试

        总结面试，说明后续流程。
        """
        if self._interview_context:
            self._interview_context.end_interview()

        logger.info("Executing stage: wrap_up")

        return {
            "stage": "wrap_up",
            "action": "end_interview",
            "instruction": "结束面试，说明后续流程",
        }

    def get_interview_context(self) -> InterviewContext | None:
        """获取面试上下文"""
        return self._interview_context

    def get_progress(self) -> dict[str, Any]:
        """获取面试进度"""
        if not self._interview_context:
            return {"status": "not_started"}

        total_stages = len(self._get_stages())
        completed = len(self._interview_context.stages_completed)

        return {
            "status": self.get_status().value,
            "current_stage": self._interview_context.current_stage.value,
            "completed_stages": [s.value for s in self._interview_context.stages_completed],
            "remaining_stages": [s.value for s in self._interview_context.stages_remaining],
            "progress_percent": (completed / total_stages * 100) if total_stages > 0 else 0,
            "interview_id": self._interview_context.interview_id,
        }


class AdaptiveInterviewFlow(InterviewFlow):
    """自适应面试流程

    根据候选人的实时表现动态调整面试难度和方向。
    """

    def __init__(
        self,
        interview_type: InterviewType = InterviewType.CUSTOM,
        candidate_level: str = "junior",
    ):
        super().__init__(interview_type, candidate_level)
        self._performance_scores: list[float] = []
        self._adaptive_enabled = True

    def record_performance(self, score: float) -> None:
        """记录候选人表现分数"""
        self._performance_scores.append(score)

    def should_adjust_difficulty(self) -> tuple[bool, str]:
        """判断是否需要调整难度

        Returns:
            (是否需要调整, 调整方向)
        """
        if len(self._performance_scores) < 2:
            return False, ""

        recent_scores = self._performance_scores[-3:]
        avg_score = sum(recent_scores) / len(recent_scores)

        if avg_score >= 4.5:
            return True, "increase"  # 提高难度
        elif avg_score <= 2.0:
            return True, "decrease"  # 降低难度

        return False, ""

    def get_recommended_next_topic(self) -> str:
        """获取推荐的下一个主题"""
        if not self._performance_scores:
            return "fundamentals"

        avg_score = sum(self._performance_scores) / len(self._performance_scores)

        if avg_score >= 4.0:
            return "advanced"
        elif avg_score >= 3.0:
            return "intermediate"
        else:
            return "fundamentals"
