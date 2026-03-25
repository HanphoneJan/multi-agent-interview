"""Crew 模式面试 WebSocket 处理器

基于多 Agent 协作的面试系统，支持面试官、评估员、学习顾问协同工作。
端点: /ws/interview/crew/{session_id}

与原有的 interview_realtime.py 共存，提供 CrewAI 模式的面试体验。
"""

import asyncio
import json
import uuid
from datetime import datetime, timezone
from typing import Any, Optional
from enum import Enum

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status
from sqlalchemy import select, update, insert

from app.dependencies import SessionDep
from app.websockets.manager import manager
from app.websockets.protocol import (
    MessageType,
    BaseMessage,
    ProgressMessage,
    ErrorMessage,
    QuestionMessage,
)
from app.agents import (
    InterviewerAgent,
    EvaluatorAgent,
    CoachAgent,
    Task,
    TaskPriority,
)
from app.agents.interview_flow import InterviewFlow, InterviewContext, InterviewStage, InterviewType
from app.agents.config import get_scenario
from app.utils.log_helper import get_logger

logger = get_logger("websockets.interview_crew")

router = APIRouter()


class CrewMessageType(str, Enum):
    """Crew 模式消息类型"""

    # Client -> Server
    START = "start"
    ANSWER = "answer"
    AUDIO_INPUT = "audio_input"
    TEXT_INPUT = "text_input"
    NEXT_QUESTION = "next_question"
    REQUEST_EVALUATION = "request_evaluation"
    REQUEST_COACHING = "request_coaching"
    PAUSE = "pause"
    RESUME = "resume"
    END = "end"
    PING = "ping"

    # Server -> Client
    CONNECTED = "connected"
    QUESTION = "question"
    AGENT_THINKING = "agent_thinking"
    AGENT_RESPONSE = "agent_response"
    EVALUATION = "evaluation"
    COACHING = "coaching"
    PROGRESS = "progress"
    STAGE_CHANGE = "stage_change"
    FLOW_UPDATE = "flow_update"
    INFO = "info"
    ERROR = "error"
    PONG = "pong"
    STREAM_CHUNK = "stream_chunk"


