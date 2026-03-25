"""Interview schemas"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict

from app.core.constants import InterviewSessionStatus


class InterviewScenarioBase(BaseModel):
    """Base interview scenario schema"""
    name: str = Field(..., max_length=200)
    technology_field: str = Field(default="通用", max_length=200)
    description: str = Field(default="")
    requirements: str = Field(default="")
    is_realtime: bool = Field(default=True)


class InterviewScenarioCreate(InterviewScenarioBase):
    """Interview scenario creation schema"""


class InterviewScenarioUpdate(BaseModel):
    """Interview scenario update schema"""
    name: Optional[str] = Field(None, max_length=200)
    technology_field: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    requirements: Optional[str] = None
    is_realtime: Optional[bool] = None


class InterviewScenarioResponse(InterviewScenarioBase):
    """Interview scenario response schema"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


class InterviewSessionBase(BaseModel):
    """Base interview session schema"""
    scenario_id: int


class InterviewSessionCreate(InterviewSessionBase):
    """Interview session creation schema"""


class InterviewSessionUpdate(BaseModel):
    """Interview session update schema"""
    status: Optional[InterviewSessionStatus] = None
    is_finished: Optional[bool] = None


class InterviewSessionResponse(BaseModel):
    """Interview session response schema"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    scenario_id: int
    scenario: InterviewScenarioResponse
    start_time: datetime
    end_time: Optional[datetime]
    total_questions: int
    is_finished: bool
    status: InterviewSessionStatus
    paused_at: Optional[datetime] = None
    resumed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class InterviewQuestionBase(BaseModel):
    """Base interview question schema"""
    question_text: str
    question_number: int


class InterviewQuestionCreate(InterviewQuestionBase):
    """Interview question creation schema"""


class InterviewQuestionResponse(InterviewQuestionBase):
    """Interview question response schema"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    session_id: int
    asked_at: datetime  # maps to created_at from DB
