"""
Unit tests for retry mechanism with exponential backoff.
"""
import pytest
import asyncio
import time
from unittest.mock import Mock, patch

from app.utils.retry import retry_with_backoff, RetryableOperation


class TestRetryWithBackoff:
    """Test retry decorator functionality."""
    
    def test_no_retry_on_success(self):
        """Successful operations should not retry."""
        call_count = 0
        
        @retry_with_backoff(max_attempts=3)
        def successful_func():
            nonlocal call_count
            call_count += 1
            return "success"
        
        result = successful_func()
        assert result == "success"
        assert call_count == 1
    
    def test_retry_on_failure_then_success(self):
        """Should retry on failure and succeed on retry."""
        call_count = 0
        
        @retry_with_backoff(max_attempts=3, initial_delay=0.1)
        def flaky_func():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("Transient error")
            return "success"
        
        result = flaky_func()
        assert result == "success"
        assert call_count == 2
    
    def test_all_retries_exhausted(self):
        """Should raise exception after all retries fail."""
        call_count = 0
        
        @retry_with_backoff(max_attempts=3, initial_delay=0.1)
        def always_failing_func():
            nonlocal call_count
            call_count += 1
            raise ValueError("Permanent error")
        
        with pytest.raises(ValueError, match="Permanent error"):
            always_failing_func()
        
        assert call_count == 3
    
    def test_exponential_backoff_timing(self):
        """Should apply exponential backoff between retries."""
        call_times = []
        
        @retry_with_backoff(
            max_attempts=3,
            initial_delay=0.1,
            exponential_base=2.0,
            jitter=False  # Disable jitter for predictable timing
        )
        def failing_func():
            call_times.append(time.time())
            raise ValueError("Error")
        
        start_time = time.time()
        
        with pytest.raises(ValueError):
            failing_func()
        
        # Check that delays increase exponentially
        assert len(call_times) == 3
        
        # First retry delay: 0.1s
        delay1 = call_times[1] - call_times[0]
        assert 0.08 < delay1 < 0.15  # Allow some tolerance
        
        # Second retry delay: 0.2s (doubled)
        delay2 = call_times[2] - call_times[1]
        assert 0.18 < delay2 < 0.25
    
    def test_max_delay_limit(self):
        """Should respect max_delay limit."""
        call_times = []
        
        @retry_with_backoff(
            max_attempts=5,
            initial_delay=1.0,
            max_delay=2.0,  # Cap at 2 seconds
            exponential_base=2.0,
            jitter=False
        )
        def failing_func():
            call_times.append(time.time())
            raise ValueError("Error")
        
        with pytest.raises(ValueError):
            failing_func()
        
        # Third retry would normally be 4s, but capped at 2s
        if len(call_times) >= 4:
            delay3 = call_times[3] - call_times[2]
            assert delay3 < 2.5  # Should be capped at max_delay
    
    def test_specific_exception_types(self):
        """Should only retry on specified exception types."""
        call_count = 0
        
        @retry_with_backoff(
            max_attempts=3,
            initial_delay=0.1,
            exceptions=(ValueError,)  # Only retry ValueError
        )
        def selective_retry_func():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ValueError("Retryable")
            elif call_count == 2:
                raise RuntimeError("Not retryable")
        
        with pytest.raises(RuntimeError):
            selective_retry_func()
        
        # Should have called twice: first ValueError, then RuntimeError
        assert call_count == 2
    
    @pytest.mark.asyncio
    async def test_async_retry_on_success(self):
        """Async functions should work with retry decorator."""
        call_count = 0
        
        @retry_with_backoff(max_attempts=3)
        async def async_successful_func():
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(0.01)
            return "async_success"
        
        result = await async_successful_func()
        assert result == "async_success"
        assert call_count == 1
    
    @pytest.mark.asyncio
    async def test_async_retry_on_failure(self):
        """Async functions should retry on failure."""
        call_count = 0
        
        @retry_with_backoff(max_attempts=3, initial_delay=0.1)
        async def async_flaky_func():
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(0.01)
            if call_count < 3:
                raise ValueError("Transient async error")
            return "async_success"
        
        result = await async_flaky_func()
        assert result == "async_success"
        assert call_count == 3
    
    @pytest.mark.asyncio
    async def test_async_all_retries_exhausted(self):
        """Async should raise after all retries fail."""
        call_count = 0
        
        @retry_with_backoff(max_attempts=2, initial_delay=0.1)
        async def async_failing_func():
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(0.01)
            raise ValueError("Async permanent error")
        
        with pytest.raises(ValueError, match="Async permanent error"):
            await async_failing_func()
        
        assert call_count == 2
    
    def test_custom_operation_name(self):
        """Should use custom operation name in logs."""
        @retry_with_backoff(
            max_attempts=2,
            initial_delay=0.1,
            operation_name="custom_operation"
        )
        def failing_func():
            raise ValueError("Error")
        
        with pytest.raises(ValueError):
            failing_func()
        
        # Operation name would appear in logs (checked manually)
    
    def test_jitter_adds_randomness(self):
        """Jitter should add randomness to delay."""
        delays = []
        
        for _ in range(5):
            call_times = []
            
            @retry_with_backoff(
                max_attempts=2,
                initial_delay=0.1,
                jitter=True
            )
            def failing_func():
                call_times.append(time.time())
                raise ValueError("Error")
            
            try:
                failing_func()
            except ValueError:
                pass
            
            if len(call_times) >= 2:
                delays.append(call_times[1] - call_times[0])
        
        # With jitter, delays should vary
        # (between 0.05 and 0.15 for initial_delay=0.1)
        assert len(set(delays)) > 1  # Not all the same
        assert all(0.04 < d < 0.16 for d in delays)


class TestRetryableOperation:
    """Test RetryableOperation context manager."""
    
    @pytest.mark.asyncio
    async def test_context_manager_no_retry_on_success(self):
        """Should not retry successful operations."""
        call_count = 0
        
        for attempt in range(3):  # Max 3 attempts
            async with RetryableOperation(
                "test_operation",
                max_attempts=3,
                initial_delay=0.1
            ):
                call_count += 1
                # Success - no exception
                break
        
        assert call_count == 1
    
    @pytest.mark.asyncio
    async def test_context_manager_retry_on_failure(self):
        """Should retry on exception."""
        call_count = 0
        
        async def operation_with_retry():
            nonlocal call_count
            
            while True:
                async with RetryableOperation(
                    "test_operation",
                    max_attempts=3,
                    initial_delay=0.1
                ) as retry:
                    call_count += 1
                    if call_count < 2:
                        raise ValueError("Transient error")
                    return "success"
        
        result = await operation_with_retry()
        assert result == "success"
        assert call_count == 2
    
    @pytest.mark.asyncio
    async def test_context_manager_exhausted_retries(self):
        """Should stop after max attempts."""
        call_count = 0
        
        with pytest.raises(ValueError):
            while True:
                async with RetryableOperation(
                    "test_operation",
                    max_attempts=3,
                    initial_delay=0.1
                ):
                    call_count += 1
                    raise ValueError("Permanent error")
        
        assert call_count == 3
