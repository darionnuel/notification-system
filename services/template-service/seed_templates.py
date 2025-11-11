"""Seed database with predefined templates."""
from sqlalchemy.orm import Session
from app.db.session import SessionLocal, init_db
from app.models.template import Template, TemplateType, TemplateStatus


def seed_templates():
    """
    Create predefined templates for common use cases.
    """
    init_db()
    db: Session = SessionLocal()
    
    try:
        # Check if templates already exist
        existing = db.query(Template).first()
        if existing:
            print("⚠️  Templates already exist. Skipping seed.")
            return
        
        templates = [
            # Welcome Email
            Template(
                template_code="welcome_email",
                template_type=TemplateType.EMAIL,
                language="en",
                subject="Welcome to {{app_name}}! 🎉",
                content="""
                    <h1>Welcome, {{user_name}}!</h1>
                    <p>We're excited to have you join {{app_name}}.</p>
                    <p>Your account has been successfully created with the email: <strong>{{user_email}}</strong></p>
                    <p>Get started by exploring our features:</p>
                    <ul>
                        <li>Complete your profile</li>
                        <li>Connect with others</li>
                        <li>Explore resources</li>
                    </ul>
                    <p>If you have any questions, feel free to reach out to our support team.</p>
                    <p>Best regards,<br>The {{app_name}} Team</p>
                """,
                description="Welcome email sent to new users upon registration",
                required_variables=["user_name", "user_email", "app_name"],
                status=TemplateStatus.ACTIVE,
                version=1
            ),
            
            # Password Reset
            Template(
                template_code="password_reset",
                template_type=TemplateType.EMAIL,
                language="en",
                subject="Reset Your Password - {{app_name}}",
                content="""
                    <h1>Password Reset Request</h1>
                    <p>Hi {{user_name}},</p>
                    <p>We received a request to reset your password for your {{app_name}} account.</p>
                    <p>Click the link below to reset your password:</p>
                    <p><a href="{{reset_link}}" style="background-color: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block;">Reset Password</a></p>
                    <p>This link will expire in {{expiry_hours}} hours.</p>
                    <p>If you didn't request this, please ignore this email. Your password will remain unchanged.</p>
                    <p>For security reasons, never share this link with anyone.</p>
                    <p>Best regards,<br>The {{app_name}} Team</p>
                """,
                description="Password reset email with secure link",
                required_variables=["user_name", "reset_link", "expiry_hours", "app_name"],
                status=TemplateStatus.ACTIVE,
                version=1
            ),
            
            # Email Verification
            Template(
                template_code="email_verification",
                template_type=TemplateType.EMAIL,
                language="en",
                subject="Verify Your Email - {{app_name}}",
                content="""
                    <h1>Verify Your Email Address</h1>
                    <p>Hi {{user_name}},</p>
                    <p>Thank you for signing up for {{app_name}}!</p>
                    <p>Please verify your email address by clicking the button below:</p>
                    <p><a href="{{verification_link}}" style="background-color: #28a745; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block;">Verify Email</a></p>
                    <p>Or copy and paste this link into your browser:</p>
                    <p>{{verification_link}}</p>
                    <p>This link will expire in {{expiry_hours}} hours.</p>
                    <p>If you didn't create an account, you can safely ignore this email.</p>
                    <p>Best regards,<br>The {{app_name}} Team</p>
                """,
                description="Email verification for new user accounts",
                required_variables=["user_name", "verification_link", "expiry_hours", "app_name"],
                status=TemplateStatus.ACTIVE,
                version=1
            ),
            
            # Order Confirmation
            Template(
                template_code="order_confirmation",
                template_type=TemplateType.EMAIL,
                language="en",
                subject="Order Confirmation - #{{order_number}}",
                content="""
                    <h1>Order Confirmed! 🎉</h1>
                    <p>Hi {{customer_name}},</p>
                    <p>Thank you for your order! We've received your order and are processing it.</p>
                    <h2>Order Details</h2>
                    <ul>
                        <li><strong>Order Number:</strong> {{order_number}}</li>
                        <li><strong>Order Date:</strong> {{order_date}}</li>
                        <li><strong>Total Amount:</strong> ${{total_amount}}</li>
                    </ul>
                    <p>We'll send you another email when your order ships.</p>
                    <p>You can track your order status at any time by visiting your account.</p>
                    <p>Thank you for shopping with {{app_name}}!</p>
                    <p>Best regards,<br>The {{app_name}} Team</p>
                """,
                description="Order confirmation email for e-commerce",
                required_variables=["customer_name", "order_number", "order_date", "total_amount", "app_name"],
                status=TemplateStatus.ACTIVE,
                version=1
            ),
            
            # Push Notification - New Message
            Template(
                template_code="new_message_push",
                template_type=TemplateType.PUSH,
                language="en",
                subject=None,  # Push notifications don't need subjects
                content="💬 New message from {{sender_name}}: {{message_preview}}",
                description="Push notification for new messages",
                required_variables=["sender_name", "message_preview"],
                status=TemplateStatus.ACTIVE,
                version=1
            ),
            
            # Push Notification - System Alert
            Template(
                template_code="system_alert_push",
                template_type=TemplateType.PUSH,
                language="en",
                subject=None,
                content="⚠️ {{alert_title}}: {{alert_message}}",
                description="System alert push notification",
                required_variables=["alert_title", "alert_message"],
                status=TemplateStatus.ACTIVE,
                version=1
            ),
        ]
        
        # Add all templates
        db.add_all(templates)
        db.commit()
        
        print(f"✅ Successfully seeded {len(templates)} templates:")
        for template in templates:
            print(f"   - {template.template_code} ({template.template_type.value})")
        
    except Exception as e:
        print(f"❌ Error seeding templates: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    print("🌱 Seeding templates...")
    seed_templates()
    print("✨ Done!")
