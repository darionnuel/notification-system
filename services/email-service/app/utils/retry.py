"""Retry utility with exponential backoff."""
import asyncio
import time
from typing import Callable, Any, Optional
from app.core.config import settings


async def retry_with_backoff(
    func: Callable,
    *args,
    max_attempts: Optional[int] = None,
    backoff_base: Optional[int] = None,
    **kwargs
) -> Any:
    """
    Retry async function with exponential backoff.
    
    Args:
        func: Async function to retry (can be a coroutine function)
        *args: Function arguments
        max_attempts: Maximum retry attempts
        backoff_base: Base seconds for exponential backoff (2^attempt * base)
        **kwargs: Function keyword arguments
        
    Returns:
        Function result
        
    Raises:
        Last exception if all retries fail
    """
    max_attempts = max_attempts or settings.retry_max_attempts
    backoff_base = backoff_base or settings.retry_backoff_seconds
    
    last_exception = None
    
    for attempt in range(max_attempts):
        try:
            # Call the function - if it has args/kwargs, pass them; otherwise just call it
            if args or kwargs:
                result = func(*args, **kwargs)
            else:
                result = func()
            
            # If result is a coroutine, await it
            if asyncio.iscoroutine(result):
                return await result
            else:
                return result
        except Exception as e:
            last_exception = e
            
            if attempt < max_attempts - 1:  # Don't sleep on last attempt
                wait_time = (2 ** attempt) * backoff_base
                print(
                    f"Retry attempt {attempt + 1}/{max_attempts} failed: {str(e)}. "
                    f"Retrying in {wait_time}s..."
                )
                await asyncio.sleep(wait_time)
            else:
                print(f"All {max_attempts} retry attempts failed")
    
    raise last_exception


def retry_sync_with_backoff(
    func: Callable,
    *args,
    max_attempts: Optional[int] = None,
    backoff_base: Optional[int] = None,
    **kwargs
) -> Any:
    """
    Retry synchronous function with exponential backoff.
    
    Args:
        func: Synchronous function to retry
        *args: Function arguments
        max_attempts: Maximum retry attempts
        backoff_base: Base seconds for exponential backoff
        **kwargs: Function keyword arguments
        
    Returns:
        Function result
        
    Raises:
        Last exception if all retries fail
    """
    max_attempts = max_attempts or settings.retry_max_attempts
    backoff_base = backoff_base or settings.retry_backoff_seconds
    
    last_exception = None
    
    for attempt in range(max_attempts):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            last_exception = e
            
            if attempt < max_attempts - 1:
                wait_time = (2 ** attempt) * backoff_base
                print(
                    f"Retry attempt {attempt + 1}/{max_attempts} failed: {str(e)}. "
                    f"Retrying in {wait_time}s..."
                )
                time.sleep(wait_time)
            else:
                print(f"All {max_attempts} retry attempts failed")
    
    raise last_exception
