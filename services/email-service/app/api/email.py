from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.response import ApiResponse, PaginationMeta
from app.schemas.email import (
    EmailSendRequest,
    EmailLogResponse,
    EmailLogListResponse,
    EmailStatsResponse,
    EmailNotificationRequest,
    NotificationType
)
from app.services.email_service import email_service
from app.models.email_log import EmailLog


router = APIRouter(prefix="/api/v1/emails", tags=["emails"])


@router.get("/health", response_model=ApiResponse)
async def health_check():
    """Health check endpoint."""
    return ApiResponse(
        success=True,
        message="Email Service is healthy",
        data={"status": "ok"}
    )


@router.post("/send", response_model=ApiResponse[EmailLogResponse])
async def send_email(
    request: EmailSendRequest,
    db: Session = Depends(get_db)
):
    """
    Send email directly (for testing/manual sending).
    
    This endpoint allows manual email sending for testing purposes.
    In production, emails should be sent via RabbitMQ queue.
    
    **Minimal Example:**
    ```json
    {
        "recipient_email": "user@example.com",
        "template_code": "welcome_email",
        "variables": {
            "first_name": "John",
            "last_name": "Doe"
        }
    }
    ```
    
    **Full Example:**
    ```json
    {
        "recipient_email": "user@example.com",
        "recipient_name": "John Doe",
        "template_code": "welcome_email",
        "variables": {
            "first_name": "John",
            "activation_link": "https://example.com/activate"
        },
        "priority": 5,
        "language": "en"
    }
    ```
    """
    import uuid
    
    # Generate IDs if not provided
    notification_id = request.notification_id or str(uuid.uuid4())
    request_id = request.request_id or notification_id
    
    # Convert to EmailNotificationRequest
    notification_request = EmailNotificationRequest(
        notification_id=notification_id,
        notification_type=NotificationType.EMAIL,
        user_id=request.user_id,
        template_code=request.template_code,
        variables=request.variables,
        request_id=request_id,
        priority=request.priority,
        metadata={
            "recipient_email": request.recipient_email,
            "recipient_name": request.recipient_name,
            "language": request.language,
            "from_email": request.from_email,
            "from_name": request.from_name,
            "reply_to": request.reply_to,
            "cc": request.cc,
            "bcc": request.bcc,
            "provider": request.provider,
        }
    )
    
    # Process email
    email_log = await email_service.process_notification(
        notification_request,
        db
    )
    
    return ApiResponse(
        success=True,
        message="Email sent successfully",
        data=EmailLogResponse.model_validate(email_log)
    )


@router.get("/{notification_id}", response_model=ApiResponse[EmailLogResponse])
async def get_email_status(
    notification_id: str,
    db: Session = Depends(get_db)
):
    """
    Get email status by notification ID.
    
    Args:
        notification_id: Notification ID
    """
    email_log = email_service.get_email_log(notification_id, db)
    
    if not email_log:
        raise HTTPException(status_code=404, detail="Email not found")
    
    return ApiResponse(
        success=True,
        message="Email found",
        data=EmailLogResponse.model_validate(email_log)
    )


@router.get("/", response_model=ApiResponse[EmailLogListResponse])
async def list_emails(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Max records to return"),
    status: Optional[str] = Query(None, description="Filter by status"),
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    db: Session = Depends(get_db)
):
    """
    List email logs with pagination and filters.
    
    Args:
        skip: Number of records to skip
        limit: Max records to return
        status: Filter by status (PENDING, SENDING, SENT, DELIVERED, FAILED)
        user_id: Filter by user ID
    """
    logs, total = email_service.get_email_logs(
        db,
        skip=skip,
        limit=limit,
        status=status,
        user_id=user_id
    )
    
    items = [EmailLogResponse.model_validate(log) for log in logs]
    
    current_page = skip // limit + 1
    total_pages = (total + limit - 1) // limit
    
    list_response = EmailLogListResponse(
        items=items,
        total=total,
        page=current_page,
        page_size=limit,
        total_pages=total_pages
    )
    
    return ApiResponse(
        success=True,
        message=f"Found {len(items)} emails",
        data=list_response
    )


@router.get("/stats/summary", response_model=ApiResponse[EmailStatsResponse])
async def get_email_stats(db: Session = Depends(get_db)):
    """
    Get email sending statistics.
    
    Returns aggregated statistics about email sending.
    """
    stats = email_service.get_email_stats(db)
    
    return ApiResponse(
        success=True,
        message="Email statistics retrieved",
        data=stats
    )


@router.post("/{notification_id}/retry", response_model=ApiResponse[EmailLogResponse])
async def retry_failed_email(
    notification_id: str,
    db: Session = Depends(get_db)
):
    """
    Retry sending a failed email.
    
    Args:
        notification_id: Notification ID to retry
    """
    email_log = email_service.get_email_log(notification_id, db)
    
    if not email_log:
        raise HTTPException(status_code=404, detail="Email not found")
    
    # Check if email can be retried (FAILED or BOUNCED status)
    from app.schemas.email import EmailStatus
    if email_log.status not in [EmailStatus.FAILED, EmailStatus.BOUNCED]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot retry email with status: {email_log.status.value}"
        )
    
    # Extract metadata from email log
    import json
    extra_metadata = json.loads(email_log.extra_metadata) if email_log.extra_metadata else {}
    
    # Convert to EmailNotificationRequest for retry
    notification_request = EmailNotificationRequest(
        notification_id=email_log.notification_id,
        notification_type=NotificationType.EMAIL,
        user_id=email_log.user_id,
        template_code=email_log.template_code,
        variables={},  # Template already rendered, we have subject and html_content
        request_id=f"{email_log.request_id}_retry_{email_log.retry_count + 1}",
        priority=email_log.priority,
        metadata={
            "recipient_email": email_log.recipient_email,
            "recipient_name": email_log.recipient_name,
            "language": extra_metadata.get("language", "en"),
            "from_email": extra_metadata.get("from_email"),
            "from_name": extra_metadata.get("from_name"),
            "reply_to": extra_metadata.get("reply_to"),
            "cc": extra_metadata.get("cc"),
            "bcc": extra_metadata.get("bcc"),
            "provider": extra_metadata.get("provider"),
        }
    )
    
    # Process retry
    email_log = await email_service.process_notification(
        notification_request,
        db,
        correlation_id=email_log.correlation_id
    )
    
    return ApiResponse(
        success=True,
        message="Email retry initiated",
        data=EmailLogResponse.model_validate(email_log)
    )
