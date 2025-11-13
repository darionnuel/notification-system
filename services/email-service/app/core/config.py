"""Application configuration settings."""
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional, Union


class Settings(BaseSettings):
    """Application settings."""
    
    # Application
    app_name: str = "Email Service"
    app_version: str = "1.0.0"
    debug: bool = True
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8002
    
    # Database
    database_url: str = "sqlite:///./email_service.db"
    
    # Template Service
    template_service_url: str = "http://localhost:8001"
    template_service_timeout: int = 10  # seconds
    
    # SMTP Configuration
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_use_tls: bool = True
    smtp_from_email: str = ""
    smtp_from_name: str = "Notification System"
    
    # SendGrid (alternative to SMTP)
    sendgrid_api_key: Optional[str] = None
    
    # Email Provider (smtp or sendgrid)
    email_provider: str = "smtp"
    
    # RabbitMQ Configuration
    rabbitmq_url: str = "amqp://guest:guest@localhost:5672/"
    rabbitmq_exchange: str = "notifications.direct"
    rabbitmq_email_queue: str = "email.queue"
    rabbitmq_status_queue: str = "status.queue"
    rabbitmq_failed_queue: str = "failed.queue"
    rabbitmq_prefetch_count: int = 10
    rabbitmq_connection_timeout: int = 30  # seconds
    
    # Retry Configuration
    retry_max_attempts: int = 3
    retry_backoff_seconds: int = 2  # seconds (exponential: 2, 4, 8)
    
    # Circuit Breaker
    circuit_breaker_failure_threshold: int = 5  # failures before opening
    circuit_breaker_timeout: int = 60  # seconds before trying again
    
    # CORS
    cors_origins: Union[str, list[str]] = "*"
    
    # Rate Limiting
    rate_limit_per_minute: int = 100
    
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