"""Correlation ID utilities for distributed tracing."""
import uuid
from contextvars import ContextVar

# Context variable to store correlation ID per request
correlation_id_var: ContextVar[str] = ContextVar('correlation_id', default=None)


def generate_correlation_id() -> str:
    """Generate a new correlation ID."""
    return str(uuid.uuid4())


def get_correlation_id() -> str:
    """Get current correlation ID or generate new one."""
    corr_id = correlation_id_var.get()
    if not corr_id:
        corr_id = generate_correlation_id()
        correlation_id_var.set(corr_id)
    return corr_id


def set_correlation_id(correlation_id: str):
    """Set correlation ID for current context."""
    correlation_id_var.set(correlation_id)


def clear_correlation_id():
    """Clear correlation ID from current context."""
    correlation_id_var.set(None)
