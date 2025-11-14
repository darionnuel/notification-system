"""Async circuit breaker pattern implementation."""
import asyncio
import time
from enum import Enum
from typing import Callable, Any, Awaitable
from app.core.config import settings


class CircuitState(str, Enum):
    """Circuit breaker states."""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Too many failures, reject requests
    HALF_OPEN = "half_open"  # Testing if service recovered


class AsyncCircuitBreaker:
    """
    Async circuit breaker to prevent cascading failures.
    
    Purpose:
    - Prevents overwhelming a failing service with requests
    - Provides fast failure when service is known to be down
    - Automatically tests for service recovery
    
    States:
    - CLOSED: Normal operation, requests pass through
    - OPEN: Too many failures, reject requests immediately (fail fast)
    - HALF_OPEN: After timeout, try one request to test recovery
    
    Use cases:
    - External API calls (SMTP, FCM, User Service, Template Service)
    - Database connections
    - Any service that might fail temporarily
    """
    
    def __init__(
        self,
        failure_threshold: int = None,
        timeout: int = None,
        name: str = "default"
    ):
        """
        Initialize async circuit breaker.
        
        Args:
            failure_threshold: Number of consecutive failures before opening circuit
            timeout: Seconds to wait before trying again (recovery time)
            name: Name of the circuit for logging
        """
        self.failure_threshold = failure_threshold or settings.circuit_breaker_failure_threshold
        self.timeout = timeout or settings.circuit_breaker_timeout
        self.name = name
        
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED
        self._lock = asyncio.Lock()
    
    async def call(self, func: Callable[..., Awaitable[Any]], *args, **kwargs) -> Any:
        """
        Execute async function through circuit breaker.
        
        Args:
            func: Async function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
            
        Raises:
            Exception: If circuit is open or function fails
        """
        async with self._lock:
            if self.state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    self.state = CircuitState.HALF_OPEN
                    print(f"🔄 Circuit breaker '{self.name}': Attempting reset (HALF_OPEN)")
                else:
                    time_left = self._time_until_reset()
                    raise Exception(
                        f"⛔ Circuit breaker '{self.name}' is OPEN. "
                        f"Service unavailable. Try again in {time_left:.0f}s"
                    )
        
        try:
            result = await func(*args, **kwargs)
            await self._on_success()
            return result
        except Exception as e:
            await self._on_failure()
            raise e
    
    async def _on_success(self):
        """Handle successful call."""
        async with self._lock:
            if self.state == CircuitState.HALF_OPEN:
                print(f"✅ Circuit breaker '{self.name}': Service recovered, closing circuit")
            
            self.failure_count = 0
            self.state = CircuitState.CLOSED
    
    async def _on_failure(self):
        """Handle failed call."""
        async with self._lock:
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if self.failure_count >= self.failure_threshold:
                self.state = CircuitState.OPEN
                print(
                    f"🔴 Circuit breaker '{self.name}': Too many failures ({self.failure_count}), "
                    f"opening circuit for {self.timeout}s"
                )
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset."""
        if self.last_failure_time is None:
            return False
        return (time.time() - self.last_failure_time) >= self.timeout
    
    def _time_until_reset(self) -> float:
        """Calculate seconds until reset attempt."""
        if self.last_failure_time is None:
            return 0
        elapsed = time.time() - self.last_failure_time
        return max(0, self.timeout - elapsed)
    
    async def reset(self):
        """Manually reset circuit breaker."""
        async with self._lock:
            self.failure_count = 0
            self.last_failure_time = None
            self.state = CircuitState.CLOSED
            print(f"🔄 Circuit breaker '{self.name}': Manually reset")
