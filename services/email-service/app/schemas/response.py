"""Shared response models."""
from pydantic import BaseModel
from typing import Optional, Any, TypeVar, Generic


class PaginationMeta(BaseModel):
    """Pagination metadata for list responses."""
    total: int
    limit: int
    page: int
    total_pages: int
    has_next: bool
    has_previous: bool


T = TypeVar('T')


class ApiResponse(BaseModel, Generic[T]):
    """Standard API response format."""
    success: bool
    message: str
    data: Optional[T] = None
    error: Optional[str] = None
    meta: Optional[PaginationMeta] = None
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "success": True,
                    "message": "Operation successful",
                    "data": {"key": "value"},
                    "error": None,
                    "meta": None
                }
            ]
        }
    }
