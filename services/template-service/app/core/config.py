"""Application configuration settings."""
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional, Union


class Settings(BaseSettings):
    """Application settings."""
    
    # Application
    app_name: str = "Template Service"
    app_version: str = "1.0.0"
    debug: bool = True
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8001
    
    # Database
    database_url: str = "sqlite:///./template_service.db"
    
    # For production PostgreSQL (uncomment and use)
    # database_url: str = "postgresql://user:password@localhost:5432/template_db"
    
    # Redis (optional for caching)
    redis_url: Optional[str] = None
    redis_cache_ttl: int = 3600  # 1 hour
    
    # CORS - can be string (comma-separated) or list
    cors_origins: Union[str, list[str]] = "*"
    
    # Pagination
    default_page_size: int = 20
    max_page_size: int = 100
    
    @field_validator('cors_origins', mode='before')
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse CORS origins from comma-separated string or list."""
        if isinstance(v, str):
            if v == "*":
                return ["*"]
            return [origin.strip() for origin in v.split(',')]
        return v
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )


# Global settings instance
settings = Settings()
