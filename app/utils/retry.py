"""
Retry mechanism with exponential backoff for transient failures.
"""
import asyncio
from functools import wraps
from typing import Callable, Type, Tuple, Optional
import random

from app.observability.logging import get_logger

logger = get_logger(__name__)


def retry_with_backoff(
    max_attempts: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    operation_name: Optional[str] = None
):
    """
    Decorator for retrying operations with exponential backoff.
    
    Args:
        max_attempts: Maximum number of retry attempts (including initial try)
        initial_delay: Initial delay in seconds before first retry
        max_delay: Maximum delay in seconds between retries
        exponential_base: Base for exponential backoff (2 = double each time)
        jitter: Add random jitter to prevent thundering herd
        exceptions: Tuple of exception types to retry on
        operation_name: Name for logging (defaults to function name)
    
    Usage:
        @retry_with_backoff(max_attempts=3, initial_delay=1.0)
        async def fetch_data():
            return await external_api.get("/data")
    """
    def decorator(func: Callable) -> Callable:
        op_name = operation_name or func.__name__
        
        if asyncio.iscoroutinefunction(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                last_exception = None
                
                for attempt in range(1, max_attempts + 1):
                    try:
                        result = await func(*args, **kwargs)
                        
                        # Log success if this was a retry
                        if attempt > 1:
                            logger.info(
                                f"Retry succeeded for {op_name}",
                                extra={
                                    "operation": op_name,
                                    "attempt": attempt,
                                    "max_attempts": max_attempts
                                }
                            )
                        
                        return result
                        
                    except exceptions as e:
                        last_exception = e
                        
                        # Don't retry if this was the last attempt
                        if attempt == max_attempts:
                            logger.error(
                                f"All retry attempts exhausted for {op_name}",
                                extra={
                                    "operation": op_name,
                                    "attempts": attempt,
                                    "error": str(e)
                                }
                            )
                            break
                        
                        # Calculate backoff delay
                        delay = min(
                            initial_delay * (exponential_base ** (attempt - 1)),
                            max_delay
                        )
                        
                        # Add jitter to prevent thundering herd
                        if jitter:
                            delay = delay * (0.5 + random.random())
                        
                        logger.warning(
                            f"Retry attempt {attempt}/{max_attempts} failed for {op_name}, waiting {delay:.2f}s",
                            extra={
                                "operation": op_name,
                                "attempt": attempt,
                                "max_attempts": max_attempts,
                                "delay_seconds": delay,
                                "error": str(e)
                            }
                        )
                        
                        await asyncio.sleep(delay)
                
                # Raise the last exception if all retries failed
                raise last_exception
            
            return async_wrapper
        else:
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                import time
                last_exception = None
                
                for attempt in range(1, max_attempts + 1):
                    try:
                        result = func(*args, **kwargs)
                        
                        if attempt > 1:
                            logger.info(
                                f"Retry succeeded for {op_name}",
                                extra={
                                    "operation": op_name,
                                    "attempt": attempt,
                                    "max_attempts": max_attempts
                                }
                            )
                        
                        return result
                        
                    except exceptions as e:
                        last_exception = e
                        
                        if attempt == max_attempts:
                            logger.error(
                                f"All retry attempts exhausted for {op_name}",
                                extra={
                                    "operation": op_name,
                                    "attempts": attempt,
                                    "error": str(e)
                                }
                            )
                            break
                        
                        delay = min(
                            initial_delay * (exponential_base ** (attempt - 1)),
                            max_delay
                        )
                        
                        if jitter:
                            delay = delay * (0.5 + random.random())
                        
                        logger.warning(
                            f"Retry attempt {attempt}/{max_attempts} failed for {op_name}, waiting {delay:.2f}s",
                            extra={
                                "operation": op_name,
                                "attempt": attempt,
                                "max_attempts": max_attempts,
                                "delay_seconds": delay,
                                "error": str(e)
                            }
                        )
                        
                        time.sleep(delay)
                
                raise last_exception
            
            return sync_wrapper
    
    return decorator


class RetryableOperation:
    """
    Context manager for retryable operations.
    
    Usage:
        async with RetryableOperation("database_query", max_attempts=3) as retry:
            result = await db.execute(query)
    """
    
    def __init__(
        self,
        operation_name: str,
        max_attempts: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True,
        exceptions: Tuple[Type[Exception], ...] = (Exception,)
    ):
        self.operation_name = operation_name
        self.max_attempts = max_attempts
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
        self.exceptions = exceptions
        self.attempt = 0
        
    async def __aenter__(self):
        self.attempt = 0
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            return False
        
        # Check if this exception should be retried
        if not issubclass(exc_type, self.exceptions):
            return False
        
        self.attempt += 1
        
        # Don't retry if max attempts reached
        if self.attempt >= self.max_attempts:
            logger.error(
                f"All retry attempts exhausted for {self.operation_name}",
                extra={
                    "operation": self.operation_name,
                    "attempts": self.attempt,
                    "error": str(exc_val)
                }
            )
            return False
        
        # Calculate and apply backoff
        delay = min(
            self.initial_delay * (self.exponential_base ** (self.attempt - 1)),
            self.max_delay
        )
        
        if self.jitter:
            delay = delay * (0.5 + random.random())
        
        logger.warning(
            f"Retry attempt {self.attempt}/{self.max_attempts} for {self.operation_name}, waiting {delay:.2f}s",
            extra={
                "operation": self.operation_name,
                "attempt": self.attempt,
                "max_attempts": self.max_attempts,
                "delay_seconds": delay,
                "error": str(exc_val)
            }
        )
        
        await asyncio.sleep(delay)
        
        # Suppress exception to allow retry
        return True
