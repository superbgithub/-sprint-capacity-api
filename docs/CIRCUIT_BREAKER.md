# Circuit Breaker Pattern

## Overview

The circuit breaker pattern prevents cascading failures by failing fast when external services are unavailable. Instead of continuously attempting to call a failing service, the circuit breaker "opens" and rejects calls immediately, giving the service time to recover.

## Implementation

### Circuit States

1. **CLOSED** (Normal Operation)
   - All requests pass through
   - Failures are counted
   - Transitions to OPEN when failure threshold is reached

2. **OPEN** (Service Unavailable)
   - All requests are rejected immediately with `CircuitBreakerError`
   - No calls are made to the failing service
   - After recovery timeout, transitions to HALF_OPEN

3. **HALF_OPEN** (Testing Recovery)
   - Limited requests are allowed to test if service recovered
   - Success transitions back to CLOSED
   - Failure returns to OPEN

### Configuration

```python
from app.utils.circuit_breaker import CircuitBreaker

breaker = CircuitBreaker(
    failure_threshold=5,      # Open after 5 consecutive failures
    recovery_timeout=60,      # Wait 60 seconds before testing recovery
    expected_exception=Exception,  # Exception type to catch
    name="my_service"        # Name for logging
)
```

## Usage Examples

### Basic Usage

```python
from app.utils.circuit_breaker import CircuitBreaker, CircuitBreakerError

breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=30)

def call_external_service():
    # Your service call here
    pass

try:
    result = breaker.call(call_external_service)
except CircuitBreakerError:
    # Circuit is open, service unavailable
    return fallback_response()
```

### Async Functions

```python
async def call_database():
    async with get_db() as db:
        return await db.execute(query)

try:
    result = await breaker.call_async(call_database)
except CircuitBreakerError:
    # Handle circuit open
    pass
```

### Decorator Pattern

```python
@breaker
async def fetch_data():
    # This function is now protected by circuit breaker
    return await external_api.get("/data")
```

## Protected Services

### Database Circuit Breaker

**Location**: `app.utils.circuit_breaker.database_breaker`

**Configuration**:
- Failure threshold: 5 failures
- Recovery timeout: 60 seconds
- Name: "database"

**Protected Operations**:
- Database session creation (`get_db()`)
- Health checks (`check_db_connection()`)

**Behavior**:
- After 5 consecutive database connection failures, circuit opens
- All database operations are rejected for 60 seconds
- After timeout, one request is allowed to test if database recovered
- If successful, circuit closes and normal operation resumes

### Kafka Circuit Breaker

**Location**: `app.utils.circuit_breaker.kafka_breaker`

**Configuration**:
- Failure threshold: 3 failures
- Recovery timeout: 30 seconds
- Name: "kafka"

**Protected Operations**:
- Event publishing (`publish_event()`)
- All Kafka producer operations

**Behavior**:
- After 3 consecutive Kafka publish failures, circuit opens
- Events are logged but not sent for 30 seconds
- After timeout, circuit tests if Kafka recovered
- Application continues functioning even if Kafka is down

## Benefits

### 1. Prevents Cascading Failures
When a service is down, the circuit breaker prevents your application from wasting resources trying to connect repeatedly.

### 2. Faster Response Times
Instead of waiting for timeouts on every request, the circuit breaker fails immediately when open.

### 3. Automatic Recovery
The circuit breaker automatically tests service recovery without manual intervention.

### 4. Resource Protection
Protects your application from exhausting connection pools or thread pools on failing services.

## Monitoring

Circuit breaker state transitions are logged:

```python
# Opening circuit
logger.error(
    "Circuit breaker 'database' opening circuit",
    extra={
        "circuit_breaker": "database",
        "state": "open",
        "failure_count": 5,
        "threshold": 5
    }
)

# Testing recovery
logger.info(
    "Circuit breaker 'database' transitioning to HALF_OPEN",
    extra={
        "circuit_breaker": "database",
        "state": "half_open",
        "elapsed_seconds": 61.2
    }
)

# Recovered
logger.info(
    "Circuit breaker 'database' recovered, closing circuit",
    extra={"circuit_breaker": "database", "state": "closed"}
)
```

## Error Handling

### CircuitBreakerError

Raised when attempting to call through an OPEN circuit:

```python
from app.utils.circuit_breaker import CircuitBreakerError

try:
    result = await database_breaker.call_async(my_function)
except CircuitBreakerError as e:
    # Circuit is open, provide fallback
    logger.warning(f"Circuit breaker open: {e}")
    return cached_data or default_response
except Exception as e:
    # Actual service error
    logger.error(f"Service error: {e}")
    raise
```

## Testing

Circuit breaker behavior can be tested:

```python
def test_circuit_opens_on_failures():
    breaker = CircuitBreaker(failure_threshold=3)
    
    def failing_func():
        raise ValueError("Service down")
    
    # Cause failures
    for _ in range(3):
        with pytest.raises(ValueError):
            breaker.call(failing_func)
    
    # Circuit should be open
    assert breaker.state == CircuitState.OPEN
    
    # Next call rejected
    with pytest.raises(CircuitBreakerError):
        breaker.call(failing_func)
```

## Best Practices

### 1. Set Appropriate Thresholds
- **High traffic services**: Lower threshold (3-5 failures)
- **Low traffic services**: Higher threshold (10-20 failures)
- Consider false positives from intermittent network issues

### 2. Balance Recovery Timeout
- **Too short**: Constant testing prevents real recovery
- **Too long**: Service unavailability extends unnecessarily
- Recommended: 30-60 seconds for most services

### 3. Provide Fallbacks
Always handle `CircuitBreakerError` with appropriate fallback behavior:
- Return cached data
- Return default/empty response
- Redirect to backup service
- Graceful degradation

### 4. Monitor Circuit State
- Track how often circuits open
- Alert on prolonged OPEN state
- Use metrics to tune thresholds

### 5. Use Per-Service Breakers
Don't share circuit breakers between unrelated services:

```python
# Good - separate breakers
database_breaker = CircuitBreaker(name="database")
redis_breaker = CircuitBreaker(name="redis")
api_breaker = CircuitBreaker(name="external_api")

# Bad - shared breaker
shared_breaker = CircuitBreaker(name="everything")
```

## Integration with Health Checks

Circuit breaker status should be included in health endpoints:

```python
@router.get("/health/detailed")
async def detailed_health():
    return {
        "status": "healthy",
        "database": {
            "circuit_breaker": database_breaker.state.value,
            "failure_count": database_breaker._failure_count
        },
        "kafka": {
            "circuit_breaker": kafka_breaker.state.value,
            "failure_count": kafka_breaker._failure_count
        }
    }
```

## Future Enhancements

Potential improvements:
1. **Metrics Export**: Expose circuit breaker metrics to Prometheus
2. **Adaptive Thresholds**: Automatically adjust based on traffic patterns
3. **Manual Control**: API endpoints to manually open/close circuits
4. **Success Rate Tracking**: Open on success rate drop, not just failure count
5. **Per-Endpoint Breakers**: Fine-grained control for API routes
