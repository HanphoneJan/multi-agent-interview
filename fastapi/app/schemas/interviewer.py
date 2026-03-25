"""Interviewer customization schemas"""
from typing import Optional, Literal
from pydantic import BaseModel, Field


class InterviewerSettings(BaseModel):
    """Interviewer customization settings"""
    gender: Literal["male", "female"] = Field(default="male", description="面试官性别")
    speed: int = Field(default=3, ge=1, le=5, description="语速 1-5")
    voice: Literal["standard", "deep", "clear", "soft", "passionate", "magnetic"] = Field(
        default="standard", description="音色类型"
    )
    style: Literal["serious", "friendly", "challenging", "guiding", "technical", "boss"] = Field(
        default="serious", description="面试风格"
    )


class InterviewerSettingsResponse(BaseModel):
    """Interviewer settings response"""
    gender: str
    speed: int
    voice: str
    style: str


class InterviewerSettingsUpdate(BaseModel):
    """Interviewer settings update request"""
    gender: Optional[Literal["male", "female"]] = None
    speed: Optional[int] = Field(None, ge=1, le=5)
    voice: Optional[Literal["standard", "deep", "clear", "soft", "passionate", "magnetic"]] = None
    style: Optional[Literal["serious", "friendly", "challenging", "guiding", "technical", "boss"]] = None
