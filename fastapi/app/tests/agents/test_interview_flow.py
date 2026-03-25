"""Interview Flow 模块测试"""

import pytest

from app.agents.interview_flow import (
    InterviewFlow,
    InterviewContext,
    InterviewStage,
    InterviewType,
    AdaptiveInterviewFlow,
)
from app.agents.flow import FlowStatus


class TestInterviewStage:
    """测试 InterviewStage 枚举"""

    def test_stage_values(self):
        """测试阶段值"""
        assert InterviewStage.SELF_INTRO.value == "self_intro"
        assert InterviewStage.TECHNICAL.value == "technical"
        assert InterviewStage.BEHAVIORAL.value == "behavioral"
        assert InterviewStage.SYSTEM_DESIGN.value == "system_design"
        assert InterviewStage.CODING.value == "coding"
        assert InterviewStage.Q_AND_A.value == "q_and_a"
        assert InterviewStage.WRAP_UP.value == "wrap_up"


class TestInterviewType:
    """测试 InterviewType 枚举"""

    def test_type_values(self):
        """测试类型值"""
        assert InterviewType.FRONTEND_JUNIOR.value == "frontend_junior"
        assert InterviewType.BACKEND_SENIOR.value == "backend_senior"
        assert InterviewType.FULLSTACK.value == "fullstack"
        assert InterviewType.ALGORITHM.value == "algorithm"


class TestInterviewContext:
    """测试 InterviewContext 类"""

    def test_context_creation(self):
        """测试创建上下文"""
        context = InterviewContext(interview_id="int_001")

        assert context.interview_id == "int_001"
        assert context.interview_type == InterviewType.CUSTOM
        assert context.candidate_level == "junior"
        assert context.current_stage == InterviewStage.SELF_INTRO
        assert context.stages_completed == []
        assert context.conversation_history == []
        assert context.evaluations == []

    def test_context_to_dict(self):
        """测试转换为字典"""
        context = InterviewContext(
            interview_id="int_001",
            interview_type=InterviewType.FRONTEND_JUNIOR,
        )

        data = context.to_dict()

        assert data["interview_id"] == "int_001"
        assert data["interview_type"] == "frontend_junior"
        assert data["candidate_level"] == "junior"

    def test_advance_stage(self):
        """测试推进阶段"""
        context = InterviewContext(interview_id="int_001")
        context.stages_remaining = [
            InterviewStage.TECHNICAL,
            InterviewStage.Q_AND_A,
        ]

        next_stage = context.advance_stage()

        assert next_stage == InterviewStage.TECHNICAL
        assert context.current_stage == InterviewStage.TECHNICAL
        assert InterviewStage.TECHNICAL in context.stages_completed
        assert InterviewStage.TECHNICAL not in context.stages_remaining

    def test_advance_stage_empty(self):
        """测试推进阶段（无剩余阶段）"""
        context = InterviewContext(interview_id="int_001")
        context.stages_remaining = []

        next_stage = context.advance_stage()

        assert next_stage is None

    def test_add_message(self):
        """测试添加消息"""
        context = InterviewContext(interview_id="int_001")

        context.add_message("interviewer", "Hello")

        assert len(context.conversation_history) == 1
        assert context.conversation_history[0]["role"] == "interviewer"
        assert context.conversation_history[0]["content"] == "Hello"
        assert "timestamp" in context.conversation_history[0]

    def test_add_evaluation(self):
        """测试添加评估"""
        context = InterviewContext(interview_id="int_001")

        context.add_evaluation(
            InterviewStage.TECHNICAL,
            {"score": 4.5, "comment": "Good"},
        )

        assert len(context.evaluations) == 1
        assert context.evaluations[0]["stage"] == "technical"
        assert context.evaluations[0]["evaluation"]["score"] == 4.5

    def test_end_interview(self):
        """测试结束面试"""
        context = InterviewContext(interview_id="int_001")

        context.end_interview()

        assert context.ended_at is not None
        assert context.current_stage == InterviewStage.WRAP_UP


