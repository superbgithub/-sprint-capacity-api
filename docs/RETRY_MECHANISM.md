# Retry Mechanism with Exponential Backoff

## Overview

The retry mechanism automatically retries failed operations with exponential backoff, helping handle transient failures in external services (database, Kafka, APIs) without manual intervention.

## How It Works

**Exponential Backoff Strategy**:
1. Initial failure triggers first retry after short delay (e.g., 1 second)
2. Each subsequent retry doubles the wait time (1s → 2s → 4s → 8s)
3. Maximum delay is capped to prevent excessive waits
4. Random jitter prevents thundering herd problem
5. After max attempts, raises the original exception

## Usage

### Decorator Pattern (Recommended)

```python
from app.utils.retry import retry_with_backoff

@retry_with_backoff(
    max_attempts=3,
    initial_delay=1.0,
    max_delay=10.0,
    exceptions=(ValueError, ConnectionError)
)
async def fetch_user_data(user_id: str):
    async with httpx.AsyncClient() as client:
        response = await client.get(f"/users/{user_id}")
        return response.json()
```

### Configuration Parameters

```python
@retry_with_backoff(
    max_attempts=3,         # Retry up to 3 times (including initial attempt)
    initial_delay=1.0,      # Wait 1 second before first retry
    max_delay=60.0,         # Cap delays at 60 seconds
    exponential_base=2.0,   # Double delay each retry (2^attempt)
    jitter=True,            # Add randomness to prevent synchronized retries
    exceptions=(Exception,), # Which exceptions trigger retries
    operation_name="custom" # Name for logging (defaults to function name)
)
```

### Context Manager Pattern

```python
from app.utils.retry import RetryableOperation

async def process_data():
    async with RetryableOperation(
        operation_name="data_processing",
        max_attempts=3,
        initial_delay=1.0
    ):
        result = await external_api.process()
        return result
```

## Integrated Retry Policies

### Database Operations

**Location**: `app.config.database.check_db_connection()`

**Configuration**:
```python
@retry_with_backoff(
    max_attempts=3,
    initial_delay=0.5,
    max_delay=5.0,
    operation_name="database_health_check"
)
```

**Behavior**:
- Retries database health checks up to 3 times
- Fast initial retry (0.5s) for quick recovery
- Exponential backoff: 0.5s → 1s → 2s
- Capped at 5 seconds

**Example Scenario**:
```
Attempt 1: Failed (connection timeout)
Wait 0.5s...
Attempt 2: Failed (still connecting)
Wait 1.0s...
Attempt 3: Success (database recovered)
```

### Kafka Event Publishing

**Location**: `app.events.kafka_producer.publish_event()`

**Configuration**:
```python
@retry_with_backoff(
    max_attempts=3,
    initial_delay=1.0,
    max_delay=10.0,
    exceptions=(KafkaError,),
    operation_name="kafka_publish"
)
```

**Behavior**:
- Only retries on `KafkaError` exceptions
- Longer initial delay (1s) for broker recovery
- Exponential backoff: 1s → 2s → 4s
- Capped at 10 seconds

**Example Scenario**:
```
Attempt 1: KafkaError (broker not ready)
Wait 1.2s (with jitter)...
Attempt 2: KafkaError (still recovering)
Wait 2.4s (with jitter)...
Attempt 3: Success (event published)
```

## Retry vs Circuit Breaker

Both patterns work together but serve different purposes:

| Feature | Retry | Circuit Breaker |
|---------|-------|-----------------|
| **Purpose** | Handle transient failures | Prevent cascading failures |
| **When** | Individual requests | System-wide protection |
| **Fails** | After N attempts | After N consecutive failures |
| **Recovery** | Immediate (next request) | After timeout period |
| **Use Case** | Network glitch, temporary overload | Service down, sustained failures |

**Combined Strategy**:
```
Request → Retry (3 attempts with backoff) → Circuit Breaker (track failures)
```

1. **Retry handles**: Brief network issues, temporary timeouts
2. **Circuit breaker handles**: Sustained outages, dead services

## Examples

### HTTP API Calls

```python
@retry_with_backoff(
    max_attempts=3,
    initial_delay=1.0,
    exceptions=(httpx.HTTPError, httpx.TimeoutException)
)
async def call_external_api(endpoint: str):
    async with httpx.AsyncClient() as client:
        response = await client.get(endpoint, timeout=5.0)
        response.raise_for_status()
        return response.json()
```

### Database Queries

```python
@retry_with_backoff(
    max_attempts=3,
    initial_delay=0.5,
    exceptions=(asyncpg.PostgresError,)
)
async def fetch_user(user_id: int):
    async with get_db() as db:
        result = await db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()
```

### File Operations

```python
@retry_with_backoff(
    max_attempts=5,
    initial_delay=0.5,
    exceptions=(IOError, OSError)
)
def write_file(path: str, content: str):
    with open(path, 'w') as f:
        f.write(content)
```

## Logging

Retry operations are automatically logged:

**Retry Attempt (Warning)**:
```json
{
  "level": "WARNING",
  "message": "Retry attempt 2/3 failed for kafka_publish, waiting 2.15s",
  "operation": "kafka_publish",
  "attempt": 2,
  "max_attempts": 3,
  "delay_seconds": 2.15,
  "error": "KafkaError: Broker not available"
}
```

**Success After Retry (Info)**:
```json
{
  "level": "INFO",
  "message": "Retry succeeded for database_health_check",
  "operation": "database_health_check",
  "attempt": 2,
  "max_attempts": 3
}
```

