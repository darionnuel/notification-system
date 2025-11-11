"""Template database models."""
from sqlalchemy import Column, String, Text, DateTime, Integer, JSON, Enum as SQLEnum, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
import uuid

from app.db.session import Base


class TemplateStatus(str, enum.Enum):
    """Template status enum."""
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"
    DEPRECATED = "deprecated"


class TemplateType(str, enum.Enum):
    """Template type enum."""
    EMAIL = "email"
    PUSH = "push"


class Template(Base):
    """
    Template model for storing notification templates.
    
    Attributes:
        id: Unique identifier (UUID as string)
        template_code: Unique code for template (e.g., 'welcome_email')
        template_type: Type of template (email or push)
        language: Language code (e.g., 'en', 'es', 'fr')
        subject: Subject line (for email templates)
        content: Template content with {{variable}} placeholders
        description: Template description
        required_variables: JSON list of required variable names
        status: Template status (draft, active, archived, deprecated)
        version: Current version number
        created_at: Creation timestamp
        updated_at: Last update timestamp
        created_by: User ID who created (optional, for future auth)
    """
    __tablename__ = "templates"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    template_code = Column(String(255), unique=True, nullable=False, index=True)
    template_type = Column(SQLEnum(TemplateType), nullable=False)
    language = Column(String(10), nullable=False, default="en")
    subject = Column(String(500), nullable=True)  # For email templates
    content = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    required_variables = Column(JSON, nullable=True, default=list)
    status = Column(SQLEnum(TemplateStatus), nullable=False, default=TemplateStatus.DRAFT)
    version = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_by = Column(String(36), nullable=True)  # Future: Link to user service
    
    # Relationship to versions
    versions = relationship("TemplateVersion", back_populates="template", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Template(code={self.template_code}, type={self.template_type}, version={self.version})>"


class TemplateVersion(Base):
    """
    Template version history model.
    
    Stores historical versions when templates are updated.
    
    Attributes:
        id: Unique identifier
        template_id: Foreign key to parent template
        version_number: Version number
        content: Template content at this version
        subject: Subject at this version (for email)
        required_variables: Required variables at this version
        status: Status at this version
        created_at: When this version was created
        created_by: User who created this version
        change_log: Description of changes made
    """
    __tablename__ = "template_versions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    template_id = Column(String(36), ForeignKey("templates.id", ondelete="CASCADE"), nullable=False)
    version_number = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    subject = Column(String(500), nullable=True)
    required_variables = Column(JSON, nullable=True, default=list)
    status = Column(SQLEnum(TemplateStatus), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_by = Column(String(36), nullable=True)
    change_log = Column(Text, nullable=True)
    
    # Relationship to parent template
    template = relationship("Template", back_populates="versions")

    def __repr__(self):
        return f"<TemplateVersion(template_id={self.template_id}, version={self.version_number})>"
