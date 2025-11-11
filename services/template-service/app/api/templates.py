"""Endpoints"""
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from typing import Optional

from app.db.session import get_db
from app.services.template_service import TemplateService
from app.schemas.template import (
    TemplateCreate,
    TemplateUpdate,
    TemplateResponse,
    TemplateListResponse,
    TemplateRenderResponse,
    TemplateRender,
    TemplateVersionResponse,
    TemplateType,
    TemplateStatus
)
# Import shared response models
from app.schemas.response import ApiResponse, PaginationMeta


router = APIRouter(prefix="/api/v1/templates", tags=["templates"])


@router.post("/", response_model=ApiResponse, status_code=status.HTTP_201_CREATED)
def create_template(
    template_data: TemplateCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new template.
    
    **Required for EMAIL templates:**
    - subject field must be provided
    
    **Variables:**
    - Variables are auto-extracted from content using {{variable}} syntax
    - Or you can provide them explicitly in required_variables
    """
    template = TemplateService.create_template(db, template_data)
    return ApiResponse(
        success=True,
        message="Template created successfully",
        data=TemplateResponse.model_validate(template).model_dump()
    )


@router.get("/", response_model=ApiResponse)
def list_templates(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of records"),
    template_type: Optional[TemplateType] = Query(None, description="Filter by template type"),
    status: Optional[TemplateStatus] = Query(None, description="Filter by status"),
    language: Optional[str] = Query(None, description="Filter by language code"),
    db: Session = Depends(get_db)
):
    """
    List all templates with pagination and optional filters.
    """
    templates, total = TemplateService.list_templates(
        db, skip, limit, template_type, status, language
    )
    
    template_responses = [TemplateResponse.model_validate(t).model_dump() for t in templates]
    
    current_page = skip // limit + 1
    total_pages = (total + limit - 1) // limit
    
    return ApiResponse(
        success=True,
        message=f"Retrieved {len(templates)} templates",
        data=template_responses,
        meta=PaginationMeta(
            total=total,
            limit=limit,
            page=current_page,
            total_pages=total_pages,
            has_next=current_page < total_pages,
            has_previous=current_page > 1
        )
    )


@router.get("/health", response_model=ApiResponse)
def health_check():
    """
    Health check endpoint.
    """
    return ApiResponse(
        success=True,
        message="Template service is healthy",
        data={"status": "healthy"}
    )


@router.get("/code/{template_code}", response_model=ApiResponse)
def get_template_by_code(
    template_code: str,
    language: str = Query("en", description="Language code"),
    db: Session = Depends(get_db)
):
    """
    Get a template by code and language.
    
    **Used by Email Service** to fetch templates for rendering.
    """
    template = TemplateService.get_template_by_code(db, template_code, language)
    return ApiResponse(
        success=True,
        message="Template retrieved successfully",
        data=TemplateResponse.model_validate(template).model_dump()
    )


@router.get("/{template_id}", response_model=ApiResponse)
def get_template(template_id: str, db: Session = Depends(get_db)):
    """
    Get a template by ID.
    """
    template = TemplateService.get_template_by_id(db, template_id)
    return ApiResponse(
        success=True,
        message="Template retrieved successfully",
        data=TemplateResponse.model_validate(template).model_dump()
    )


@router.put("/{template_id}", response_model=ApiResponse)
def update_template(
    template_id: str,
    update_data: TemplateUpdate,
    db: Session = Depends(get_db)
):
    """
    Update a template.
    
    **Version Management:**
    - Old version is saved to version history
    - Version number is auto-incremented
    - Include change_log to document what changed
    """
    template = TemplateService.update_template(db, template_id, update_data)
    return ApiResponse(
        success=True,
        message="Template updated successfully",
        data=TemplateResponse.model_validate(template).model_dump()
    )


@router.delete("/{template_id}", response_model=ApiResponse, status_code=status.HTTP_200_OK)
def delete_template(template_id: str, db: Session = Depends(get_db)):
    """
    Soft delete a template by marking it as ARCHIVED.
    """
    TemplateService.delete_template(db, template_id)
    return ApiResponse(
        success=True,
        message="Template archived successfully",
        data=None
    )


@router.get("/{template_id}/versions", response_model=ApiResponse)
def get_template_versions(template_id: str, db: Session = Depends(get_db)):
    """
    Get version history for a template.
    """
    versions = TemplateService.get_template_versions(db, template_id)
    version_responses = [TemplateVersionResponse.model_validate(v).model_dump() for v in versions]
    return ApiResponse(
        success=True,
        message=f"Retrieved {len(versions)} versions",
        data=version_responses
    )

# this one is strictly for us to test with
@router.post("/{template_id}/render", response_model=ApiResponse)
def render_template(
    template_id: str,
    render_data: TemplateRender,
    db: Session = Depends(get_db)
):
    """
    Test render a template with provided variables.
    
    **Use this to:**
    - Test templates before using them in production
    - Preview how templates will look with real data
    - Validate variable substitution
    """
    template = TemplateService.get_template_by_id(db, template_id)
    
    # Validate required variables
    TemplateService.validate_required_variables(template.required_variables, render_data.variables)
    
    # Render content
    rendered_content = TemplateService.render_template(template.content, render_data.variables)
    
    # Render subject if exists
    rendered_subject = None
    if template.subject:
        rendered_subject = TemplateService.render_template(template.subject, render_data.variables)
    
    return ApiResponse(
        success=True,
        message="Template rendered successfully",
        data=TemplateRenderResponse(
            rendered_content=rendered_content,
            subject=rendered_subject,
            variables_used=list(render_data.variables.keys())
        ).model_dump()
    )
