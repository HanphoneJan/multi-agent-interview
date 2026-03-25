"""BaseAgent 测试"""

import pytest
from datetime import datetime

from app.agents.base import BaseAgent, AgentOutput, LLMConfig, AgentStatus
from app.agents.task import Task


class MockAgent(BaseAgent):
    """测试用的 Mock Agent"""

    async def execute(self, task: Task, context: dict) -> AgentOutput:
        return AgentOutput(
            content=f"Executed: {task.description}",
            success=True,
            agent_id=self.agent_id,
        )


class TestAgentOutput:
    """测试 AgentOutput 类"""

    def test_agent_output_creation(self):
        """测试创建 AgentOutput"""
        output = AgentOutput(
            content="Test content",
            metadata={"key": "value"},
            success=True,
            agent_id="test_agent",
        )

        assert output.content == "Test content"
        assert output.metadata == {"key": "value"}
        assert output.success is True
        assert output.agent_id == "test_agent"
        assert output.error is None
        assert isinstance(output.timestamp, datetime)

    def test_agent_output_auto_id(self):
        """测试自动生成的 agent_id"""
        output = AgentOutput(content="Test")
        assert output.agent_id
        assert len(output.agent_id) == 8

    def test_agent_output_failure(self):
        """测试失败的输出"""
        output = AgentOutput(
            content="",
            success=False,
            error="Something went wrong",
        )

        assert output.success is False
        assert output.error == "Something went wrong"


class TestLLMConfig:
    """测试 LLMConfig 类"""

    def test_default_config(self):
        """测试默认配置"""
        config = LLMConfig()

        assert config.model == "qwen-plus"
        assert config.temperature == 0.7
        assert config.max_tokens == 2048
        assert config.top_p == 0.9
        assert config.api_key is None
        assert config.base_url is None

    def test_custom_config(self):
        """测试自定义配置"""
        config = LLMConfig(
            model="gpt-4",
            temperature=0.5,
            max_tokens=4096,
            api_key="test_key",
        )

        assert config.model == "gpt-4"
        assert config.temperature == 0.5
        assert config.max_tokens == 4096
        assert config.api_key == "test_key"


class TestBaseAgent:
    """测试 BaseAgent 类"""

    @pytest.mark.asyncio
    async def test_agent_initialization(self):
        """测试 Agent 初始化"""
        agent = MockAgent(
            role="Test Role",
            goal="Test Goal",
            backstory="Test Backstory",
        )

        assert agent.role == "Test Role"
        assert agent.goal == "Test Goal"
        assert agent.backstory == "Test Backstory"
        assert agent.status == AgentStatus.IDLE
        assert agent.agent_id
        assert len(agent.agent_id) == 8

    @pytest.mark.asyncio
    async def test_agent_execute(self):
        """测试 Agent 执行"""
        agent = MockAgent(
            role="Test",
            goal="Test",
            backstory="Test",
        )

        task = Task(
            description="Test task",
            expected_output="Test output",
            agent_role="test",
        )

        result = await agent.execute(task, {})

        assert result.success is True
        assert "Executed" in str(result.content)
        assert result.agent_id == agent.agent_id

    def test_build_system_prompt(self):
        """测试构建系统 Prompt"""
        agent = MockAgent(
            role="Interviewer",
            goal="Conduct interviews",
            backstory="Experienced interviewer",
        )

        prompt = agent.build_system_prompt()

        assert "Interviewer" in prompt
        assert "Conduct interviews" in prompt
        assert "Experienced interviewer" in prompt

    def test_build_task_prompt(self):
        """测试构建任务 Prompt"""
        agent = MockAgent(
            role="Test",
            goal="Test",
            backstory="Test",
        )

        task = Task(
            description="Do something",
            expected_output="Result",
            agent_role="test",
        )

        prompt = agent.build_task_prompt(task, {"key": "value"})

        assert "Do something" in prompt
        assert "Result" in prompt
        assert "value" in prompt

    def test_get_status(self):
        """测试获取状态"""
        agent = MockAgent(role="Test", goal="Test", backstory="Test")

        assert agent.get_status() == AgentStatus.IDLE
        assert agent.is_available() is True

    def test_get_stats(self):
        """测试获取统计信息"""
        agent = MockAgent(
            role="Test Role",
            goal="Test",
            backstory="Test",
        )

        stats = agent.get_stats()

        assert stats["agent_id"] == agent.agent_id
        assert stats["role"] == "Test Role"
        assert stats["status"] == "idle"
        assert stats["execution_count"] == 0

    @pytest.mark.asyncio
    async def test_execute_stream(self):
        """测试流式执行"""
        agent = MockAgent(role="Test", goal="Test", backstory="Test")

        task = Task(
            description="Test",
            expected_output="Test",
            agent_role="test",
        )

        chunks = []
        async for chunk in agent.execute_stream(task, {}):
            chunks.append(chunk)

        assert len(chunks) > 0
