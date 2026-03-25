"""Flow 模块测试"""

import pytest
import asyncio

from app.agents.flow import (
    Flow,
    FlowContext,
    FlowStep,
    StepType,
    StepResult,
    FlowStatus,
    start,
    listen,
    router,
    task,
)


class TestFlowContext:
    """测试 FlowContext 类"""

    def test_context_creation(self):
        """测试创建上下文"""
        context = FlowContext()

        assert context.flow_id.startswith("flow_")
        assert context.data == {}
        assert context.step_results == {}
        assert context.current_step is None

    def test_context_with_initial_data(self):
        """测试带初始数据的上下文"""
        context = FlowContext(initial_data={"key": "value"})

        assert context.data == {"key": "value"}

    @pytest.mark.asyncio
    async def test_context_async_operations(self):
        """测试异步操作"""
        context = FlowContext()

        await context.set("key", "value")
        value = await context.get("key")

        assert value == "value"

    def test_context_sync_operations(self):
        """测试同步操作"""
        context = FlowContext()

        context.set_sync("key", "value")
        value = context.get_sync("key")

        assert value == "value"

    def test_context_default_value(self):
        """测试默认值"""
        context = FlowContext()

        value = context.get_sync("nonexistent", "default")
        assert value == "default"

    def test_context_store_step_result(self):
        """测试存储步骤结果"""
        context = FlowContext()

        result = StepResult(step_id="step_1", output="result", success=True)
        context.store_step_result(result)

        assert "step_1" in context.step_results
        assert context.get_step_result("step_1") == result

    def test_context_to_dict(self):
        """测试转换为字典"""
        context = FlowContext(initial_data={"key": "value"})
        result = StepResult(step_id="step_1", output="result", success=True)
        context.store_step_result(result)

        data = context.to_dict()

        assert data["flow_id"] == context.flow_id
        assert data["data"] == {"key": "value"}
        assert "step_1" in data["step_results"]


class TestFlowStep:
    """测试 FlowStep 类"""

    def test_step_creation(self):
        """测试创建步骤"""
        async def dummy_func():
            return "result"

        step = FlowStep(
            step_id="step_1",
            name="test_step",
            step_type=StepType.TASK,
            func=dummy_func,
        )

        assert step.step_id == "step_1"
        assert step.name == "test_step"
        assert step.step_type == StepType.TASK
        assert step.func == dummy_func
        assert step.depends_on == []

    def test_step_with_dependencies(self):
        """测试带依赖的步骤"""
        step = FlowStep(
            step_id="step_2",
            name="dependent_step",
            step_type=StepType.LISTEN,
            depends_on=["step_1"],
        )

        assert step.depends_on == ["step_1"]


class TestStepResult:
    """测试 StepResult 类"""

    def test_result_creation(self):
        """测试创建结果"""
        result = StepResult(
            step_id="step_1",
            output="result",
            success=True,
            next_steps=["step_2"],
        )

        assert result.step_id == "step_1"
        assert result.output == "result"
        assert result.success is True
        assert result.next_steps == ["step_2"]

    def test_result_default_values(self):
        """测试默认值"""
        result = StepResult(step_id="step_1")

        assert result.output is None
        assert result.success is True
        assert result.next_steps == []
        assert result.metadata == {}


class TestFlowDecorators:
    """测试 Flow 装饰器"""

    def test_start_decorator(self):
        """测试 @start 装饰器"""
        class TestFlow(Flow):
            @start()
            async def init_step(self, context):
                return "initialized"

        flow = TestFlow()

        assert flow._start_step == "init_step"
        assert "init_step" in flow._steps
        assert flow._steps["init_step"].step_type == StepType.START

    def test_listen_decorator(self):
        """测试 @listen 装饰器"""
        class TestFlow(Flow):
            @start()
            async def step1(self, context):
                return "step1"

            @listen(step1)
            async def step2(self, prev_result, context):
                return f"received: {prev_result}"

        flow = TestFlow()

        assert "step2" in flow._steps
        assert flow._steps["step2"].step_type == StepType.LISTEN
        assert "step1" in flow._steps["step2"].depends_on

    def test_router_decorator(self):
        """测试 @router 装饰器"""
        class TestFlow(Flow):
            @start()
            async def step1(self, context):
                return "step1"

            @router(step1)
            async def decision(self, prev_result, context):
                return "branch_a"

        flow = TestFlow()

        assert "decision" in flow._steps
        assert flow._steps["decision"].step_type == StepType.ROUTER

    def test_task_decorator(self):
        """测试 @task 装饰器"""
        class TestFlow(Flow):
            @task()
            async def standalone_task(self, context):
                return "done"

        flow = TestFlow()

        assert "standalone_task" in flow._steps
        assert flow._steps["standalone_task"].step_type == StepType.TASK


class TestFlowExecution:
    """测试 Flow 执行"""

    @pytest.mark.asyncio
    async def test_simple_flow_execution(self):
        """测试简单流程执行"""
        execution_order = []

        class SimpleFlow(Flow):
            @start()
            async def step1(self, context):
                execution_order.append("step1")
                await context.set("value", 1)
                return "result1"

            @listen(step1)
            async def step2(self, prev_result, context):
                execution_order.append("step2")
                value = await context.get("value")
                await context.set("value", value + 1)
                return f"result2: {prev_result}"

        flow = SimpleFlow()
        context = await flow.execute()

        assert execution_order == ["step1", "step2"]
        assert await context.get("value") == 2
        assert flow.get_status() == FlowStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_flow_with_router(self):
        """测试带路由的流程"""
        execution_order = []

        class RouterFlow(Flow):
            @start()
            async def start_step(self, context):
                execution_order.append("start")
                return "start_result"

            @router(start_step)
            async def decision(self, prev_result, context):
                execution_order.append("decision")
                return "branch_a"

            @task()
            async def branch_a(self, context):
                execution_order.append("branch_a")
                return "branch_a_result"

        flow = RouterFlow()
        context = await flow.execute()

        assert "decision" in execution_order
        assert flow.get_status() == FlowStatus.COMPLETED

    def test_flow_get_steps(self):
        """测试获取步骤列表"""
        class TestFlow(Flow):
            @start()
            async def step1(self, context):
                return "step1"

            @listen(step1)
            async def step2(self, prev_result, context):
                return "step2"

        flow = TestFlow()
        steps = flow.get_steps()

        assert len(steps) == 2
        step_ids = [s.step_id for s in steps]
        assert "step1" in step_ids
        assert "step2" in step_ids

    def test_flow_get_status(self):
        """测试获取流程状态"""
        class TestFlow(Flow):
            @start()
            async def step1(self, context):
                return "step1"

        flow = TestFlow()
        assert flow.get_status() == FlowStatus.PENDING


class TestStepType:
    """测试 StepType 枚举"""

    def test_step_type_values(self):
        """测试步骤类型值"""
        assert StepType.START.value == "start"
        assert StepType.TASK.value == "task"
        assert StepType.ROUTER.value == "router"
        assert StepType.LISTEN.value == "listen"
        assert StepType.PARALLEL.value == "parallel"
        assert StepType.END.value == "end"


class TestFlowStatus:
    """测试 FlowStatus 枚举"""

    def test_flow_status_values(self):
        """测试流程状态值"""
        assert FlowStatus.PENDING.value == "pending"
        assert FlowStatus.RUNNING.value == "running"
        assert FlowStatus.COMPLETED.value == "completed"
        assert FlowStatus.FAILED.value == "failed"
        assert FlowStatus.CANCELLED.value == "cancelled"
