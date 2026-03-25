"""Interview Crew 集成测试

测试 Crew 模式面试的完整流程，包括：
- 会话创建和管理
- Agent 协作
- WebSocket 通信
- 评估报告生成
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timezone

from app.services.interview_crew_service import (
    InterviewCrewService,
    CrewSessionConfig,
    CrewSessionState,
)
from app.agents.interview_flow import InterviewType, InterviewStage
from app.agents import Task


@pytest.fixture
def mock_db():
    """模拟数据库会话"""
    return AsyncMock()


@pytest.fixture
def crew_service(mock_db):
    """创建 Crew 服务实例"""
    return InterviewCrewService(mock_db)


@pytest.fixture
def basic_config():
    """基础配置"""
    return CrewSessionConfig(
        scenario_id="frontend_junior",
        interview_type=InterviewType.FRONTEND_JUNIOR,
        candidate_level="junior",
        enable_coach=False,
    )


class TestCrewSessionLifecycle:
    """测试 Crew 会话生命周期"""

    @pytest.mark.asyncio
    async def test_create_and_start_session(self, crew_service, basic_config):
        """测试创建并启动会话"""
        # 创建会话
        state = await crew_service.create_session(
            user_id=1,
            config=basic_config,
        )

        assert state.session_id.startswith("crew_")
        assert state.status == "created"
        assert state.user_id == 1

        # 启动会话
        started_state = await crew_service.start_session(state.session_id)

        assert started_state.status == "active"
        assert started_state.started_at is not None

    @pytest.mark.asyncio
    async def test_session_not_found(self, crew_service):
        """测试会话不存在的情况"""
        with pytest.raises(ValueError, match="Session not found"):
            await crew_service.start_session("nonexistent_session")

    @pytest.mark.asyncio
    async def test_pause_and_resume_session(self, crew_service, basic_config):
        """测试暂停和恢复会话"""
        # 创建并启动会话
        state = await crew_service.create_session(user_id=1, config=basic_config)
        await crew_service.start_session(state.session_id)

        # 暂停
        paused_state = crew_service.pause_session(state.session_id)
        assert paused_state.status == "paused"

        # 恢复
        resumed_state = crew_service.resume_session(state.session_id)
        assert resumed_state.status == "active"

    @pytest.mark.asyncio
    async def test_end_session(self, crew_service, basic_config):
        """测试结束会话"""
        # 创建会话
        state = await crew_service.create_session(user_id=1, config=basic_config)

        # 结束会话
        result = await crew_service.end_session(state.session_id)

        assert result["status"] == "completed"
        assert result["session_id"] == state.session_id
        assert "duration" in result


class TestCrewQuestionGeneration:
    """测试问题生成"""

    @pytest.mark.asyncio
    async def test_generate_question(self, crew_service, basic_config):
        """测试生成问题"""
        # 创建会话
        state = await crew_service.create_session(user_id=1, config=basic_config)

        # Mock interviewer agent
        mock_result = Mock()
        mock_result.success = True
        mock_result.content = "What is HTML5?"
        mock_result.metadata = {"task_type": "generate_question"}

        with patch.object(
            crew_service._sessions[state.session_id]["interviewer"],
            "execute",
            return_value=mock_result,
        ):
            result = await crew_service.generate_question(state.session_id)

        assert result["success"] is True
        assert result["question"] == "What is HTML5?"
        assert result["agent"] == "interviewer"

    @pytest.mark.asyncio
    async def test_generate_question_session_not_found(self, crew_service):
        """测试生成问题时会话不存在"""
        with pytest.raises(ValueError, match="Session not found"):
            await crew_service.generate_question("nonexistent")


class TestCrewAnswerProcessing:
    """测试回答处理"""

    @pytest.mark.asyncio
    async def test_process_answer(self, crew_service, basic_config):
        """测试处理回答"""
        # 创建会话
        state = await crew_service.create_session(user_id=1, config=basic_config)

        # Mock evaluator agent
        mock_eval_result = Mock()
        mock_eval_result.success = True
        mock_eval_result.metadata = {
            "scores": {"technical": 4.5},
            "strengths": ["Clear explanation"],
            "weaknesses": [],
        }

        # Mock interviewer agent for follow-up
        mock_follow_result = Mock()
        mock_follow_result.success = True
        mock_follow_result.content = "Can you explain more?"

        session_data = crew_service._sessions[state.session_id]

        with patch.object(
            session_data["evaluator"],
            "execute",
            return_value=mock_eval_result,
        ), patch.object(
            session_data["interviewer"],
            "execute",
            return_value=mock_follow_result,
        ):
            result = await crew_service.process_answer(
                session_id=state.session_id,
                answer="HTML5 is the latest version of HTML.",
            )

        assert result["success"] is True
        assert "evaluation" in result
        assert "follow_up" in result

    @pytest.mark.asyncio
    async def test_process_answer_updates_history(self, crew_service, basic_config):
        """测试处理回答更新历史记录"""
        # 创建会话
        state = await crew_service.create_session(user_id=1, config=basic_config)

        # Mock agents
        mock_result = Mock()
        mock_result.success = True
        mock_result.metadata = {"scores": {}}

        session_data = crew_service._sessions[state.session_id]

        with patch.object(session_data["evaluator"], "execute", return_value=mock_result):
            await crew_service.process_answer(
                session_id=state.session_id,
                answer="Test answer",
            )

        # 验证历史记录
        history = session_data["conversation_history"]
        assert len(history) == 1
        assert history[0]["role"] == "candidate"
        assert history[0]["content"] == "Test answer"


class TestCrewCoaching:
    """测试学习建议功能"""

    @pytest.mark.asyncio
    async def test_generate_coaching(self, crew_service):
        """测试生成学习建议"""
        config = CrewSessionConfig(
            scenario_id="frontend_senior",
            enable_coach=True,
        )

        state = await crew_service.create_session(user_id=1, config=config)

        # Mock coach agent
        mock_result = Mock()
        mock_result.success = True
        mock_result.content = "Here are your learning recommendations..."

        with patch.object(
            crew_service._sessions[state.session_id]["coach"],
            "execute",
            return_value=mock_result,
        ):
            result = await crew_service.generate_coaching(state.session_id)

        assert result["success"] is True
        assert "coaching" in result
        assert result["agent"] == "coach"

    @pytest.mark.asyncio
    async def test_generate_coaching_disabled(self, crew_service, basic_config):
        """测试学习顾问未启用的情况"""
        state = await crew_service.create_session(user_id=1, config=basic_config)

        result = await crew_service.generate_coaching(state.session_id)

        assert result["error"] == "Coach agent not enabled"

    @pytest.mark.asyncio
    async def test_generate_learning_plan(self, crew_service):
        """测试生成学习计划"""
        config = CrewSessionConfig(enable_coach=True)
        state = await crew_service.create_session(user_id=1, config=config)

        # Mock coach agent
        mock_result = Mock()
        mock_result.success = True
        mock_result.content = "Your learning plan..."

        with patch.object(
            crew_service._sessions[state.session_id]["coach"],
            "execute",
            return_value=mock_result,
        ):
            result = await crew_service.generate_learning_plan(
                session_id=state.session_id,
                target_position="Senior Frontend Developer",
            )

        assert result["success"] is True
        assert "learning_plan" in result


class TestCrewProgressTracking:
    """测试进度跟踪"""

    @pytest.mark.asyncio
    async def test_get_session_progress(self, crew_service, basic_config):
        """测试获取会话进度"""
        state = await crew_service.create_session(user_id=1, config=basic_config)
        await crew_service.start_session(state.session_id)

        progress = crew_service.get_session_progress(state.session_id)

        assert progress["session_id"] == state.session_id
        assert "status" in progress
        assert "progress_percent" in progress

    @pytest.mark.asyncio
    async def test_progress_updates_with_questions(self, crew_service, basic_config):
        """测试进度随问题更新"""
        state = await crew_service.create_session(user_id=1, config=basic_config)

        # Mock agent
        mock_result = Mock()
        mock_result.success = True
        mock_result.content = "Question?"
        mock_result.metadata = {}

        with patch.object(
            crew_service._sessions[state.session_id]["interviewer"],
            "execute",
            return_value=mock_result,
        ):
            await crew_service.generate_question(state.session_id)

        state_obj = crew_service.get_session_state(state.session_id)
        assert state_obj.questions_asked == 1


class TestCrewSessionState:
    """测试会话状态管理"""

    @pytest.mark.asyncio
    async def test_session_state_transitions(self, crew_service, basic_config):
        """测试会话状态转换"""
        # created -> active
        state = await crew_service.create_session(user_id=1, config=basic_config)
        assert state.status == "created"

        await crew_service.start_session(state.session_id)
        state = crew_service.get_session_state(state.session_id)
        assert state.status == "active"

        # active -> paused
        crew_service.pause_session(state.session_id)
        state = crew_service.get_session_state(state.session_id)
        assert state.status == "paused"

        # paused -> active
        crew_service.resume_session(state.session_id)
        state = crew_service.get_session_state(state.session_id)
        assert state.status == "active"

    @pytest.mark.asyncio
    async def test_list_active_sessions(self, crew_service, basic_config):
        """测试列出活动会话"""
        # 创建多个会话
        state1 = await crew_service.create_session(user_id=1, config=basic_config)
        state2 = await crew_service.create_session(user_id=1, config=basic_config)

        await crew_service.start_session(state1.session_id)
        await crew_service.start_session(state2.session_id)

        # 暂停一个
        crew_service.pause_session(state2.session_id)

        active_sessions = crew_service.list_active_sessions()

        assert len(active_sessions) == 2
        assert all(s.status in ["active", "paused"] for s in active_sessions)


class TestCrewScenarios:
    """测试场景配置"""

    @pytest.mark.asyncio
    async def test_get_available_scenarios(self, crew_service, mock_db):
        """测试获取可用场景"""
        scenarios = await crew_service.get_available_scenarios()

        assert isinstance(scenarios, list)
        if scenarios:  # 如果有配置
            for scenario in scenarios:
                assert "id" in scenario
                assert "name" in scenario
                assert "description" in scenario

    @pytest.mark.asyncio
    async def test_scenario_config_loading(self, crew_service):
        """测试场景配置加载"""
        config = CrewSessionConfig(scenario_id="frontend_junior")
        state = await crew_service.create_session(user_id=1, config=config)

        session_data = crew_service._sessions[state.session_id]

        # 验证场景配置被加载
        assert session_data["config"].scenario_id == "frontend_junior"


class TestCrewErrorHandling:
    """测试错误处理"""

    @pytest.mark.asyncio
    async def test_invalid_session_operations(self, crew_service):
        """测试无效会话操作"""
        with pytest.raises(ValueError):
            await crew_service.generate_question("invalid_session")

        with pytest.raises(ValueError):
            await crew_service.process_answer("invalid_session", "answer")

        with pytest.raises(ValueError):
            await crew_service.end_session("invalid_session")

    @pytest.mark.asyncio
    async def test_agent_execution_failure(self, crew_service, basic_config):
        """测试 Agent 执行失败"""
        state = await crew_service.create_session(user_id=1, config=basic_config)

        # Mock failed agent execution
        mock_result = Mock()
        mock_result.success = False
        mock_result.error = "Agent execution failed"

        with patch.object(
            crew_service._sessions[state.session_id]["interviewer"],
            "execute",
            return_value=mock_result,
        ):
            result = await crew_service.generate_question(state.session_id)

        assert result["success"] is False
        assert "error" in result


class TestCrewFinalReport:
    """测试最终报告"""

    @pytest.mark.asyncio
    async def test_end_session_generates_report(self, crew_service, basic_config):
        """测试结束会话生成报告"""
        state = await crew_service.create_session(user_id=1, config=basic_config)

        # 添加一些评估数据
        session_data = crew_service._sessions[state.session_id]
        session_data["evaluations"] = [
            {
                "question": "Q1",
                "evaluation": {"scores": {"technical": 4.0}},
            }
        ]

        # Mock evaluator for final report
        mock_result = Mock()
        mock_result.success = True
        mock_result.metadata = {"overall_score": 4.0}
        mock_result.content = "Final report content"

        with patch.object(
            session_data["evaluator"],
            "execute",
            return_value=mock_result,
        ):
            result = await crew_service.end_session(state.session_id)

        assert result["status"] == "completed"
        assert "final_report" in result
        assert result["questions_asked"] >= 0
