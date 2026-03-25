"""Evaluation schemas"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


class AnswerEvaluationResponse(BaseModel):
    """Answer evaluation response schema"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    question_id: int
    evaluation_text: str
    score: float
    evaluated_at: datetime


class ResumeEvaluationCreate(BaseModel):
    """Resume evaluation creation schema"""
    resume_file: bytes = Field(..., description="Resume file content")
    user_id: int


class ResumeEvaluationResponse(BaseModel):
    """Resume evaluation response schema"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    resume_score: str
    resume_summary: Optional[str]
    created_at: datetime


class OverallInterviewEvaluationCreate(BaseModel):
    """Overall interview evaluation creation schema"""
    session_id: int
    user_id: int
    overall_evaluation: str
    help: str
    recommendation: str = ""
    overall_score: int = 0
    professional_knowledge: int = 0
    skill_match: int = 0
    language_expression: int = 0
    logical_thinking: int = 0
    stress_response: int = 0
    personality: int = 0
    motivation: int = 0
    value: int = 0


class OverallInterviewEvaluationResponse(BaseModel):
    """Overall interview evaluation response schema"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    session_id: int
    user_id: int
    overall_evaluation: str
    help: str
    recommendation: str
    overall_score: int
    professional_knowledge: int
    skill_match: int
    language_expression: int
    logical_thinking: int
    stress_response: int
    personality: int
    motivation: int
    value: int
    created_at: datetime


class FacialAnalysisRequest(BaseModel):
    """Facial analysis request schema"""
    image_data: str = Field(..., description="Base64 encoded image")


class FacialAnalysisResponse(BaseModel):
    """Facial analysis response schema"""
    expression: str
    emotion: str
    confidence: float
    timestamp: datetime
