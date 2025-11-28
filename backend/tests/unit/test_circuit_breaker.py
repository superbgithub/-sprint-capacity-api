"""
Unit tests for circuit breaker implementation.
"""
import pytest
import asyncio
from datetime import datetime, timedelta

from app.utils.circuit_breaker import (
    CircuitBreaker,
    CircuitState,
    CircuitBreakerError
)


class TestCircuitBreaker:
    """Test circuit breaker functionality."""
    
    def test_initial_state_is_closed(self):
        """Circuit breaker should start in CLOSED state."""
        breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=10)
        assert breaker.state == CircuitState.CLOSED
    
    def test_successful_calls_keep_circuit_closed(self):
        """Successful calls should keep circuit in CLOSED state."""
        breaker = CircuitBreaker(failure_threshold=3)
        
        def success_func():
            return "success"
        
        for _ in range(5):
            result = breaker.call(success_func)
            assert result == "success"
            assert breaker.state == CircuitState.CLOSED
    
    def test_circuit_opens_after_threshold_failures(self):
        """Circuit should open after reaching failure threshold."""
        breaker = CircuitBreaker(failure_threshold=3)
        
        def failing_func():
            raise ValueError("Error")
        
        # Fail threshold times
        for _ in range(3):
            with pytest.raises(ValueError):
                breaker.call(failing_func)
        
        assert breaker.state == CircuitState.OPEN
    
    def test_open_circuit_rejects_calls(self):
        """Open circuit should reject calls immediately."""
        breaker = CircuitBreaker(failure_threshold=2)
        
        def failing_func():
            raise ValueError("Error")
        
        # Open the circuit
        for _ in range(2):
            with pytest.raises(ValueError):
                breaker.call(failing_func)
        
        # Next call should be rejected
        with pytest.raises(CircuitBreakerError):
            breaker.call(failing_func)
    
    def test_circuit_transitions_to_half_open(self):
        """Circuit should transition to HALF_OPEN after recovery timeout."""
        breaker = CircuitBreaker(failure_threshold=2, recovery_timeout=1)
        
        def failing_func():
            raise ValueError("Error")
        
        # Open the circuit
        for _ in range(2):
            with pytest.raises(ValueError):
                breaker.call(failing_func)
        
        assert breaker.state == CircuitState.OPEN
        
        # Wait for recovery timeout
        import time
        time.sleep(1.1)
        
        # Check state - should be HALF_OPEN now
        assert breaker.state == CircuitState.HALF_OPEN
    
    def test_successful_call_closes_half_open_circuit(self):
        """Successful call in HALF_OPEN state should close circuit."""
        breaker = CircuitBreaker(failure_threshold=2, recovery_timeout=1)
        
        def failing_func():
            raise ValueError("Error")
        
        def success_func():
            return "success"
        
        # Open the circuit
        for _ in range(2):
            with pytest.raises(ValueError):
                breaker.call(failing_func)
        
        # Wait for recovery
        import time
        time.sleep(1.1)
        
        # Successful call should close circuit
        result = breaker.call(success_func)
        assert result == "success"
        assert breaker.state == CircuitState.CLOSED
    
    @pytest.mark.asyncio
    async def test_async_circuit_breaker(self):
        """Test circuit breaker with async functions."""
        breaker = CircuitBreaker(failure_threshold=3)
        
        async def async_success():
            await asyncio.sleep(0.01)
            return "async_success"
        
        async def async_failure():
            await asyncio.sleep(0.01)
            raise ValueError("Async error")
        
        # Test successful calls
        result = await breaker.call_async(async_success)
        assert result == "async_success"
        assert breaker.state == CircuitState.CLOSED
        
        # Test failures
        for _ in range(3):
            with pytest.raises(ValueError):
                await breaker.call_async(async_failure)
        
        assert breaker.state == CircuitState.OPEN
        
        # Test rejection
        with pytest.raises(CircuitBreakerError):
            await breaker.call_async(async_success)
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_decorator(self):
        """Test circuit breaker as decorator."""
        breaker = CircuitBreaker(failure_threshold=2, name="test_decorator")
        
        @breaker
        async def decorated_func(should_fail: bool = False):
            if should_fail:
                raise ValueError("Decorated failure")
            return "decorated_success"
        
        # Successful calls
        result = await decorated_func(should_fail=False)
        assert result == "decorated_success"
        
        # Fail to open circuit
        for _ in range(2):
            with pytest.raises(ValueError):
                await decorated_func(should_fail=True)
        
        assert breaker.state == CircuitState.OPEN
        
        # Should reject
        with pytest.raises(CircuitBreakerError):
            await decorated_func(should_fail=False)
    
    def test_circuit_breaker_with_specific_exception(self):
        """Test circuit breaker only catches expected exceptions."""
        breaker = CircuitBreaker(
            failure_threshold=2,
            expected_exception=ValueError
        )
        
        def value_error_func():
            raise ValueError("Expected error")
        
        def runtime_error_func():
            raise RuntimeError("Unexpected error")
        
        # ValueError should count towards threshold
        with pytest.raises(ValueError):
            breaker.call(value_error_func)
        
        # RuntimeError should not be caught
        with pytest.raises(RuntimeError):
            breaker.call(runtime_error_func)
        
        # Only 1 failure counted, circuit still closed
        assert breaker.state == CircuitState.CLOSED
    
    def test_failure_count_resets_on_success(self):
        """Failure count should reset after successful call."""
        breaker = CircuitBreaker(failure_threshold=3)
        
        def failing_func():
            raise ValueError("Error")
        
        def success_func():
            return "success"
        
        # 2 failures (not enough to open)
        for _ in range(2):
            with pytest.raises(ValueError):
                breaker.call(failing_func)
        
        # Success should reset counter
        breaker.call(success_func)
        
        # 2 more failures should not open (counter was reset)
        for _ in range(2):
            with pytest.raises(ValueError):
                breaker.call(failing_func)
        
        assert breaker.state == CircuitState.CLOSED
