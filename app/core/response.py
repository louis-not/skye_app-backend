from typing import TypeVar, Generic, Optional, Any
from pydantic import BaseModel
from datetime import datetime, timezone
import uuid


T = TypeVar("T")


class ErrorDetail(BaseModel):
    """Error detail model for API responses."""

    code: str
    message: str
    details: Optional[Any] = None


class ResponseMeta(BaseModel):
    """Metadata for API responses."""

    timestamp: datetime
    request_id: str


class APIResponse(BaseModel, Generic[T]):
    """Standardized API response wrapper for Android clients.

    All API responses follow this structure for consistency:
    {
        "success": true/false,
        "data": { ... } or null,
        "error": { ... } or null,
        "meta": { "timestamp": "...", "request_id": "..." }
    }
    """

    success: bool
    data: Optional[T] = None
    error: Optional[ErrorDetail] = None
    meta: ResponseMeta

    @classmethod
    def ok(cls, data: T, request_id: Optional[str] = None) -> "APIResponse[T]":
        """Create a successful response."""
        return cls(
            success=True,
            data=data,
            error=None,
            meta=ResponseMeta(
                timestamp=datetime.now(timezone.utc),
                request_id=request_id or str(uuid.uuid4()),
            ),
        )

    @classmethod
    def fail(
        cls,
        code: str,
        message: str,
        details: Optional[Any] = None,
        request_id: Optional[str] = None,
    ) -> "APIResponse[None]":
        """Create a failed response."""
        return cls(
            success=False,
            data=None,
            error=ErrorDetail(code=code, message=message, details=details),
            meta=ResponseMeta(
                timestamp=datetime.now(timezone.utc),
                request_id=request_id or str(uuid.uuid4()),
            ),
        )


class CursorPagination(BaseModel):
    """Cursor-based pagination metadata for mobile infinite scroll."""

    next_cursor: Optional[str] = None
    has_more: bool = False


class PaginatedData(BaseModel, Generic[T]):
    """Paginated data wrapper."""

    items: list[T]
    pagination: CursorPagination
