"""SMTP and SendGrid email service."""
import aiosmtplib
import sendgrid
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, Dict, Any
from sendgrid.helpers.mail import Mail, Email, To, Content

from app.core.config import settings
from app.core.circuit_breaker import CircuitBreaker


class SMTPService:
    """Service for sending emails via SMTP or SendGrid."""
    
    def __init__(self):
        """Initialize SMTP service."""
        self.smtp_circuit_breaker = CircuitBreaker(name="SMTP")
        self.sendgrid_circuit_breaker = CircuitBreaker(name="SendGrid")
    
    async def send_via_smtp(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None,
        reply_to: Optional[str] = None,
        cc: Optional[list[str]] = None,
        bcc: Optional[list[str]] = None,
    ) -> Dict[str, Any]:
        """
        Send email via SMTP (Gmail).
        
        Args:
            to_email: Recipient email
            subject: Email subject
            html_content: HTML email content
            from_email: Sender email (default from settings)
            from_name: Sender name
            reply_to: Reply-to email
            cc: List of CC emails
            bcc: List of BCC emails
            
        Returns:
            Dict with success status and message
            
        Raises:
            Exception: If SMTP send fails
        """
        async def send():
            # Use default sender if not provided
            sender_email = from_email or settings.smtp_from_email
            sender_display = f"{from_name} <{sender_email}>" if from_name else sender_email
            
            # Create message
            message = MIMEMultipart("alternative")
            message["From"] = sender_display
            message["To"] = to_email
            message["Subject"] = subject
            
            if reply_to:
                message["Reply-To"] = reply_to
            
            if cc:
                message["Cc"] = ", ".join(cc)
            
            if bcc:
                message["Bcc"] = ", ".join(bcc)
            
            # Add HTML content
            html_part = MIMEText(html_content, "html")
            message.attach(html_part)
            
            # Send via SMTP
            await aiosmtplib.send(
                message,
                hostname=settings.smtp_host,
                port=settings.smtp_port,
                username=settings.smtp_username,
                password=settings.smtp_password,
                use_tls=settings.smtp_use_tls,
            )
            
            return {
                "success": True,
                "provider": "smtp",
                "message": "Email sent successfully via SMTP"
            }
        
        return await self.smtp_circuit_breaker.call(send)
    
    async def send_via_sendgrid(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None,
        reply_to: Optional[str] = None,
        cc: Optional[list[str]] = None,
        bcc: Optional[list[str]] = None,
    ) -> Dict[str, Any]:
        """
        Send email via SendGrid API.
        
        Args:
            to_email: Recipient email
            subject: Email subject
            html_content: HTML email content
            from_email: Sender email (default from settings)
            from_name: Sender name
            reply_to: Reply-to email
            cc: List of CC emails
            bcc: List of BCC emails
            
        Returns:
            Dict with success status and message
            
        Raises:
            Exception: If SendGrid send fails
        """
        async def send():
            sg = sendgrid.SendGridAPIClient(api_key=settings.sendgrid_api_key)
            
            # Setup sender
            sender_email = from_email or settings.smtp_from_email
            from_email_obj = Email(sender_email, from_name)
            
            # Setup recipient
            to_email_obj = To(to_email)
            
            # Setup content
            content = Content("text/html", html_content)
            
            # Create mail object
            mail = Mail(from_email_obj, to_email_obj, subject, content)
            
            # Add reply-to
            if reply_to:
                mail.reply_to = Email(reply_to)
            
            # Add CC
            if cc:
                for email in cc:
                    mail.add_cc(Email(email))
            
            # Add BCC
            if bcc:
                for email in bcc:
                    mail.add_bcc(Email(email))
            
            # Send email
            response = sg.send(mail)
            
            return {
                "success": True,
                "provider": "sendgrid",
                "message": "Email sent successfully via SendGrid",
                "status_code": response.status_code,
                "message_id": response.headers.get("X-Message-Id")
            }
        
        return await self.sendgrid_circuit_breaker.call(send)
    
    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None,
        reply_to: Optional[str] = None,
        cc: Optional[list[str]] = None,
        bcc: Optional[list[str]] = None,
        provider: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Send email using configured provider.
        
        Args:
            to_email: Recipient email
            subject: Email subject
            html_content: HTML email content
            from_email: Sender email
            from_name: Sender name
            reply_to: Reply-to email
            cc: List of CC emails
            bcc: List of BCC emails
            provider: Email provider ("smtp" or "sendgrid"). If not provided, uses default from settings.
            
        Returns:
            Dict with success status and provider info
            
        Raises:
            Exception: If sending fails
        """
        # Determine provider
        selected_provider = provider or settings.email_provider
        
        if selected_provider == "sendgrid" and settings.sendgrid_api_key:
            return await self.send_via_sendgrid(
                to_email=to_email,
                subject=subject,
                html_content=html_content,
                from_email=from_email,
                from_name=from_name,
                reply_to=reply_to,
                cc=cc,
                bcc=bcc,
            )
        else:
            # Default to SMTP
            return await self.send_via_smtp(
                to_email=to_email,
                subject=subject,
                html_content=html_content,
                from_email=from_email,
                from_name=from_name,
                reply_to=reply_to,
                cc=cc,
                bcc=bcc,
            )


# Global instance
smtp_service = SMTPService()
