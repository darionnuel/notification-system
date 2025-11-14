"""Core email service with business logic."""
from datetime import datetime
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from app.models.email_log import EmailLog, EmailStatus
from app.schemas.email import EmailNotificationRequest, EmailStatsResponse
from app.services.template_client import template_client
from app.services.smtp_service import smtp_service
from app.services.queue_service import queue_service
from app.utils.retry import retry_with_backoff
from app.utils.correlation import get_correlation_id, set_correlation_id


class EmailService:
    """Service for processing email notifications."""
    
    async def process_notification(
        self,
        request: EmailNotificationRequest,
        db: Session,
        correlation_id: Optional[str] = None
    ) -> EmailLog:
        """
        Process email notification request from queue.
        
        Args:
            request: Email notification request
            db: Database session
            correlation_id: Request correlation ID
            
        Returns:
            EmailLog entry
        """
        # Set correlation ID for tracking
        if correlation_id:
            set_correlation_id(correlation_id)
        
        # Check for duplicate request (idempotency)
        existing = db.query(EmailLog).filter(
            EmailLog.request_id == request.request_id
        ).first()
        
        if existing:
            print(f"⚠️ Duplicate request_id: {request.request_id}, skipping")
            return existing
        
        # Extract recipient info from metadata
        metadata = request.metadata or {}
        recipient_email = metadata.get("recipient_email")
        recipient_name = metadata.get("recipient_name")
        language = metadata.get("language", "en")
        
        if not recipient_email:
            raise ValueError("recipient_email is required in metadata")
        
        # Prepare extra metadata for storage
        import json
        extra_metadata = json.dumps({
            "language": language,
            "from_email": metadata.get("from_email"),
            "from_name": metadata.get("from_name"),
            "reply_to": metadata.get("reply_to"),
            "cc": metadata.get("cc"),
            "bcc": metadata.get("bcc"),
            "provider": metadata.get("provider"),
        })
        
        # Create email log entry
        email_log = EmailLog(
            notification_id=request.notification_id,
            request_id=request.request_id,
            correlation_id=correlation_id or get_correlation_id(),
            user_id=request.user_id,
            template_code=request.template_code,
            recipient_email=recipient_email,
            recipient_name=recipient_name,
            priority=request.priority,
            status=EmailStatus.PENDING,
            extra_metadata=extra_metadata,
        )
        
        db.add(email_log)
        db.commit()
        db.refresh(email_log)
        
        # Process email asynchronously
        try:
            await self._send_email(email_log, request, db)
        except Exception as e:
            print(f"❌ Error sending email: {e}")
            self._update_email_status(
                email_log,
                EmailStatus.FAILED,
                error_message=str(e),
                db=db
            )
        
        return email_log
    
    async def _send_email(
        self,
        email_log: EmailLog,
        request: EmailNotificationRequest,
        db: Session
    ):
        """
        Send email with retry logic.
        
        Args:
            email_log: Email log entry
            request: Email notification request
            db: Database session
        """
        # Update status to SENDING
        self._update_email_status(email_log, EmailStatus.SENDING, db=db)
        
        # Publish status update
        await queue_service.publish_status_update(
            notification_id=request.notification_id,
            status="SENDING",
            correlation_id=email_log.correlation_id,
        )
        
        # Extract metadata
        metadata = request.metadata or {}
        language = metadata.get("language", "en")
        recipient_email = metadata.get("recipient_email")
        from_email = metadata.get("from_email")
        from_name = metadata.get("from_name")
        reply_to = metadata.get("reply_to")
        cc = metadata.get("cc")
        bcc = metadata.get("bcc")
        provider = metadata.get("provider")
        
                # Fetch and render template with retry
        async def _fetch_template():
            return await template_client.render_email_template(
                template_code=request.template_code,
                variables=request.variables,
                language=language
            )
        
        subject, html_content = await retry_with_backoff(_fetch_template)
        
        # Update email log with rendered content
        email_log.subject = subject
        email_log.body_html = html_content
        db.commit()
        
        # Send email with retry
        async def _send_email():
            return await smtp_service.send_email(
                to_email=recipient_email,
                subject=subject,
                html_content=html_content,
                from_email=from_email,
                from_name=from_name,
                reply_to=reply_to,
                cc=cc,
                bcc=bcc,
                provider=provider
            )
        
        result = await retry_with_backoff(_send_email)
        
        # Update status to SENT
        self._update_email_status(
            email_log,
            EmailStatus.SENT,
            provider=result.get("provider"),
            metadata=result,
            db=db
        )
        
        # Publish success status
        await queue_service.publish_status_update(
            notification_id=request.notification_id,
            status="SENT",
            correlation_id=email_log.correlation_id,
            metadata={"provider": result.get("provider")}
        )
        
        print(f"✅ Email sent successfully: {request.notification_id}")
    
    def _update_email_status(
        self,
        email_log: EmailLog,
        status: EmailStatus,
        error_message: Optional[str] = None,
        provider: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        db: Session = None
    ):
        """
        Update email log status.
        
        Args:
            email_log: Email log entry
            status: New status
            error_message: Error message if failed
            provider: Email provider used
            metadata: Additional metadata
            db: Database session
        """
        email_log.status = status
        
        if error_message:
            email_log.error_message = error_message
            email_log.retry_count += 1
        
        if provider:
            email_log.provider = provider
        
        if metadata:
            email_log.extra_metadata = metadata
        
        # Update timestamps
        if status == EmailStatus.SENDING:
            email_log.sent_at = datetime.utcnow()
        elif status == EmailStatus.SENT:
            email_log.delivered_at = datetime.utcnow()
        elif status == EmailStatus.FAILED:
            email_log.failed_at = datetime.utcnow()
        
        if db:
            db.commit()
    
    def get_email_log(self, notification_id: str, db: Session) -> Optional[EmailLog]:
        """
        Get email log by notification ID.
        
        Args:
            notification_id: Notification ID
            db: Database session
            
        Returns:
            EmailLog or None
        """
        return db.query(EmailLog).filter(
            EmailLog.notification_id == notification_id
        ).first()
    
    def get_email_logs(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> tuple[list[EmailLog], int]:
        """
        Get email logs with pagination and filters.
        
        Args:
            db: Database session
            skip: Number of records to skip
            limit: Max records to return
            status: Filter by status
            user_id: Filter by user ID
            
        Returns:
            Tuple of (email_logs, total_count)
        """
        query = db.query(EmailLog)
        
        if status:
            query = query.filter(EmailLog.status == status)
        
        if user_id:
            query = query.filter(EmailLog.user_id == user_id)
        
        total = query.count()
        logs = query.order_by(EmailLog.created_at.desc()).offset(skip).limit(limit).all()
        
        return logs, total
    
    def get_email_stats(self, db: Session) -> EmailStatsResponse:
        """
        Get email sending statistics.
        
        Args:
            db: Database session
            
        Returns:
            Email statistics
        """
        total_emails = db.query(EmailLog).count()
        
        pending = db.query(EmailLog).filter(
            EmailLog.status == EmailStatus.PENDING
        ).count()
        
        sent = db.query(EmailLog).filter(
            EmailLog.status == EmailStatus.SENT
        ).count()
        
        delivered = db.query(EmailLog).filter(
            EmailLog.status == EmailStatus.DELIVERED
        ).count()
        
        failed = db.query(EmailLog).filter(
            EmailLog.status == EmailStatus.FAILED
        ).count()
        
        bounced = db.query(EmailLog).filter(
            EmailLog.status == EmailStatus.BOUNCED
        ).count()
        
        return EmailStatsResponse(
            total_emails=total_emails,
            pending=pending,
            sent=sent,
            delivered=delivered,
            failed=failed,
            bounced=bounced
        )


# Global instance
email_service = EmailService()
