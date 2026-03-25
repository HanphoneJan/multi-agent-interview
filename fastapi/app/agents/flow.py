"""流程控制器

支持顺序、条件分支、并行等流程模式。
提供 CrewAI 风格的流程编排能力。
"""
from abc import ABC
from dataclasses import dataclass, field
from typing import Any, Callable, TypeVar
from enum import Enum
from collections.abc import Awaitable
import asyncio
import uuid
from datetime import datetime

from app.utils.log_helper import get_logger

logger = get_logger("agents.flow")

T = TypeVar("T")


class StepType(Enum):
    """流程步骤类型"""
    START = "start"           # 起始步骤
    TASK = "task"             # 普通任务步骤
    ROUTER = "router"         # 路由/条件分支
    LISTEN = "listen"         # 监听前序步骤
    PARALLEL = "parallel"     # 并行执行
    END = "end"               # 结束步骤


class FlowStatus(Enum):
    """流程状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class FlowStep:
    """流程步骤定义

    Attributes:
        step_id: 步骤唯一标识
        name: 步骤名称
        step_type: 步骤类型
        func: 执行的函数
        depends_on: 依赖的前置步骤 ID 列表
        metadata: 元数据
    """
    step_id: str
    name: str
    step_type: StepType
    func: Callable[..., Awaitable[Any]] | None = None
    depends_on: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class StepResult:
    """步骤执行结果

    Attributes:
        step_id: 步骤 ID
        output: 输出内容
        success: 是否成功
        next_steps: 下一步要执行的步骤 ID 列表（路由使用）
        metadata: 元数据
        timestamp: 执行时间
    """
    step_id: str
    output: Any = None
    success: bool = True
    next_steps: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)


class FlowContext:
    """流程执行上下文

    在流程执行过程中传递状态和数据。

    Attributes:
        flow_id: 流程实例 ID
        data: 共享数据存储
        step_results: 各步骤的执行结果
        current_step: 当前执行的步骤 ID
    """

    def __init__(self, flow_id: str | None = None, initial_data: dict[str, Any] | None = None):
        self.flow_id = flow_id or f"flow_{str(uuid.uuid4())[:8]}"
        self.data: dict[str, Any] = initial_data or {}
        self.step_results: dict[str, StepResult] = {}
        self.current_step: str | None = None
        self._lock = asyncio.Lock()

    async def set(self, key: str, value: Any) -> None:
        """异步设置数据"""
        async with self._lock:
            self.data[key] = value

    async def get(self, key: str, default: Any = None) -> Any:
        """异步获取数据"""
        async with self._lock:
            return self.data.get(key, default)

    def set_sync(self, key: str, value: Any) -> None:
        """同步设置数据（仅用于非并发场景）"""
        self.data[key] = value

    def get_sync(self, key: str, default: Any = None) -> Any:
        """同步获取数据（仅用于非并发场景）"""
        return self.data.get(key, default)

    def store_step_result(self, result: StepResult) -> None:
        """存储步骤执行结果"""
        self.step_results[result.step_id] = result

    def get_step_result(self, step_id: str) -> StepResult | None:
        """获取步骤执行结果"""
        return self.step_results.get(step_id)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典表示"""
        return {
            "flow_id": self.flow_id,
            "data": self.data,
            "step_results": {
                k: {
                    "step_id": v.step_id,
                    "success": v.success,
                    "timestamp": v.timestamp.isoformat(),
                }
                for k, v in self.step_results.items()
            },
            "current_step": self.current_step,
        }


