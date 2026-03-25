"""Interview Crew API endpoints

Crew 模式面试的 REST API 端点。
提供会话管理、问题生成、评估报告等功能。
"""

from typing import Optional, Any
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.services.interview_crew_service import (
    InterviewCrewService,
    CrewSessionConfig,
    CrewSessionState,
)
from app.agents.interview_flow import InterviewType
from app.utils.log_helper import get_logger

logger = get_logger("api.interview_crew")

router = APIRouter(prefix="/interviews/crew", tags=["Interview Crew"])


# ============ Pydantic Models ============

class CreateCrewSessionRequest(BaseModel):
    """创建 Crew 会话请求"""
    scenario_id: str = Field(default="frontend_junior", description="面试场景 ID")
    interview_type: str = Field(default="custom", description="面试类型")
    candidate_level: str = Field(default="junior", description="候选人级别")
    enable_coach: bool = Field(default=False, description="是否启用学习顾问")
    enable_realtime_evaluation: bool = Field(default=True, description="是否启用实时评估")
    max_duration_minutes: int = Field(default=60, ge=10, le=120, description="最大时长(分钟)")


class CreateCrewSessionResponse(BaseModel):
    """创建 Crew 会话响应"""
    session_id: str
    status: str
    scenario_id: str
    agents: list[str]
    created_at: str


class CrewSessionStatusResponse(BaseModel):
    """会话状态响应"""
    session_id: str
    status: str
    current_stage: str
    progress_percent: float
    questions_asked: int
    answers_received: int
    evaluations_count: int
    duration: Optional[str] = None


class GenerateQuestionResponse(BaseModel):
    """生成问题响应"""
    success: bool
    question: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    agent: str = "interviewer"
    error: Optional[str] = None


class ProcessAnswerRequest(BaseModel):
    """处理回答请求"""
    answer: str = Field(..., min_length=1, description="回答内容")
    answer_type: str = Field(default="text", description="回答类型")


class ProcessAnswerResponse(BaseModel):
    """处理回答响应"""
    success: bool
    evaluation: dict[str, Any] = Field(default_factory=dict)
    follow_up: dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None


class CoachingResponse(BaseModel):
    """学习建议响应"""
    success: bool
    coaching: Optional[str] = None
    agent: str = "coach"
    error: Optional[str] = None


class LearningPlanRequest(BaseModel):
    """学习计划请求"""
    target_position: str = Field(..., min_length=1, description="目标岗位")
    available_time: str = Field(default="每周10小时", description="可用学习时间")


class LearningPlanResponse(BaseModel):
    """学习计划响应"""
    success: bool
    learning_plan: Optional[str] = None
    error: Optional[str] = None


class FinalReportResponse(BaseModel):
    """最终报告响应"""
    success: bool
    session_id: str
    duration: str
    questions_asked: int
    answers_received: int
    report: dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None


class ScenarioInfo(BaseModel):
    """场景信息"""
    id: str
    name: str
    description: str
    target_level: str
    agents: list[str]


class ScenariosListResponse(BaseModel):
    """场景列表响应"""
    scenarios: list[ScenarioInfo]
    total: int


class MessageResponse(BaseModel):
    """通用消息响应"""
    message: str


# ============ Dependency ============

async def get_crew_service(db: AsyncSession = Depends(get_db)) -> InterviewCrewService:
    """获取 Crew 服务实例"""
    return InterviewCrewService(db)


# ============ API Endpoints ============

@router.post(
    "/sessions",
    response_model=CreateCrewSessionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="创建 Crew 面试会话",
    description="创建一个新的 Crew 模式面试会话",
)
async def create_crew_session(
    request: CreateCrewSessionRequest,
    current_user: dict = Depends(get_current_user),
    service: InterviewCrewService = Depends(get_crew_service),
) -> CreateCrewSessionResponse:
    """创建新的 Crew 面试会话"""
    try:
        # 转换 interview_type
        try:
            interview_type = InterviewType(request.interview_type)
        except ValueError:
            interview_type = InterviewType.CUSTOM

        config = CrewSessionConfig(
            scenario_id=request.scenario_id,
            interview_type=interview_type,
            candidate_level=request.candidate_level,
            enable_coach=request.enable_coach,
            enable_realtime_evaluation=request.enable_realtime_evaluation,
            max_duration_minutes=request.max_duration_minutes,
        )

        state = await service.create_session(
            user_id=current_user["user_id"],
            config=config,
        )

        # 确定启用的 agents
        agents = ["interviewer", "evaluator"]
        if request.enable_coach:
            agents.append("coach")

        return CreateCrewSessionResponse(
            session_id=state.session_id,
            status=state.status,
            scenario_id=request.scenario_id,
            agents=agents,
            created_at=state.created_at.isoformat(),
        )

    except Exception as e:
        logger.error(f"Failed to create crew session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create session: {str(e)}",
        )


