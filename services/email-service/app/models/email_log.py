"""Email log database model."""
from sqlalchemy import Column, String, Integer, DateTime, Text, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid
import enum

from app.db.session import Base


class EmailStatus(str, enum.Enum):
    """Email delivery status."""
    PENDING = "pending"
    SENDING = "sending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    BOUNCED = "bounced"


class EmailLog(Base):
    """Email log model for tracking sent emails."""
    
    __tablename__ = "email_logs"
    
    # Primary key
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Tracking IDs
    notification_id = Column(String(36), nullable=False, index=True)
    request_id = Column(String(255), unique=True, nullable=False, index=True)  # For idempotency
    correlation_id = Column(String(255), index=True)  # For distributed tracing
    
    # User and template info
    user_id = Column(String(36), nullable=False, index=True)
    template_code = Column(String(100), nullable=False)
    
    # Email details
    recipient_email = Column(String(255), nullable=False, index=True)
    recipient_name = Column(String(255))
    subject = Column(String(500))
    body_html = Column(Text)
    body_text = Column(Text, nullable=True)
    
    # Status tracking
    status = Column(SQLEnum(EmailStatus), default=EmailStatus.PENDING, nullable=False, index=True)
    priority = Column(Integer, default=1)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    sent_at = Column(DateTime, nullable=True)
    delivered_at = Column(DateTime, nullable=True)
    failed_at = Column(DateTime, nullable=True)
    
    # Error handling
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)
    last_retry_at = Column(DateTime, nullable=True)
    
    # Provider info
    provider = Column(String(50))  # gmail, sendgrid, etc.
    provider_message_id = Column(String(255), nullable=True)  # External provider's message ID
    
    # Additional data
    extra_metadata = Column(Text, nullable=True)  # JSON string for additional data
    
    def __repr__(self):
        return f"<EmailLog(id={self.id}, recipient={self.recipient_email}, status={self.status})>"
