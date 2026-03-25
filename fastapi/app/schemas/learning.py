"""Learning schemas"""
from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field, ConfigDict

from app.core.constants import ResourceType, Difficulty


class ResourceBase(BaseModel):
    """Base resource schema"""
    name: str = Field(..., max_length=200)
    resource_type: ResourceType
    tags: List[str] = Field(default_factory=list)
    url: str = Field(..., max_length=500)
    duration_or_quantity: str = Field(..., max_length=50)
    difficulty: Optional[Difficulty] = None


class ResourceCreate(ResourceBase):
    """Resource creation schema"""


class ResourceUpdate(BaseModel):
    """Resource update schema"""
    name: Optional[str] = Field(None, max_length=200)
    tags: Optional[List[str]] = Field(None)
    url: Optional[str] = Field(None, max_length=500)
    duration_or_quantity: Optional[str] = Field(None, max_length=50)
    difficulty: Optional[Difficulty] = None


class ResourceResponse(ResourceBase):
    """Resource response schema"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    views: int
    completions: int
    rating: float
    rating_count: int
    created_at: datetime
    updated_at: datetime


class QuestionBase(BaseModel):
    """Base question schema"""
    question_id: int
    resource_id: int
    name: str = Field(default="", max_length=200)
    pass_rate: str
    solution_url: str = Field(default="", max_length=500)
    question_url: str = Field(default="", max_length=500)
    difficulty: Difficulty = Field(default=Difficulty.MEDIUM)


class QuestionCreate(QuestionBase):
    """Question creation schema"""


class QuestionUpdate(BaseModel):
    """Question update schema"""
    pass_rate: Optional[str] = None
    solution_url: Optional[str] = Field(None, max_length=500)
    question_url: Optional[str] = Field(None, max_length=500)
    difficulty: Optional[Difficulty] = None


class QuestionResponse(QuestionBase):
    """Question response schema"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    resource: ResourceResponse
    created_at: datetime
    updated_at: datetime


class RecommendationResponse(BaseModel):
    """Recommendation response schema"""
    id: int
    name: str
    resource_type: ResourceType
    tags: List[str]
    difficulty: Optional[Difficulty]
    score: float
    reason: str
    created_at: datetime


class UserResourceInteractionCreate(BaseModel):
    """User resource interaction creation schema"""
    resource_id: int
    interaction_type: str = Field(..., pattern=r'^(view|complete|rate)$')
    value: float = Field(default=0.0)