@router.post(
    "/sessions/{session_id}/start",
    response_model=CrewSessionStatusResponse,
    summary="开始面试会话",
    description="启动已创建的 Crew 面试会话",
)
async def start_crew_session(
    session_id: str,
    current_user: dict = Depends(get_current_user),
    service: InterviewCrewService = Depends(get_crew_service),
) -> CrewSessionStatusResponse:
    """开始面试会话"""
    try:
        state = await service.start_session(session_id)
        return CrewSessionStatusResponse(
            session_id=state.session_id,
            status=state.status,
            current_stage=state.current_stage,
            progress_percent=state.progress_percent,
            questions_asked=state.questions_asked,
            answers_received=state.answers_received,
            evaluations_count=state.evaluations_count,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Failed to start crew session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start session: {str(e)}",
        )


@router.get(
    "/sessions/{session_id}/status",
    response_model=CrewSessionStatusResponse,
    summary="获取会话状态",
    description="获取 Crew 面试会话的当前状态",
)
async def get_session_status(
    session_id: str,
    current_user: dict = Depends(get_current_user),
    service: InterviewCrewService = Depends(get_crew_service),
) -> CrewSessionStatusResponse:
    """获取会话状态"""
    state = service.get_session_state(session_id)
    if not state:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session not found: {session_id}",
        )

    # 获取进度信息
    progress = service.get_session_progress(session_id)

    return CrewSessionStatusResponse(
        session_id=state.session_id,
        status=state.status,
        current_stage=progress.get("current_stage", state.current_stage),
        progress_percent=progress.get("progress_percent", state.progress_percent),
        questions_asked=state.questions_asked,
        answers_received=state.answers_received,
        evaluations_count=state.evaluations_count,
        duration=progress.get("duration"),
    )


@router.post(
    "/sessions/{session_id}/questions",
    response_model=GenerateQuestionResponse,
    summary="生成面试问题",
    description="生成下一个面试问题",
)
async def generate_question(
    session_id: str,
    current_user: dict = Depends(get_current_user),
    service: InterviewCrewService = Depends(get_crew_service),
) -> GenerateQuestionResponse:
    """生成面试问题"""
    try:
        result = await service.generate_question(session_id)
        return GenerateQuestionResponse(**result)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Failed to generate question: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate question: {str(e)}",
        )


@router.post(
    "/sessions/{session_id}/answers",
    response_model=ProcessAnswerResponse,
    summary="提交回答",
    description="提交候选人的回答并获取评估",
)
async def process_answer(
    session_id: str,
    request: ProcessAnswerRequest,
    current_user: dict = Depends(get_current_user),
    service: InterviewCrewService = Depends(get_crew_service),
) -> ProcessAnswerResponse:
    """处理候选人回答"""
    try:
        result = await service.process_answer(
            session_id=session_id,
            answer=request.answer,
            answer_type=request.answer_type,
        )
        return ProcessAnswerResponse(**result)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Failed to process answer: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process answer: {str(e)}",
        )


@router.get(
    "/sessions/{session_id}/coaching",
    response_model=CoachingResponse,
    summary="获取学习建议",
    description="获取基于面试表现的学习建议",
)
async def get_coaching(
    session_id: str,
    current_user: dict = Depends(get_current_user),
    service: InterviewCrewService = Depends(get_crew_service),
) -> CoachingResponse:
    """获取学习建议"""
    try:
        result = await service.generate_coaching(session_id)
        return CoachingResponse(**result)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Failed to generate coaching: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate coaching: {str(e)}",
        )


