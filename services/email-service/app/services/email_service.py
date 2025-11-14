"""Core email service with business logic."""
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from app.models.email_log import EmailLog, EmailStatus
from app.schemas.email import EmailNotificationRequest, EmailStatsResponse
from app.services.user_client import user_client
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
        
        Worker-fetch pattern:
        1. Fetch user details from User Service using user_id
        2. Check user preferences (email enabled?)
        3. Fetch template from Template Service using template_code
        4. Render template with variables
        5. Send email
        
        Args:
            request: Email notification request (contains only references)
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
        
        print(f"📨 Processing notification {request.notification_id} for user {request.user_id}")
        
        # 1. Fetch user data from User Service with retry
        try:
            last_exception = None
            for attempt in range(3):
                try:
                    user_data = await user_client.get_user_by_id(request.user_id)
                    print(f"✅ Fetched user data for {request.user_id}")
                    break
                except Exception as e:
                    last_exception = e
                    if attempt < 2:
                        wait_time = (2 ** attempt) * 2
                        print(f"User fetch attempt {attempt + 1}/3 failed: {e}. Retrying in {wait_time}s...")
                        await asyncio.sleep(wait_time)
                    else:
                        raise e
        except Exception as e:
            error_msg = f"Failed to fetch user {request.user_id}: {str(e)}"
            print(f"❌ {error_msg}")
            raise ValueError(error_msg)
        
        # 2. Extract user details
        recipient_email = user_client.extract_user_email(user_data)
        recipient_name = user_client.extract_user_name(user_data)
        language = user_client.extract_user_language(user_data)
        
        if not recipient_email:
            raise ValueError(f"User {request.user_id} has no email address")
        
        # 3. Check if user has email notifications enabled
        email_enabled = await user_client.check_email_preference(request.user_id)
        if not email_enabled:
            print(f"⚠️ User {request.user_id} has email notifications disabled, skipping")
            # Still create log entry but mark as skipped
            email_log = EmailLog(
                notification_id=request.notification_id,
                request_id=request.request_id,
                correlation_id=correlation_id or get_correlation_id(),
                user_id=request.user_id,
                template_code=request.template_code,
                recipient_email=recipient_email,
                recipient_name=recipient_name,
                priority=request.priority,
                status=EmailStatus.FAILED,
                error_message="User has email notifications disabled",
            )
            db.add(email_log)
            db.commit()
            db.refresh(email_log)
            return email_log
        
        # Extract optional email configuration from metadata
        metadata = request.metadata or {}
        from_email = metadata.get("from_email")
        from_name = metadata.get("from_name")
        reply_to = metadata.get("reply_to")
        cc = metadata.get("cc")
        bcc = metadata.get("bcc")
        provider = metadata.get("provider")
        
        # Prepare extra metadata for storage
        import json
        extra_metadata = json.dumps({
            "language": language,
            "from_email": from_email,
            "from_name": from_name,
            "reply_to": reply_to,
            "cc": cc,
            "bcc": bcc,
            "provider": provider,
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
            await self._send_email(
                email_log, 
                request, 
                db,
                recipient_email=recipient_email,
                language=language,
                from_email=from_email,
                from_name=from_name,
                reply_to=reply_to,
                cc=cc,
                bcc=bcc,
                provider=provider
            )
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
        db: Session,
        recipient_email: str,
        language: str,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None,
        reply_to: Optional[str] = None,
        cc: Optional[list] = None,
        bcc: Optional[list] = None,
        provider: Optional[str] = None
    ):
        """
        Send email with retry logic.
        
        Args:
            email_log: Email log entry
            request: Email notification request
            db: Database session
            recipient_email: Recipient email address
            language: User's preferred language
            from_email: Custom sender email (optional)
            from_name: Custom sender name (optional)
            reply_to: Reply-to address (optional)
            cc: CC recipients (optional)
            bcc: BCC recipients (optional)
            provider: Email provider (optional)
        """
        # Update status to SENDING
        self._update_email_status(email_log, EmailStatus.SENDING, db=db)
        
        # Publish status update
        await queue_service.publish_status_update(
            notification_id=request.notification_id,
            status="SENDING",
            correlation_id=email_log.correlation_id,
        )
        
        # Fetch and render template with retry
        print(f"📄 Fetching template: {request.template_code} (language: {language})")
        
        # Simple retry with manual loop (more reliable than retry_with_backoff)
        last_exception = None
        for attempt in range(3):
            try:
                subject, html_content = await template_client.render_email_template(
                    template_code=request.template_code,
                    variables=request.variables,
                    language=language
                )
                print(f"✅ Template rendered successfully")
                break
            except Exception as e:
                last_exception = e
                if attempt < 2:  # Don't sleep on last attempt
                    wait_time = (2 ** attempt) * 2
                    print(f"Template fetch attempt {attempt + 1}/3 failed: {e}. Retrying in {wait_time}s...")
                    await asyncio.sleep(wait_time)
                else:
                    print(f"All template fetch attempts failed")
                    raise e
        
        # Update email log with rendered content
        email_log.subject = subject
        email_log.body_html = html_content
        db.commit()
        
        # Send email with retry
        last_exception = None
        for attempt in range(3):
            try:
                result = await smtp_service.send_email(
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
                break
            except Exception as e:
                last_exception = e
                if attempt < 2:
                    wait_time = (2 ** attempt) * 2
                    print(f"Email send attempt {attempt + 1}/3 failed: {e}. Retrying in {wait_time}s...")
                    await asyncio.sleep(wait_time)
                else:
                    print(f"All email send attempts failed")
                    raise e
        
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
