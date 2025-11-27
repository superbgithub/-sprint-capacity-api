"""
Circuit Breaker Pattern Implementation

Prevents cascading failures by failing fast when services are unavailable.
"""
from datetime import datetime, timedelta
from enum import Enum
from typing import Callable, Any, Optional
import asyncio
from functools import wraps

from app.observability.logging import get_logger

logger = get_logger(__name__)


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitBreakerError(Exception):
    """Raised when circuit breaker is open."""
    pass


class CircuitBreaker:
    """
    Circuit breaker implementation for protecting external service calls.
    
    States:
    - CLOSED: Normal operation, requests pass through
    - OPEN: Too many failures, reject requests immediately
    - HALF_OPEN: After timeout, allow limited requests to test recovery
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: type = Exception,
        name: str = "circuit_breaker"
    ):
        """
        Initialize circuit breaker.
        
        Args:
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Seconds to wait before attempting recovery
            expected_exception: Exception type to catch
            name: Circuit breaker name for logging
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.name = name
        
        self._failure_count = 0
        self._last_failure_time: Optional[datetime] = None
        self._state = CircuitState.CLOSED
        
    @property
    def state(self) -> CircuitState:
        """Get current circuit state."""
        # Auto-transition from OPEN to HALF_OPEN after timeout
        if self._state == CircuitState.OPEN:
            if self._last_failure_time:
                elapsed = (datetime.now() - self._last_failure_time).total_seconds()
                if elapsed >= self.recovery_timeout:
                    logger.info(
                        f"Circuit breaker '{self.name}' transitioning to HALF_OPEN",
                        extra={
                            "circuit_breaker": self.name,
                            "state": "half_open",
                            "elapsed_seconds": elapsed
                        }
                    )
                    self._state = CircuitState.HALF_OPEN
                    self._failure_count = 0
        
        return self._state
    
    def _on_success(self):
        """Handle successful call."""
        if self._state == CircuitState.HALF_OPEN:
            logger.info(
                f"Circuit breaker '{self.name}' recovered, closing circuit",
                extra={"circuit_breaker": self.name, "state": "closed"}
            )
            self._state = CircuitState.CLOSED
        
        self._failure_count = 0
        self._last_failure_time = None
    
    def _on_failure(self):
        """Handle failed call."""
        self._failure_count += 1
        self._last_failure_time = datetime.now()
        
        if self._failure_count >= self.failure_threshold:
            if self._state != CircuitState.OPEN:
                logger.error(
                    f"Circuit breaker '{self.name}' opening circuit",
                    extra={
                        "circuit_breaker": self.name,
                        "state": "open",
                        "failure_count": self._failure_count,
                        "threshold": self.failure_threshold
                    }
                )
                self._state = CircuitState.OPEN
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function with circuit breaker protection.
        
        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
            
        Raises:
            CircuitBreakerError: If circuit is open
        """
        if self.state == CircuitState.OPEN:
            raise CircuitBreakerError(
                f"Circuit breaker '{self.name}' is OPEN, rejecting call"
            )
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception as e:
            self._on_failure()
            raise e
    
    async def call_async(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute async function with circuit breaker protection.
        
        Args:
            func: Async function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
            
        Raises:
            CircuitBreakerError: If circuit is open
        """
        if self.state == CircuitState.OPEN:
            raise CircuitBreakerError(
                f"Circuit breaker '{self.name}' is OPEN, rejecting call"
            )
        
        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception as e:
            self._on_failure()
            raise e
    
    def __call__(self, func: Callable) -> Callable:
        """
        Decorator for wrapping functions with circuit breaker.
        
        Usage:
            @circuit_breaker(failure_threshold=3, recovery_timeout=30)
            async def my_function():
                ...
        """
        if asyncio.iscoroutinefunction(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                return await self.call_async(func, *args, **kwargs)
            return async_wrapper
        else:
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                return self.call(func, *args, **kwargs)
            return sync_wrapper


# Global circuit breakers for common services
database_breaker = CircuitBreaker(
    failure_threshold=5,
    recovery_timeout=60,
    expected_exception=Exception,
    name="database"
)

kafka_breaker = CircuitBreaker(
    failure_threshold=3,
    recovery_timeout=30,
    expected_exception=Exception,
    name="kafka"
)