class TestInterviewFlow:
    """测试 InterviewFlow 类"""

    def test_flow_creation(self):
        """测试创建流程"""
        flow = InterviewFlow(
            interview_type=InterviewType.FRONTEND_JUNIOR,
            candidate_level="junior",
        )

        assert flow.interview_type == InterviewType.FRONTEND_JUNIOR
        assert flow.candidate_level == "junior"
        assert flow.name == "InterviewFlow_frontend_junior"

    def test_get_stages_default(self):
        """测试获取默认阶段"""
        flow = InterviewFlow()
        stages = flow._get_stages()

        assert len(stages) >= 4
        assert InterviewStage.SELF_INTRO in stages
        assert InterviewStage.TECHNICAL in stages
        assert InterviewStage.WRAP_UP in stages

    def test_get_stages_frontend_junior(self):
        """测试获取前端初级阶段"""
        flow = InterviewFlow(interview_type=InterviewType.FRONTEND_JUNIOR)
        stages = flow._get_stages()

        assert InterviewStage.SELF_INTRO in stages
        assert InterviewStage.TECHNICAL in stages
        assert InterviewStage.CODING in stages
        assert InterviewStage.WRAP_UP in stages

    def test_get_stages_backend_senior(self):
        """测试获取后端高级阶段"""
        flow = InterviewFlow(interview_type=InterviewType.BACKEND_SENIOR)
        stages = flow._get_stages()

        assert InterviewStage.SELF_INTRO in stages
        assert InterviewStage.TECHNICAL in stages
        assert InterviewStage.SYSTEM_DESIGN in stages
        assert InterviewStage.CODING in stages
        assert InterviewStage.BEHAVIORAL in stages

    @pytest.mark.asyncio
    async def test_flow_initialization(self):
        """测试流程初始化"""
        flow = InterviewFlow(interview_type=InterviewType.FRONTEND_JUNIOR)

        result = await flow.initialize(flow._create_context())

        assert result["status"] == "initialized"
        assert result["interview_type"] == "frontend_junior"
        assert "stages" in result

    def test_flow_get_progress_not_started(self):
        """测试获取未开始流程的进度"""
        flow = InterviewFlow()
        progress = flow.get_progress()

        assert progress["status"] == "not_started"

    def _create_context(self):
        """辅助方法：创建上下文"""
        from app.agents.flow import FlowContext
        return FlowContext()


class TestAdaptiveInterviewFlow:
    """测试 AdaptiveInterviewFlow 类"""

    def test_adaptive_flow_creation(self):
        """测试创建自适应流程"""
        flow = AdaptiveInterviewFlow(
            interview_type=InterviewType.BACKEND_SENIOR,
            candidate_level="senior",
        )

        assert flow.interview_type == InterviewType.BACKEND_SENIOR
        assert flow.candidate_level == "senior"
        assert flow._adaptive_enabled is True
        assert flow._performance_scores == []

    def test_record_performance(self):
        """测试记录表现"""
        flow = AdaptiveInterviewFlow()

        flow.record_performance(4.5)
        flow.record_performance(3.5)

        assert flow._performance_scores == [4.5, 3.5]

    def test_should_adjust_difficulty_increase(self):
        """测试应该提高难度"""
        flow = AdaptiveInterviewFlow()

        flow.record_performance(4.8)
        flow.record_performance(4.9)
        flow.record_performance(4.7)

        should_adjust, direction = flow.should_adjust_difficulty()

        assert should_adjust is True
        assert direction == "increase"

    def test_should_adjust_difficulty_decrease(self):
        """测试应该降低难度"""
        flow = AdaptiveInterviewFlow()

        flow.record_performance(1.5)
        flow.record_performance(1.8)
        flow.record_performance(1.2)

        should_adjust, direction = flow.should_adjust_difficulty()

        assert should_adjust is True
        assert direction == "decrease"

    def test_should_not_adjust_difficulty(self):
        """测试不应该调整难度"""
        flow = AdaptiveInterviewFlow()

        flow.record_performance(3.5)
        flow.record_performance(3.0)

        should_adjust, direction = flow.should_adjust_difficulty()

        assert should_adjust is False
        assert direction == ""

    def test_get_recommended_next_topic_advanced(self):
        """测试推荐高级主题"""
        flow = AdaptiveInterviewFlow()

        flow.record_performance(4.5)
        flow.record_performance(4.0)

        topic = flow.get_recommended_next_topic()

        assert topic == "advanced"

    def test_get_recommended_next_topic_fundamentals(self):
        """测试推荐基础主题"""
        flow = AdaptiveInterviewFlow()

        flow.record_performance(2.0)
        flow.record_performance(1.5)

        topic = flow.get_recommended_next_topic()

        assert topic == "fundamentals"

    def test_get_recommended_next_topic_default(self):
        """测试默认推荐主题"""
        flow = AdaptiveInterviewFlow()

        topic = flow.get_recommended_next_topic()

        assert topic == "fundamentals"


class TestInterviewFlowConfigs:
    """测试 InterviewFlow 配置"""

    def test_frontend_junior_config(self):
        """测试前端初级配置"""
        stages = InterviewFlow.FLOW_CONFIGS[InterviewType.FRONTEND_JUNIOR]

        assert InterviewStage.SELF_INTRO in stages
        assert InterviewStage.TECHNICAL in stages
        assert InterviewStage.CODING in stages
        assert InterviewStage.WRAP_UP in stages

    def test_backend_senior_config(self):
        """测试后端高级配置"""
        stages = InterviewFlow.FLOW_CONFIGS[InterviewType.BACKEND_SENIOR]

        assert InterviewStage.SELF_INTRO in stages
        assert InterviewStage.TECHNICAL in stages
        assert InterviewStage.SYSTEM_DESIGN in stages
        assert InterviewStage.BEHAVIORAL in stages
        assert InterviewStage.WRAP_UP in stages

    def test_fullstack_config(self):
        """测试全栈配置"""
        stages = InterviewFlow.FLOW_CONFIGS[InterviewType.FULLSTACK]

        assert InterviewStage.SELF_INTRO in stages
        assert InterviewStage.TECHNICAL in stages
        assert InterviewStage.SYSTEM_DESIGN in stages
        assert InterviewStage.PRACTICAL in stages