class Flow(ABC):
    """流程控制器基类

    支持 CrewAI 风格的流程编排：
    - @start(): 标记起始步骤
    - @listen(step): 监听前序步骤完成
    - @router(step): 根据条件路由到不同分支
    - @parallel([steps]): 并行执行多个步骤

    Example:
        class InterviewFlow(Flow):
            @start()
            async def self_introduction(self, context: FlowContext):
                return "请自我介绍"

            @listen(self_introduction)
            async def technical_round(self, prev_result, context: FlowContext):
                return "技术问题"

            @router(technical_round)
            async def adaptive_next(self, prev_result, context: FlowContext):
                if context.get_sync("level") == "expert":
                    return "system_design"
                return "practical_coding"
    """

    def __init__(self, name: str | None = None):
        self.name = name or self.__class__.__name__
        self.flow_id = f"flow_{str(uuid.uuid4())[:8]}"
        self._steps: dict[str, FlowStep] = {}
        self._start_step: str | None = None
        self._step_order: list[str] = []
        self._status = FlowStatus.PENDING
        self._build_flow()

        logger.info(f"Flow initialized: {self.name} (id={self.flow_id})")

    def _build_flow(self) -> None:
        """构建流程图

        扫描类中定义的方法，识别装饰器标记的步骤，
        构建步骤依赖关系图。
        """
        for attr_name in dir(self):
            attr = getattr(self, attr_name)
            if callable(attr) and hasattr(attr, "_flow_meta"):
                meta = attr._flow_meta
                step_id = meta.get("step_id", attr_name)
                step_type = meta.get("step_type", StepType.TASK)

                # 确定依赖关系
                depends_on = []
                if "listens_to" in meta:
                    listened_func = meta["listens_to"]
                    if hasattr(listened_func, "_flow_meta"):
                        depends_on = [listened_func._flow_meta.get("step_id", listened_func.__name__)]

                step = FlowStep(
                    step_id=step_id,
                    name=attr_name,
                    step_type=step_type,
                    func=attr,
                    depends_on=depends_on,
                    metadata=meta,
                )
                self._steps[step_id] = step

                if step_type == StepType.START:
                    self._start_step = step_id

                self._step_order.append(step_id)

    async def execute(
        self,
        context: FlowContext | None = None,
        initial_data: dict[str, Any] | None = None,
    ) -> FlowContext:
        """执行流程

        Args:
            context: 流程上下文（可选）
            initial_data: 初始数据（如果未提供 context）

        Returns:
            FlowContext: 执行后的上下文
        """
        if context is None:
            context = FlowContext(initial_data=initial_data)

        self._status = FlowStatus.RUNNING
        logger.info(f"Flow {self.name} starting execution")

        try:
            if self._start_step:
                await self._execute_step(self._start_step, context)
            else:
                # 没有明确的 start 步骤，按顺序执行
                for step_id in self._step_order:
                    await self._execute_step(step_id, context)

            self._status = FlowStatus.COMPLETED
            logger.info(f"Flow {self.name} completed successfully")

        except Exception as e:
            self._status = FlowStatus.FAILED
            logger.error(f"Flow {self.name} failed: {e}")
            raise

        return context

    async def _execute_step(self, step_id: str, context: FlowContext) -> StepResult:
        """执行单个步骤

        Args:
            step_id: 步骤 ID
            context: 流程上下文

        Returns:
            StepResult: 步骤执行结果
        """
        step = self._steps.get(step_id)
        if not step or not step.func:
            raise ValueError(f"Step {step_id} not found or has no function")

        # 检查依赖是否满足
        for dep_id in step.depends_on:
            if dep_id not in context.step_results:
                await self._execute_step(dep_id, context)

        context.current_step = step_id
        logger.info(f"Executing step: {step.name} (type={step.step_type.value})")

        # 准备参数
        kwargs: dict[str, Any] = {"context": context}

        # 如果有依赖，传入前序结果
        if step.depends_on:
            prev_step_id = step.depends_on[0]
            prev_result = context.get_step_result(prev_step_id)
            if prev_result:
                kwargs["prev_result"] = prev_result.output

        # 执行步骤
        try:
            output = await step.func(self, **kwargs)

            # 处理路由结果
            next_steps = []
            if step.step_type == StepType.ROUTER and isinstance(output, str):
                next_steps = [output]

            result = StepResult(
                step_id=step_id,
                output=output,
                success=True,
                next_steps=next_steps,
            )

        except Exception as e:
            result = StepResult(
                step_id=step_id,
                output=None,
                success=False,
                metadata={"error": str(e)},
            )
            logger.error(f"Step {step.name} failed: {e}")

        context.store_step_result(result)

        # 执行后续步骤
        if result.next_steps:
            for next_step_id in result.next_steps:
                if next_step_id in self._steps:
                    await self._execute_step(next_step_id, context)
        elif step.step_type != StepType.ROUTER:
            # 自动执行下一个顺序步骤
            current_idx = self._step_order.index(step_id)
            if current_idx + 1 < len(self._step_order):
                next_step_id = self._step_order[current_idx + 1]
                next_step = self._steps[next_step_id]
                if not next_step.depends_on:  # 只有无依赖的步骤才自动执行
                    await self._execute_step(next_step_id, context)

        return result

    def get_status(self) -> FlowStatus:
        """获取流程状态"""
        return self._status

    def get_steps(self) -> list[FlowStep]:
        """获取所有步骤定义"""
        return list(self._steps.values())