**All Retries Exhausted (Error)**:
```json
{
  "level": "ERROR",
  "message": "All retry attempts exhausted for kafka_publish",
  "operation": "kafka_publish",
  "attempts": 3,
  "error": "KafkaError: Connection refused"
}
```

## Best Practices

### 1. Choose Appropriate Max Attempts
```python
# Fast operations (< 1s): 3-5 attempts
@retry_with_backoff(max_attempts=3)
async def quick_api_call(): ...

# Slow operations (> 5s): 2-3 attempts
@retry_with_backoff(max_attempts=2)
async def large_file_upload(): ...
```

### 2. Set Realistic Timeouts
```python
# Don't retry forever - set max_delay
@retry_with_backoff(
    max_attempts=5,
    initial_delay=1.0,
    max_delay=30.0  # Cap at 30 seconds
)
```

### 3. Retry Only Transient Errors
```python
# Good - Only retry transient errors
@retry_with_backoff(
    exceptions=(ConnectionError, TimeoutError)
)

# Bad - Don't retry permanent errors
@retry_with_backoff(
    exceptions=(Exception,)  # Too broad!
)
```

### 4. Use Jitter in Production
```python
# Always enable jitter to prevent thundering herd
@retry_with_backoff(
    jitter=True  # Default, but be explicit
)
```

### 5. Monitor Retry Metrics
```python
# Track retry success rate
retry_success_count = Counter("retry_success_total")
retry_failure_count = Counter("retry_failure_total")
```

## Common Patterns

### Idempotent Operations Only
```python
# Safe to retry (idempotent)
@retry_with_backoff()
async def get_user(id: int):  # Read operation
    return await db.fetch_one(...)

# UNSAFE to retry (not idempotent)
# @retry_with_backoff()  # DON'T DO THIS!
async def create_payment(amount: float):  # Write operation
    await payment_api.charge(amount)  # Could charge multiple times!
```

### Retry with Fallback
```python
@retry_with_backoff(max_attempts=3)
async def fetch_from_primary():
    return await primary_db.fetch()

async def fetch_with_fallback():
    try:
        return await fetch_from_primary()
    except Exception:
        logger.warning("Primary failed, using fallback")
        return await secondary_db.fetch()
```

### Conditional Retry
```python
def is_retryable_error(error: Exception) -> bool:
    """Only retry on specific error codes."""
    if isinstance(error, HTTPError):
        return error.status_code in (408, 429, 500, 502, 503, 504)
    return False

@retry_with_backoff(
    exceptions=(HTTPError,)
)
async def api_call():
    try:
        return await client.get("/data")
    except HTTPError as e:
        if not is_retryable_error(e):
            raise  # Don't retry
        raise  # Retry
```

## Exponential Backoff Calculation

**Formula**: `delay = min(initial_delay * (base ^ attempt), max_delay)`

**With Jitter**: `delay = delay * (0.5 + random())`

**Example Timeline** (initial=1s, base=2, max=30s):
```
Attempt 1: Immediate
Attempt 2: 1s delay    (1 * 2^0)
Attempt 3: 2s delay    (1 * 2^1)
Attempt 4: 4s delay    (1 * 2^2)
Attempt 5: 8s delay    (1 * 2^3)
Attempt 6: 16s delay   (1 * 2^4)
Attempt 7: 30s delay   (capped at max_delay)
```

**With Jitter** (adds 50-150% randomness):
```
Attempt 2: 0.5-1.5s
Attempt 3: 1.0-3.0s
Attempt 4: 2.0-6.0s
Attempt 5: 4.0-12.0s
```

## Testing Retry Logic

```python
from unittest.mock import Mock, patch

def test_retry_succeeds_on_second_attempt():
    call_count = 0
    
    @retry_with_backoff(max_attempts=3, initial_delay=0.1)
    def flaky_function():
        nonlocal call_count
        call_count += 1
        if call_count < 2:
            raise ConnectionError("Temporary failure")
        return "success"
    
    result = flaky_function()
    assert result == "success"
    assert call_count == 2

def test_retry_exhausts_all_attempts():
    @retry_with_backoff(max_attempts=3, initial_delay=0.1)
    def always_fails():
        raise ValueError("Permanent error")
    
    with pytest.raises(ValueError):
        always_fails()
```

## Performance Considerations

**Total Time with Retries**:
```
max_time = sum of all delays + (max_attempts * operation_time)
```

**Example** (3 attempts, 1s initial, exponential):
```
Attempt 1: 0s + 5s (operation) = 5s
Attempt 2: 1s + 5s = 6s
Attempt 3: 2s + 5s = 7s
Total: 18 seconds
```

**Recommendation**: Set timeouts on operations to prevent long retry cycles:
```python
@retry_with_backoff(max_attempts=3)
async def fetch_with_timeout():
    async with httpx.AsyncClient(timeout=5.0) as client:
        return await client.get("/data")
```

## When NOT to Use Retries

1. **Validation Errors**: Bad input won't fix itself
2. **Authentication Failures**: Invalid credentials need user action
3. **Resource Not Found**: 404 errors won't change
4. **Rate Limiting**: Use exponential backoff OR respect Retry-After header
5. **Non-Idempotent Operations**: Payment processing, order creation

## Future Enhancements

Potential improvements:
1. **Adaptive Retry**: Adjust based on success rate
2. **Retry Budget**: Global limit on retry attempts
3. **Dead Letter Queue**: Store failed operations for later
4. **Metrics Integration**: Export retry stats to Prometheus
5. **Retry Headers**: Respect HTTP Retry-After headers
