"""Circuit breaker pattern implementation."""
import time
from enum import Enum
from typing import Callable, Any
from app.core.config import settings


class CircuitState(str, Enum):
    """Circuit breaker states."""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Too many failures, reject requests
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitBreaker:
    """
    Circuit breaker to prevent cascading failures.
    
    - CLOSED: Normal operation, requests pass through
    - OPEN: Too many failures, reject requests immediately
    - HALF_OPEN: After timeout, try one request to test recovery
    """
    
    def __init__(
        self,
        failure_threshold: int = None,
        timeout: int = None,
        name: str = "default"
    ):
        """
        Initialize circuit breaker.
        
        Args:
            failure_threshold: Number of failures before opening circuit
            timeout: Seconds to wait before trying again
            name: Name of the circuit for logging
        """
        self.failure_threshold = failure_threshold or settings.circuit_breaker_failure_threshold
        self.timeout = timeout or settings.circuit_breaker_timeout
        self.name = name
        
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function through circuit breaker.
        
        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
            
        Raises:
            Exception: If circuit is open or function fails
        """
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
                print(f"Circuit breaker '{self.name}': Attempting reset (HALF_OPEN)")
            else:
                raise Exception(
                    f"Circuit breaker '{self.name}' is OPEN. "
                    f"Service unavailable. Try again in {self._time_until_reset():.0f}s"
                )
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise e
    
    def _on_success(self):
        """Handle successful call."""
        if self.state == CircuitState.HALF_OPEN:
            print(f"Circuit breaker '{self.name}': Service recovered, closing circuit")
        
        self.failure_count = 0
        self.state = CircuitState.CLOSED
    
    def _on_failure(self):
        """Handle failed call."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
            print(
                f"Circuit breaker '{self.name}': Too many failures ({self.failure_count}), "
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
    
    def reset(self):
        """Manually reset circuit breaker."""
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED
        print(f"Circuit breaker '{self.name}': Manually reset")