@router.post(
    "/sessions/{session_id}/learning-plan",
    response_model=LearningPlanResponse,
    summary="生成学习计划",
    description="基于面试表现生成个性化学习计划",
)
async def generate_learning_plan(
    session_id: str,
    request: LearningPlanRequest,
    current_user: dict = Depends(get_current_user),
    service: InterviewCrewService = Depends(get_crew_service),
) -> LearningPlanResponse:
    """生成学习计划"""
    try:
        result = await service.generate_learning_plan(
            session_id=session_id,
            target_position=request.target_position,
            available_time=request.available_time,
        )
        return LearningPlanResponse(**result)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Failed to generate learning plan: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate learning plan: {str(e)}",
        )


@router.post(
    "/sessions/{session_id}/end",
    response_model=FinalReportResponse,
    summary="结束面试会话",
    description="结束 Crew 面试会话并生成最终报告",
)
async def end_session(
    session_id: str,
    current_user: dict = Depends(get_current_user),
    service: InterviewCrewService = Depends(get_crew_service),
) -> FinalReportResponse:
    """结束面试会话"""
    try:
        result = await service.end_session(session_id)
        return FinalReportResponse(**result)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Failed to end session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to end session: {str(e)}",
        )


@router.post(
    "/sessions/{session_id}/pause",
    response_model=CrewSessionStatusResponse,
    summary="暂停会话",
    description="暂停正在进行的面试会话",
)
async def pause_session(
    session_id: str,
    current_user: dict = Depends(get_current_user),
    service: InterviewCrewService = Depends(get_crew_service),
) -> CrewSessionStatusResponse:
    """暂停会话"""
    try:
        state = service.pause_session(session_id)
        return CrewSessionStatusResponse(
            session_id=state.session_id,
            status=state.status,
            current_stage=state.current_stage,
            progress_percent=state.progress_percent,
            questions_asked=state.questions_asked,
            answers_received=state.answers_received,
            evaluations_count=state.evaluations_count,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.post(
    "/sessions/{session_id}/resume",
    response_model=CrewSessionStatusResponse,
    summary="恢复会话",
    description="恢复已暂停的面试会话",
)
async def resume_session(
    session_id: str,
    current_user: dict = Depends(get_current_user),
    service: InterviewCrewService = Depends(get_crew_service),
) -> CrewSessionStatusResponse:
    """恢复会话"""
    try:
        state = service.resume_session(session_id)
        return CrewSessionStatusResponse(
            session_id=state.session_id,
            status=state.status,
            current_stage=state.current_stage,
            progress_percent=state.progress_percent,
            questions_asked=state.questions_asked,
            answers_received=state.answers_received,
            evaluations_count=state.evaluations_count,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.get(
    "/scenarios",
    response_model=ScenariosListResponse,
    summary="获取可用场景",
    description="获取所有可用的 Crew 面试场景",
)
async def list_scenarios(
    current_user: dict = Depends(get_current_user),
    service: InterviewCrewService = Depends(get_crew_service),
) -> ScenariosListResponse:
    """获取可用场景列表"""
    try:
        scenarios = await service.get_available_scenarios()
        return ScenariosListResponse(
            scenarios=[ScenarioInfo(**s) for s in scenarios],
            total=len(scenarios),
        )
    except Exception as e:
        logger.error(f"Failed to list scenarios: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list scenarios: {str(e)}",
        )


@router.get(
    "/sessions",
    response_model=list[CrewSessionStatusResponse],
    summary="获取活动会话列表",
    description="获取当前用户的所有活动 Crew 会话",
)
async def list_active_sessions(
    current_user: dict = Depends(get_current_user),
    service: InterviewCrewService = Depends(get_crew_service),
) -> list[CrewSessionStatusResponse]:
    """获取活动会话列表"""
    sessions = service.list_active_sessions()
    # 过滤当前用户的会话
    user_sessions = [s for s in sessions if s.user_id == current_user["user_id"]]

    return [
        CrewSessionStatusResponse(
            session_id=s.session_id,
            status=s.status,
            current_stage=s.current_stage,
            progress_percent=s.progress_percent,
            questions_asked=s.questions_asked,
            answers_received=s.answers_received,
            evaluations_count=s.evaluations_count,
        )
        for s in user_sessions
    ]