# 装饰器函数

def start() -> Callable[[Callable[..., Awaitable[T]]], Callable[..., Awaitable[T]]]:
    """标记起始步骤的装饰器

    Example:
        @start()
        async def initialize(self, context: FlowContext):
            return "initialized"
    """
    def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        func._flow_meta = {  # type: ignore
            "step_type": StepType.START,
            "step_id": func.__name__,
        }
        return func
    return decorator


def listen(
    step_func: Callable[..., Awaitable[T]]
) -> Callable[[Callable[..., Awaitable[T]]], Callable[..., Awaitable[T]]]:
    """标记监听前序步骤的装饰器

    Args:
        step_func: 要监听的前序步骤函数

    Example:
        @listen(self_introduction)
        async def technical_questions(self, prev_result, context: FlowContext):
            return f"Based on: {prev_result}"
    """
    def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        meta = getattr(func, "_flow_meta", {})
        meta.update({
            "step_type": StepType.LISTEN,
            "step_id": func.__name__,
            "listens_to": step_func,
        })
        func._flow_meta = meta  # type: ignore
        return func
    return decorator


def router(
    step_func: Callable[..., Awaitable[T]]
) -> Callable[[Callable[..., Awaitable[T]]], Callable[..., Awaitable[T]]]:
    """标记路由/条件分支的装饰器

    Args:
        step_func: 前序步骤函数

    Example:
        @router(technical_questions)
        async def decide_next(self, prev_result, context: FlowContext):
            if prev_result == "expert":
                return "system_design"
            return "basic_coding"
    """
    def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        meta = getattr(func, "_flow_meta", {})
        meta.update({
            "step_type": StepType.ROUTER,
            "step_id": func.__name__,
            "listens_to": step_func,
        })
        func._flow_meta = meta  # type: ignore
        return func
    return decorator


def parallel(
    step_funcs: list[Callable[..., Awaitable[T]]]
) -> Callable[[Callable[..., Awaitable[T]]], Callable[..., Awaitable[T]]]:
    """标记并行步骤的装饰器

    Args:
        step_funcs: 要并行执行的步骤函数列表

    Example:
        @parallel([evaluate_technical, evaluate_communication])
        async def combine_evaluations(self, results, context: FlowContext):
            return combine(results)
    """
    def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        meta = getattr(func, "_flow_meta", {})
        meta.update({
            "step_type": StepType.PARALLEL,
            "step_id": func.__name__,
            "parallel_steps": step_funcs,
        })
        func._flow_meta = meta  # type: ignore
        return func
    return decorator


def task() -> Callable[[Callable[..., Awaitable[T]]], Callable[..., Awaitable[T]]]:
    """标记普通任务步骤的装饰器

    Example:
        @task()
        async def process_data(self, context: FlowContext):
            return "processed"
    """
    def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        meta = getattr(func, "_flow_meta", {})
        meta.update({
            "step_type": StepType.TASK,
            "step_id": func.__name__,
        })
        func._flow_meta = meta  # type: ignore
        return func
    return decorator