class CrewInterviewSession:
    """Crew 面试会话

    管理一个 Crew 模式面试的完整生命周期。
    """

    def __init__(
        self,
        session_id: str,
        user_id: int,
        scenario_id: str,
        interview_type: InterviewType = InterviewType.CUSTOM,
        candidate_level: str = "junior",
    ):
        self.session_id = session_id
        self.user_id = user_id
        self.scenario_id = scenario_id
        self.interview_type = interview_type
        self.candidate_level = candidate_level

        # Agent 实例
        self.interviewer = InterviewerAgent()
        self.evaluator = EvaluatorAgent()
        self.coach: Optional[CoachAgent] = None

        # 流程控制器
        self.flow: Optional[InterviewFlow] = None
        self.interview_context: Optional[InterviewContext] = None

        # 会话状态
        self.is_active = False
        self.is_paused = False
        self.current_question: Optional[str] = None
        self.current_answer: Optional[str] = None
        self.conversation_history: list[dict[str, Any]] = []
        self.evaluations: list[dict[str, Any]] = []

        # 配置
        self.scenario_config: Optional[dict] = None

        # 创建时间
        self.created_at = datetime.now(timezone.utc)
        self.started_at: Optional[datetime] = None
        self.ended_at: Optional[datetime] = None

    async def initialize(self) -> dict[str, Any]:
        """初始化会话"""
        logger.info(f"Initializing Crew session: {self.session_id}")

        # 加载场景配置
        self.scenario_config = get_scenario(self.scenario_id)
        if self.scenario_config:
            # 根据配置调整
            self.candidate_level = self.scenario_config.get("target_level", self.candidate_level)
            agents_needed = self.scenario_config.get("agents", ["interviewer", "evaluator"])

            # 初始化学习顾问（如果需要）
            if "coach" in agents_needed:
                self.coach = CoachAgent()

        # 初始化流程控制器
        self.flow = InterviewFlow(
            interview_type=self.interview_type,
            candidate_level=self.candidate_level,
        )

        # 初始化面试上下文
        self.interview_context = InterviewContext(
            interview_id=self.session_id,
            interview_type=self.interview_type,
            candidate_id=str(self.user_id),
            candidate_level=self.candidate_level,
        )

        self.is_active = True
        self.started_at = datetime.now(timezone.utc)

        return {
            "status": "initialized",
            "session_id": self.session_id,
            "scenario": self.scenario_id,
            "agents": self._get_active_agents(),
        }

    def _get_active_agents(self) -> list[str]:
        """获取当前激活的 Agent 列表"""
        agents = ["interviewer", "evaluator"]
        if self.coach:
            agents.append("coach")
        return agents

    async def generate_question(self) -> dict[str, Any]:
        """生成面试问题"""
        if not self.is_active:
            return {"error": "Session not active"}

        # 构建上下文
        context = {
            "task_type": "generate_question",
            "scenario": self.scenario_id,
            "candidate_info": {
                "level": self.candidate_level,
                "user_id": self.user_id,
            },
            "history": self.conversation_history,
            "current_stage": self.interview_context.current_stage.value if self.interview_context else "unknown",
        }

        # 创建任务
        task = Task(
            description="生成下一个面试问题",
            expected_output="面试问题和考察点",
            agent_role="interviewer",
            priority=TaskPriority.HIGH,
        )

        # 执行 Agent
        try:
            result = await self.interviewer.execute(task, context)

            if result.success:
                self.current_question = result.content if isinstance(result.content, str) else str(result.content)

                # 添加到对话历史
                self.conversation_history.append({
                    "role": "interviewer",
                    "content": self.current_question,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                })

                return {
                    "success": True,
                    "question": self.current_question,
                    "agent": "interviewer",
                    "metadata": result.metadata,
                }
            else:
                return {
                    "success": False,
                    "error": result.error or "Failed to generate question",
                }

        except Exception as e:
            logger.error(f"Error generating question: {e}")
            return {
                "success": False,
                "error": str(e),
            }

    async def process_answer(self, answer: str, answer_type: str = "text") -> dict[str, Any]:
        """处理候选人回答"""
        if not self.is_active:
            return {"error": "Session not active"}

        self.current_answer = answer

        # 添加到对话历史
        self.conversation_history.append({
            "role": "candidate",
            "content": answer,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "type": answer_type,
        })

        # 并行执行评估和追问生成
        results = await asyncio.gather(
            self._evaluate_answer(answer),
            self._generate_follow_up(answer),
            return_exceptions=True,
        )

        evaluation_result = results[0] if not isinstance(results[0], Exception) else {"error": str(results[0])}
        follow_up_result = results[1] if not isinstance(results[1], Exception) else {"error": str(results[1])}

        return {
            "success": True,
            "evaluation": evaluation_result,
            "follow_up": follow_up_result,
        }

    async def _evaluate_answer(self, answer: str) -> dict[str, Any]:
        """评估回答"""
        if not self.current_question:
            return {"error": "No current question"}

        context = {
            "task_type": "evaluate_answer",
            "scenario": self.scenario_id,
            "question": self.current_question,
            "answer": answer,
            "history": self.conversation_history,
        }

        task = Task(
            description="评估候选人回答",
            expected_output="JSON 格式的评估结果",
            agent_role="evaluator",
            priority=TaskPriority.NORMAL,
        )

        try:
            result = await self.evaluator.execute(task, context)

            if result.success:
                evaluation = {
                    "question": self.current_question,
                    "answer": answer,
                    "evaluation": result.metadata,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
                self.evaluations.append(evaluation)

                return {
                    "success": True,
                    "scores": result.metadata.get("scores", {}),
                    "strengths": result.metadata.get("strengths", []),
                    "weaknesses": result.metadata.get("weaknesses", []),
                }
            else:
                return {"success": False, "error": result.error}

        except Exception as e:
            logger.error(f"Error evaluating answer: {e}")
            return {"success": False, "error": str(e)}

    async def _generate_follow_up(self, answer: str) -> dict[str, Any]:
        """生成追问"""
        context = {
            "task_type": "follow_up",
            "scenario": self.scenario_id,
            "current_question": self.current_question,
            "candidate_answer": answer,
            "history": self.conversation_history,
        }

        task = Task(
            description="基于回答进行追问",
            expected_output="追问内容",
            agent_role="interviewer",
            priority=TaskPriority.NORMAL,
        )

        try:
            result = await self.interviewer.execute(task, context)

            if result.success:
                return {
                    "success": True,
                    "follow_up": result.content if isinstance(result.content, str) else str(result.content),
                }
            else:
                return {"success": False, "error": result.error}

        except Exception as e:
            logger.error(f"Error generating follow up: {e}")
            return {"success": False, "error": str(e)}

    async def generate_coaching(self) -> dict[str, Any]:
        """生成学习建议"""
        if not self.coach:
            return {"error": "Coach agent not enabled"}

        if not self.evaluations:
            return {"error": "No evaluations available"}

        context = {
            "task_type": "analyze_weaknesses",
            "scenario": self.scenario_id,
            "candidate_info": {
                "level": self.candidate_level,
                "user_id": self.user_id,
            },
            "evaluation_results": self.evaluations,
            "answers_summary": self._summarize_answers(),
        }

        task = Task(
            description="分析能力薄弱点并提供学习建议",
            expected_output="学习建议和计划",
            agent_role="coach",
            priority=TaskPriority.LOW,
        )

        try:
            result = await self.coach.execute(task, context)

            if result.success:
                return {
                    "success": True,
                    "coaching": result.content if isinstance(result.content, str) else str(result.content),
                    "agent": "coach",
                }
            else:
                return {"success": False, "error": result.error}

        except Exception as e:
            logger.error(f"Error generating coaching: {e}")
            return {"success": False, "error": str(e)}

    def _summarize_answers(self) -> str:
        """总结回答历史"""
        summaries = []
        for item in self.conversation_history:
            if item.get("role") == "candidate":
                content = item.get("content", "")[:100]  # 截断
                summaries.append(content)
        return " | ".join(summaries)

    async def end_session(self) -> dict[str, Any]:
        """结束会话"""
        self.is_active = False
        self.ended_at = datetime.now(timezone.utc)

        # 生成最终评估报告
        final_evaluation = await self._generate_final_report()

        return {
            "status": "ended",
            "session_id": self.session_id,
            "duration": self._get_duration(),
            "total_questions": len([h for h in self.conversation_history if h.get("role") == "interviewer"]),
            "final_evaluation": final_evaluation,
        }

    async def _generate_final_report(self) -> dict[str, Any]:
        """生成最终评估报告"""
        if not self.evaluations:
            return {"error": "No evaluations available"}

        context = {
            "task_type": "generate_report",
            "scenario": self.scenario_id,
            "interview_duration": self._get_duration(),
            "evaluations": self.evaluations,
            "history_summary": self._summarize_answers(),
        }

        task = Task(
            description="生成综合评估报告",
            expected_output="JSON 格式的评估报告",
            agent_role="evaluator",
            priority=TaskPriority.HIGH,
        )

        try:
            result = await self.evaluator.execute(task, context)

            if result.success:
                return {
                    "success": True,
                    "report": result.metadata,
                    "content": result.content if isinstance(result.content, str) else str(result.content),
                }
            else:
                return {"success": False, "error": result.error}

        except Exception as e:
            logger.error(f"Error generating final report: {e}")
            return {"success": False, "error": str(e)}

    def _get_duration(self) -> str:
        """获取面试时长"""
        if not self.started_at:
            return "0分钟"

        end_time = self.ended_at or datetime.now(timezone.utc)
        duration = (end_time - self.started_at).total_seconds()

        minutes = int(duration // 60)
        seconds = int(duration % 60)

        if minutes > 0:
            return f"{minutes}分{seconds}秒"
        return f"{seconds}秒"

    def get_progress(self) -> dict[str, Any]:
        """获取面试进度"""
        if self.flow:
            return self.flow.get_progress()

        return {
            "status": "active" if self.is_active else "inactive",
            "questions_asked": len([h for h in self.conversation_history if h.get("role") == "interviewer"]),
            "answers_given": len([h for h in self.conversation_history if h.get("role") == "candidate"]),
            "evaluations_count": len(self.evaluations),
        }


# 会话管理器
_crew_sessions: dict[str, CrewInterviewSession] = {}


def get_or_create_session(
    session_id: str,
    user_id: int,
    scenario_id: str,
    interview_type: InterviewType = InterviewType.CUSTOM,
    candidate_level: str = "junior",
) -> CrewInterviewSession:
    """获取或创建会话"""
    if session_id not in _crew_sessions:
        _crew_sessions[session_id] = CrewInterviewSession(
            session_id=session_id,
            user_id=user_id,
            scenario_id=scenario_id,
            interview_type=interview_type,
            candidate_level=candidate_level,
        )
    return _crew_sessions[session_id]


def remove_session(session_id: str) -> None:
    """移除会话"""
    if session_id in _crew_sessions:
        del _crew_sessions[session_id]


@router.websocket("/ws/interview/crew/{session_id}")
async def interview_crew_websocket(
    websocket: WebSocket,
    session_id: str,
    token: str,
    scenario: str = "frontend_junior",
    db: SessionDep = None,
):
    """Crew 模式面试 WebSocket

    支持:
    - 多 Agent 协作面试
    - 实时评估反馈
    - 个性化学习建议
    - 灵活的流程控制

    消息协议:
    - Client -> Server:
      - {type: "start", scenario: "..."}  # 开始面试
      - {type: "answer", content: "..."}  # 回答问题
      - {type: "audio_input", data: "..."}  # 音频输入
      - {type: "text_input", content: "..."}  # 文本输入
      - {type: "next_question"}  # 请求下一题
      - {type: "request_evaluation"}  # 请求评估
      - {type: "request_coaching"}  # 请求学习建议
      - {type: "pause"}  # 暂停
      - {type: "resume"}  # 恢复
      - {type: "end"}  # 结束
      - {type: "ping"}  # 心跳

    - Server -> Client:
      - {type: "connected", ...}  # 连接成功
      - {type: "question", content: "..."}  # 面试问题
      - {type: "agent_thinking", agent: "..."}  # Agent 思考中
      - {type: "agent_response", agent: "...", content: "..."}  # Agent 响应
      - {type: "evaluation", ...}  # 评估结果
      - {type: "coaching", ...}  # 学习建议
      - {type: "progress", ...}  # 进度更新
      - {type: "flow_update", ...}  # 流程更新
      - {type: "info", message: "..."}  # 提示信息
      - {type: "error", error: "..."}  # 错误
      - {type: "pong"}  # 心跳响应
    """

    # 身份验证
    from app.core.security import verify_token
    from app.config import get_settings

    settings = get_settings()

    logger.info(f"Crew WebSocket 连接请求: session_id={session_id}, scenario={scenario}")

    if not token:
        logger.warning("连接被拒绝: 缺少 token")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Missing token")
        return

    payload = verify_token(token, settings.JWT_SECRET_KEY)
    if not payload:
        logger.warning("连接被拒绝: token 验证失败")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid token")
        return

    user_id = payload.get("user_id")

    # 接受连接
    await manager.connect(websocket, session_id)

    # 获取或创建会话
    crew_session = get_or_create_session(
        session_id=session_id,
        user_id=user_id,
        scenario_id=scenario,
    )

    try:
        # 发送连接成功消息
        await websocket.send_json({
            "type": CrewMessageType.CONNECTED,
            "session_id": session_id,
            "scenario": scenario,
            "agents": crew_session._get_active_agents(),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

        # 消息处理循环
        while True:
            try:
                message = await websocket.receive_json()
                msg_type = message.get("type")

                if msg_type == CrewMessageType.PING:
                    await websocket.send_json({"type": CrewMessageType.PONG})

                elif msg_type == CrewMessageType.START:
                    # 初始化会话
                    init_result = await crew_session.initialize()
                    await websocket.send_json({
                        "type": CrewMessageType.FLOW_UPDATE,
                        "data": init_result,
                    })

                    # 生成第一个问题
                    await websocket.send_json({
                        "type": CrewMessageType.AGENT_THINKING,
                        "agent": "interviewer",
                    })

                    question_result = await crew_session.generate_question()
                    await websocket.send_json({
                        "type": CrewMessageType.QUESTION,
                        "content": question_result.get("question"),
                        "metadata": question_result.get("metadata", {}),
                    })

                elif msg_type == CrewMessageType.ANSWER or msg_type == CrewMessageType.TEXT_INPUT:
                    # 处理回答
                    content = message.get("content", "")
                    answer_type = "text" if msg_type == CrewMessageType.TEXT_INPUT else message.get("answer_type", "text")

                    # 通知正在处理
                    await websocket.send_json({
                        "type": CrewMessageType.AGENT_THINKING,
                        "agent": "evaluator",
                    })

                    result = await crew_session.process_answer(content, answer_type)

                    # 发送评估结果
                    if result.get("success"):
                        await websocket.send_json({
                            "type": CrewMessageType.EVALUATION,
                            "data": result.get("evaluation", {}),
                        })

                        # 发送追问
                        follow_up = result.get("follow_up", {})
                        if follow_up.get("success") and follow_up.get("follow_up"):
                            await websocket.send_json({
                                "type": CrewMessageType.AGENT_RESPONSE,
                                "agent": "interviewer",
                                "content": follow_up.get("follow_up"),
                            })

                elif msg_type == CrewMessageType.NEXT_QUESTION:
                    # 请求下一题
                    await websocket.send_json({
                        "type": CrewMessageType.AGENT_THINKING,
                        "agent": "interviewer",
                    })

                    question_result = await crew_session.generate_question()
                    await websocket.send_json({
                        "type": CrewMessageType.QUESTION,
                        "content": question_result.get("question"),
                        "metadata": question_result.get("metadata", {}),
                    })

                elif msg_type == CrewMessageType.REQUEST_EVALUATION:
                    # 请求评估报告
                    await websocket.send_json({
                        "type": CrewMessageType.AGENT_THINKING,
                        "agent": "evaluator",
                    })

                    final_report = await crew_session._generate_final_report()
                    await websocket.send_json({
                        "type": CrewMessageType.EVALUATION,
                        "data": final_report,
                    })

                elif msg_type == CrewMessageType.REQUEST_COACHING:
                    # 请求学习建议
                    if crew_session.coach:
                        await websocket.send_json({
                            "type": CrewMessageType.AGENT_THINKING,
                            "agent": "coach",
                        })

                        coaching_result = await crew_session.generate_coaching()
                        await websocket.send_json({
                            "type": CrewMessageType.COACHING,
                            "data": coaching_result,
                        })
                    else:
                        await websocket.send_json({
                            "type": CrewMessageType.INFO,
                            "message": "学习顾问未在此场景中启用",
                        })

                elif msg_type == CrewMessageType.PAUSE:
                    crew_session.is_paused = True
                    await websocket.send_json({
                        "type": CrewMessageType.INFO,
                        "message": "面试已暂停",
                    })

                elif msg_type == CrewMessageType.RESUME:
                    crew_session.is_paused = False
                    await websocket.send_json({
                        "type": CrewMessageType.INFO,
                        "message": "面试已恢复",
                    })

                elif msg_type == CrewMessageType.END:
                    # 结束面试
                    end_result = await crew_session.end_session()
                    await websocket.send_json({
                        "type": CrewMessageType.FLOW_UPDATE,
                        "data": end_result,
                    })
                    break

                elif msg_type == CrewMessageType.PROGRESS:
                    # 请求进度
                    progress = crew_session.get_progress()
                    await websocket.send_json({
                        "type": CrewMessageType.PROGRESS,
                        "data": progress,
                    })

                else:
                    await websocket.send_json({
                        "type": CrewMessageType.ERROR,
                        "error": f"Unknown message type: {msg_type}",
                    })

            except WebSocketDisconnect:
                logger.info(f"WebSocket disconnected: {session_id}")
                break
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                await websocket.send_json({
                    "type": CrewMessageType.ERROR,
                    "error": str(e),
                })

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {session_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        # 清理
        manager.disconnect(websocket, session_id)
        if crew_session and not crew_session.is_active:
            remove_session(session_id)
        logger.info(f"Crew WebSocket connection closed: {session_id}")
