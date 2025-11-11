"""Template schemas for request/response validation."""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class TemplateType(str, Enum):
    """Template type enum."""
    EMAIL = "email"
    PUSH = "push"


class TemplateStatus(str, Enum):
    """Template status enum."""
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"
    DEPRECATED = "deprecated"


# Request Schemas

class TemplateCreate(BaseModel):
    """Schema for creating a new template."""
    template_code: str = Field(..., min_length=1, max_length=255, description="Unique template identifier")
    template_type: TemplateType = Field(..., description="Type of template (email or push)")
    language: str = Field(default="en", max_length=10, description="Language code (e.g., 'en', 'es')")
    subject: Optional[str] = Field(None, max_length=500, description="Subject line (required for email templates)")
    content: str = Field(..., min_length=1, description="Template content with {{variable}} placeholders")
    description: Optional[str] = Field(None, description="Template description")
    required_variables: List[str] = Field(default_factory=list, description="List of required variable names")
    status: TemplateStatus = Field(default=TemplateStatus.DRAFT, description="Template status")
    
    @field_validator('subject')
    @classmethod
    def validate_email_subject(cls, v, info):
        """Ensure email templates have a subject."""
        if info.data.get('template_type') == TemplateType.EMAIL and not v:
            raise ValueError('Subject is required for email templates')
        return v
    
    @field_validator('template_code')
    @classmethod
    def validate_template_code(cls, v):
        """Ensure template code is valid (lowercase, alphanumeric, underscores)."""
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('Template code must contain only alphanumeric characters, underscores, and hyphens')
        return v.lower()


class TemplateUpdate(BaseModel):
    """Schema for updating an existing template."""
    subject: Optional[str] = Field(None, max_length=500, description="Subject line")
    content: Optional[str] = Field(None, min_length=1, description="Template content")
    description: Optional[str] = Field(None, description="Template description")
    required_variables: Optional[List[str]] = Field(None, description="List of required variable names")
    status: Optional[TemplateStatus] = Field(None, description="Template status")
    change_log: Optional[str] = Field(None, description="Description of changes made")


class TemplateRender(BaseModel):
    """Schema for rendering a template with variables."""
    variables: Dict[str, Any] = Field(..., description="Variables to inject into template")
    version: Optional[int] = Field(None, description="Specific version to render (default: latest)")


# Response Schemas

class TemplateResponse(BaseModel):
    """Schema for template response."""
    id: str
    template_code: str
    template_type: TemplateType
    language: str
    subject: Optional[str]
    content: str
    description: Optional[str]
    required_variables: List[str]
    status: TemplateStatus
    version: int
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str]

    model_config = {
        "from_attributes": True
    }


class TemplateVersionResponse(BaseModel):
    """Schema for template version response."""
    id: str
    template_id: str
    version_number: int
    content: str
    subject: Optional[str]
    required_variables: List[str]
    status: TemplateStatus
    created_at: datetime
    created_by: Optional[str]
    change_log: Optional[str]

    model_config = {
        "from_attributes": True
    }


class TemplateRenderResponse(BaseModel):
    """Schema for template render response."""
    rendered_content: str
    subject: Optional[str] = None
    variables_used: List[str]


class TemplateListResponse(BaseModel):
    """Schema for paginated template list response."""
    items: List[TemplateResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
