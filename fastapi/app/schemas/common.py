"""Common schemas"""
from typing import Any, Generic, List, TypeVar
from pydantic import BaseModel, Field, ConfigDict


T = TypeVar('T')


class BaseResponse(BaseModel):
    """Base response schema"""
    success: bool = True
    message: str = "Success"


class ErrorResponse(BaseModel):
    """Error response schema"""
    success: bool = False
    error: str
    detail: str | None = None
    error_code: str | None = None


class MessageResponse(BaseModel):
    """Simple message response schema"""
    success: bool = True
    message: str
    data: Any | None = None


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated response schema"""
    items: List[T]
    total: int
    page: int
    page_size: int
    total_pages: int

    model_config = ConfigDict(arbitrary_types_allowed=True)


class PaginationParams(BaseModel):
    """Pagination parameters"""
    page: int = Field(1, ge=1, description="Page number")
    page_size: int = Field(10, ge=1, le=100, description="Items per page")

    @property
    def skip(self) -> int:
        return (self.page - 1) * self.page_size
