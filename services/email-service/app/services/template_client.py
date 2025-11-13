import httpx
from typing import Dict, Any
from jinja2 import Template as Jinja2Template

from app.core.config import settings
from app.core.circuit_breaker import CircuitBreaker


class TemplateServiceClient:
    """Client for interacting with Template Service."""
    
    def __init__(self):
        """Initialize template service client."""
        self.base_url = settings.template_service_url
        self.timeout = settings.template_service_timeout
        self.circuit_breaker = CircuitBreaker(name="TemplateService")
    
    async def get_template_by_code(self, template_code: str, language: str = "en") -> Dict[str, Any]:
        """
        Fetch template from Template Service by code.
        
        Args:
            template_code: Template code identifier
            language: Language code
            
        Returns:
            Template data dictionary
            
        Raises:
            Exception: If template not found or service unavailable
        """
        url = f"{self.base_url}/api/v1/templates/code/{template_code}"
        params = {"language": language}
        
        async def fetch():
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                
                if not data.get("success"):
                    raise Exception(f"Template Service error: {data.get('message')}")
                
                return data["data"]
        
        return self.circuit_breaker.call(await fetch)
    
    def render_template(self, content: str, variables: Dict[str, Any]) -> str:
        """
        Render template content with variables using Jinja2.
        
        Args:
            content: Template content with {{variable}} placeholders
            variables: Dictionary of variables to inject
            
        Returns:
            Rendered template string
            
        Raises:
            Exception: If rendering fails
        """
        try:
            template = Jinja2Template(content)
            return template.render(**variables)
        except Exception as e:
            raise Exception(f"Template rendering failed: {str(e)}")
    
    async def render_email_template(
        self,
        template_code: str,
        variables: Dict[str, Any],
        language: str = "en"
    ) -> tuple[str, str]:
        """
        Fetch and render email template.
        
        Args:
            template_code: Template code to fetch
            variables: Variables for rendering
            language: Language code
            
        Returns:
            Tuple of (rendered_subject, rendered_content)
            
        Raises:
            Exception: If template not found or rendering fails
        """
        # Fetch template
        template = await self.get_template_by_code(template_code, language)
        
        # Render subject
        subject = ""
        if template.get("subject"):
            subject = self.render_template(template["subject"], variables)
        
        # Render content
        content = self.render_template(template["content"], variables)
        
        return subject, content


# Global instance
template_client = TemplateServiceClient()
