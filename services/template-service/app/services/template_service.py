"""Template service with business logic."""
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional, Dict, Any
from jinja2 import Template as Jinja2Template, TemplateError
import re

from app.models.template import Template, TemplateVersion, TemplateStatus, TemplateType
from app.schemas.template import TemplateCreate, TemplateUpdate
from fastapi import HTTPException, status


class TemplateService:
    """Service class for template operations."""
    
    @staticmethod
    def extract_variables(content: str) -> List[str]:
        """
        Extract all {{variable}} names from template content.
        
        Args:
            content: Template content string
            
        Returns:
            List of unique variable names found
        """
        pattern = r'\{\{(\w+)\}\}'
        return list(set(re.findall(pattern, content)))
    
    @staticmethod
    def render_template(content: str, variables: Dict[str, Any]) -> str:
        """
        Safely render template with variable substitution using Jinja2.
        
        Args:
            content: Template content with {{variable}} placeholders
            variables: Dictionary of variables to inject
            
        Returns:
            Rendered template string
            
        Raises:
            HTTPException: If rendering fails
        """
        try:
            template = Jinja2Template(content)
            return template.render(**variables)
        except TemplateError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Template rendering failed: {str(e)}"
            )
    
    @staticmethod
    def validate_required_variables(required: List[str], provided: Dict[str, Any]) -> None:
        """
        Validate that all required variables are provided.
        
        Args:
            required: List of required variable names
            provided: Dictionary of provided variables
            
        Raises:
            HTTPException: If required variables are missing
        """
        missing = [var for var in required if var not in provided]
        if missing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Missing required variables: {', '.join(missing)}"
            )
    
    @staticmethod
    def create_template(db: Session, template_data: TemplateCreate, created_by: Optional[str] = None) -> Template:
        """
        Create a new template.
        
        Args:
            db: Database session
            template_data: Template creation data
            created_by: User ID who created the template
            
        Returns:
            Created template
            
        Raises:
            HTTPException: If template with same code already exists
        """
        
        # Check if template code already exists
        existing = db.query(Template).filter(Template.template_code == template_data.template_code).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Template with code '{template_data.template_code}' already exists"
            )
        
        # Validate subject for EMAIL templates
        if template_data.template_type == TemplateType.EMAIL and not template_data.subject:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Subject is required for EMAIL templates"
            )
        
        # Extract variables from content if not provided
        if not template_data.required_variables:
            template_data.required_variables = TemplateService.extract_variables(template_data.content)
        
        # Create template
        template = Template(
            template_code=template_data.template_code,
            template_type=template_data.template_type,
            language=template_data.language,
            subject=template_data.subject,
            content=template_data.content,
            description=template_data.description,
            required_variables=template_data.required_variables,
            status=template_data.status,
            version=1,
            created_by=created_by
        )
        
        db.add(template)
        db.commit()
        db.refresh(template)
        
        return template
    
    @staticmethod
    def get_template_by_id(db: Session, template_id: str) -> Template:
        """
        Get template by ID.
        
        Args:
            db: Database session
            template_id: Template ID
            
        Returns:
            Template
            
        Raises:
            HTTPException: If template not found
        """
        template = db.query(Template).filter(Template.id == template_id).first()
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Template with ID '{template_id}' not found"
            )
        return template
    
    @staticmethod
    def get_template_by_code(db: Session, template_code: str, language: str = "en") -> Template:
        """
        Get template by code and language.
        
        Args:
            db: Database session
            template_code: Template code
            language: Language code
            
        Returns:
            Template
            
        Raises:
            HTTPException: If template not found
        """
        template = db.query(Template).filter(
            Template.template_code == template_code,
            Template.language == language
        ).first()
        
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Template '{template_code}' not found for language '{language}'"
            )
        return template
    
    @staticmethod
    def list_templates(
        db: Session,
        skip: int = 0,
        limit: int = 20,
        template_type: Optional[TemplateType] = None,
        status: Optional[TemplateStatus] = None,
        language: Optional[str] = None
    ) -> tuple[List[Template], int]:
        """
        List templates with pagination and filters.
        
        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return
            template_type: Filter by template type
            status: Filter by status
            language: Filter by language
            
        Returns:
            Tuple of (templates list, total count)
        """
        query = db.query(Template)
        
        # Apply filters
        if template_type:
            query = query.filter(Template.template_type == template_type)
        if status:
            query = query.filter(Template.status == status)
        if language:
            query = query.filter(Template.language == language)
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        templates = query.order_by(Template.created_at.desc()).offset(skip).limit(limit).all()
        
        return templates, total
    
    @staticmethod
    def update_template(
        db: Session,
        template_id: str,
        update_data: TemplateUpdate,
        created_by: Optional[str] = None
    ) -> Template:
        """
        Update template and create a new version.
        
        Args:
            db: Database session
            template_id: Template ID
            update_data: Update data
            created_by: User ID who updated
            
        Returns:
            Updated template
            
        Raises:
            HTTPException: If template not found
        """
        template = TemplateService.get_template_by_id(db, template_id)
        
        # Validate subject for EMAIL templates if updating subject or type
        update_dict = update_data.model_dump(exclude_unset=True, exclude={'change_log'})
        template_type = update_dict.get('template_type', template.template_type)
        subject = update_dict.get('subject', template.subject)
        if template_type == TemplateType.EMAIL and not subject:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Subject is required for EMAIL templates"
            )
        
        # Create version history before updating
        version = TemplateVersion(
            template_id=template.id,
            version_number=template.version,
            content=template.content,
            subject=template.subject,
            required_variables=template.required_variables,
            status=template.status,
            created_by=created_by,
            change_log=update_data.change_log
        )
        db.add(version)
        
        # Update template
        update_dict = update_data.model_dump(exclude_unset=True, exclude={'change_log'})
        
        # Extract variables if content is updated
        if 'content' in update_dict:
            update_dict['required_variables'] = TemplateService.extract_variables(update_dict['content'])
        
        # Increment version
        update_dict['version'] = template.version + 1
        
        for key, value in update_dict.items():
            setattr(template, key, value)
        
        db.commit()
        db.refresh(template)
        
        return template
    
    @staticmethod
    def delete_template(db: Session, template_id: str) -> None:
        """
        Soft delete template by marking as archived.
        
        Args:
            db: Database session
            template_id: Template ID
            
        Raises:
            HTTPException: If template not found
        """
        template = TemplateService.get_template_by_id(db, template_id)
        template.status = TemplateStatus.ARCHIVED
        db.commit()
    
    @staticmethod
    def get_template_versions(db: Session, template_id: str) -> List[TemplateVersion]:
        """
        Get all versions of a template.
        
        Args:
            db: Database session
            template_id: Template ID
            
        Returns:
            List of template versions
            
        Raises:
            HTTPException: If template not found
        """
        # Verify template exists
        TemplateService.get_template_by_id(db, template_id)
        
        versions = db.query(TemplateVersion).filter(
            TemplateVersion.template_id == template_id
        ).order_by(TemplateVersion.version_number.desc()).all()
        
        return versions
