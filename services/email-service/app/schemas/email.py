"""Email schemas for request/response validation."""
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum


class NotificationType(str, Enum):
    """Notification types."""
    EMAIL = "email"
    PUSH = "push"


class EmailStatus(str, Enum):
    """Email delivery status."""
    PENDING = "pending"
    SENDING = "sending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    BOUNCED = "bounced"


# Request Schemas

class EmailNotificationRequest(BaseModel):
    """Schema for email notification request from queue."""
    notification_id: str = Field(..., description="Unique notification ID")
    notification_type: NotificationType = Field(..., description="Type of notification")
    user_id: str = Field(..., description="User ID")
    template_code: str = Field(..., description="Template code to use")
    variables: Dict[str, Any] = Field(..., description="Variables for template rendering")
    request_id: str = Field(..., description="Unique request ID for idempotency")
    priority: int = Field(default=1, ge=1, le=10, description="Priority (1-10)")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    correlation_id: Optional[str] = Field(None, description="Correlation ID for tracing")


class EmailSendRequest(BaseModel):
    """
    Schema for direct email send request (REST API).
    
    Minimal required fields: recipient_email, template_code, variables
    All other fields have sensible defaults.
    
    Example:
    {
        "recipient_email": "user@example.com",
        "recipient_name": "John Doe",
        "template_code": "welcome_email",
        "variables": {
            "user_name": "John",
            "user_email": "john@example.com",
            "activation_link": "https://example.com/activate",
            "app_name": "MyApp"
        }
    }
    """
    model_config = ConfigDict(extra='forbid', json_schema_extra={
        "example": {
            "recipient_email": "user@example.com",
            "template_code": "welcome_email",
            "variables": {
                "first_name": "John",
                "last_name": "Doe",
                "app_name": "MyApp",
                "activation_link": "https://example.com/activate/abc123"
            }
        }
    })
    
    # Required fields
    recipient_email: EmailStr = Field(..., description="Recipient email address")
    template_code: str = Field(..., description="Template code to use")
    variables: Dict[str, Any] = Field(..., description="Variables for template rendering")
    
    # Optional fields with defaults
    recipient_name: Optional[str] = Field(None, description="Recipient name")
    user_id: str = Field(default="anonymous", description="User ID (defaults to 'anonymous' for testing)")
    notification_id: Optional[str] = Field(None, description="Notification ID (auto-generated if not provided)")
    request_id: Optional[str] = Field(None, description="Request ID for idempotency (auto-generated if not provided)")
    priority: int = Field(default=1, ge=1, le=10, description="Priority (1-10, default is 1)")
    language: str = Field(default="en", description="Language code (e.g., 'en', 'fr')")
    
    # Email configuration (optional)
    from_email: Optional[str] = Field(None, description="Custom sender email (uses default if not provided)")
    from_name: Optional[str] = Field(None, description="Custom sender name")
    reply_to: Optional[str] = Field(None, description="Reply-to email address")
    cc: Optional[list[str]] = Field(None, description="CC recipients")
    bcc: Optional[list[str]] = Field(None, description="BCC recipients")
    provider: Optional[str] = Field(None, description="Email provider to use (smtp/sendgrid, auto-selected if not provided)")
    provider: Optional[str] = Field(None, description="Email provider to use (smtp/sendgrid, auto-selected if not provided)")


class EmailStatusUpdate(BaseModel):
    """Schema for email status update."""
    notification_id: str = Field(..., description="Notification ID")
    status: EmailStatus = Field(..., description="Email status")
    timestamp: Optional[datetime] = Field(None, description="Status update timestamp")
    error: Optional[str] = Field(None, description="Error message if failed")


# Response Schemas

class EmailLogResponse(BaseModel):
    """Schema for email log response."""
    id: str
    notification_id: str
    request_id: str
    user_id: str
    template_code: str
    recipient_email: str
    recipient_name: Optional[str]
    subject: Optional[str]
    status: EmailStatus
    priority: int
    created_at: datetime
    sent_at: Optional[datetime]
    delivered_at: Optional[datetime]
    failed_at: Optional[datetime]
    error_message: Optional[str]
    retry_count: int
    provider: Optional[str]
    correlation_id: Optional[str]
    
    model_config = {
        "from_attributes": True
    }


class EmailLogListResponse(BaseModel):
    """Schema for paginated email log list response."""
    items: list[EmailLogResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class EmailStatsResponse(BaseModel):
    """Schema for email statistics response."""
    total_emails: int
    pending: int
    sent: int
    delivered: int
    failed: int
    bounced: int
