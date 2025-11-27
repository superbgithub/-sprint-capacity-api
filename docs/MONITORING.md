# Monitoring and Observability Guide

## Overview

The Sprint Capacity API includes comprehensive monitoring and observability features using industry-standard tools and practices.

## Architecture

```
┌─────────────────┐
│                 │
│   FastAPI App   │◄─── Structured Logging (JSON)
│                 │
└────────┬────────┘
         │
         │ Exposes /metrics
         │
         ▼
┌─────────────────┐
│   Prometheus    │◄─── Scrapes metrics every 10s
│                 │
└────────┬────────┘
         │
         │ Data source
         │
         ▼
┌─────────────────┐
│    Grafana      │◄─── Visualizations & Dashboards
│                 │
└─────────────────┘
```

## Features

### 1. Structured Logging

All application logs are output in JSON format with consistent fields:

```json
{
  "timestamp": "2025-01-09T10:30:45.123Z",
  "level": "INFO",
  "logger": "app.routes.sprints",
  "message": "Sprint created successfully",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "user-123",
  "sprint_id": "sprint-abc",
  "duration_ms": 45.23
}
```

**Benefits:**
- Easy parsing by log aggregation tools (ELK, Splunk, etc.)
- Correlation IDs for distributed tracing
- Structured context for debugging

### 2. Request Tracing

Every request gets a unique request ID:

1. Client sends `X-Request-ID` header (optional)
2. If not provided, middleware generates UUID
3. Request ID is logged with every log entry
4. Response includes `X-Request-ID` header

**Usage:**
```bash
# Include request ID in request
curl -H "X-Request-ID: my-trace-123" http://localhost:8000/v1/sprints

# Response includes the same ID
X-Request-ID: my-trace-123
```

### 3. Prometheus Metrics

The API exposes metrics at `/metrics` in Prometheus format.

#### HTTP Metrics

```promql
# Request rate
rate(http_requests_total[1m])

# 95th percentile latency
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# Requests in progress
http_requests_in_progress
```

#### Business Metrics

```promql
# Sprint creation rate
rate(sprints_created_total[5m])

# Active sprints
active_sprints

# Capacity calculations
rate(sprint_capacity_calculations_total[5m])
```

#### Error Metrics

```promql
# Error rate by type
rate(errors_total[1m])

# Validation errors by field
rate(validation_errors_total[1m])
```

### 4. Health Checks

Multiple health check endpoints for different purposes:

#### Basic Health (`/health`)
- Quick alive check
- Returns uptime
- Use for: Load balancer health checks

#### Detailed Health (`/health/detailed`)
- System metrics (CPU, memory, disk)
- Identifies degraded performance
- Use for: Monitoring dashboards

#### Readiness (`/health/ready`)
- Checks if app can accept traffic
- Validates dependencies
- Use for: Kubernetes readiness probe

#### Liveness (`/health/live`)
- Simple alive check
- Use for: Kubernetes liveness probe

### 5. Performance Monitoring

Middleware automatically tracks slow requests:

```python
# Logged when request exceeds threshold
{
  "level": "WARNING",
  "message": "Slow request detected: GET /v1/sprints/{id}",
  "duration_ms": 1234.56,
  "threshold_ms": 1000
}
```

## Setup

### Local Development

1. **Install dependencies:**
```powershell
pip install -r requirements.txt
```

2. **Run the application:**
```powershell
uvicorn app.main:app --reload
```

3. **View metrics:**
```powershell
curl http://localhost:8000/metrics
```

### Docker Compose Stack

1. **Start all services:**
```powershell
docker-compose up -d
```

2. **Access services:**
- API: http://localhost:8000
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000

3. **Stop services:**
```powershell
docker-compose down
```

4. **View logs:**
```powershell
docker-compose logs -f api
docker-compose logs -f prometheus
docker-compose logs -f grafana
```

## Grafana Dashboard

The pre-built dashboard includes:

1. **Request Rate** - Requests per second by endpoint
2. **Request Duration** - P95/P99 latency by endpoint
3. **HTTP Status Codes** - Distribution of response codes
4. **Error Rate** - Errors per second by type
5. **Requests In Progress** - Active request count
6. **Sprint Operations** - Create/update/delete rates
7. **Active Sprints** - Current sprint count
8. **Validation Errors** - Validation failures by field
9. **Capacity Calculations** - Calculation count
10. **Total Requests** - Request volume
11. **Average Response Time** - Overall latency
12. **Total Errors** - Error count with thresholds

### Accessing the Dashboard

1. Open Grafana: http://localhost:3000
2. Login: `admin` / `admin`
3. Navigate to: Dashboards → Sprint Capacity API - Overview
4. Dashboard auto-refreshes every 10 seconds

### Creating Custom Dashboards

1. Click "+" → Dashboard
2. Add Panel
3. Select Prometheus data source
4. Write PromQL queries
5. Save dashboard

## Monitoring Best Practices

### 1. Logging

**Do:**
- Use structured logging (JSON)
- Include request IDs
- Log at appropriate levels (INFO, WARNING, ERROR)
- Include context (user_id, sprint_id, etc.)

**Don't:**
- Log sensitive data (passwords, tokens)
- Log at DEBUG in production
- Log inside tight loops

### 2. Metrics

**Do:**
- Use counters for things that increase
- Use gauges for current values
- Use histograms for durations
- Label metrics appropriately

**Don't:**
- Create high-cardinality labels (UUIDs, timestamps)
- Create too many metrics (causes memory issues)
- Change metric types

### 3. Alerting

Set up alerts in Prometheus for:

```yaml
# High error rate
- alert: HighErrorRate
  expr: rate(errors_total[5m]) > 0.05
  for: 5m
  annotations:
    summary: "High error rate detected"

# Slow responses
- alert: SlowResponses
  expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 1
  for: 5m
  annotations:
    summary: "95th percentile latency exceeds 1s"

# High memory usage
- alert: HighMemoryUsage
  expr: node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes < 0.1
  for: 10m
  annotations:
    summary: "Available memory below 10%"
```

## Troubleshooting

### Metrics not appearing

1. Check `/metrics` endpoint:
```powershell
curl http://localhost:8000/metrics
```

2. Verify Prometheus is scraping:
- Open http://localhost:9090
- Go to Status → Targets
- Check if `sprint-capacity-api` is UP

3. Check Prometheus configuration:
```powershell
docker-compose exec prometheus cat /etc/prometheus/prometheus.yml
```

### Grafana shows no data

1. Verify Prometheus data source:
- Go to Configuration → Data Sources
- Test Prometheus connection

2. Check query syntax:
- Open panel editor
- Test queries in Prometheus UI first

3. Check time range:
- Ensure time range includes data
- Try "Last 5 minutes"

### Logs not appearing

1. Check log level:
```python
# In app/main.py
setup_logging(log_level="DEBUG")  # More verbose
```

2. View container logs:
```powershell
docker-compose logs -f api
```

3. Verify JSON format:
```powershell
docker-compose logs api | python -m json.tool
```

## Production Considerations

### 1. Log Aggregation

Send logs to centralized system:
- **ELK Stack** (Elasticsearch, Logstash, Kibana)
- **Splunk**
- **Datadog**
- **CloudWatch** (AWS)

### 2. Metrics Storage

Prometheus local storage is limited:
- Use **Prometheus Remote Write** for long-term storage
- Consider **Thanos** or **Cortex** for distributed Prometheus
- Use managed services (CloudWatch, Datadog, New Relic)

### 3. Alerting

Configure alert notifications:
- **Slack** - Team notifications
- **PagerDuty** - On-call escalation
- **Email** - Non-critical alerts

### 4. Security

- Restrict `/metrics` endpoint (authentication)
- Use TLS for Prometheus scraping
- Secure Grafana with OAuth/LDAP
- Don't expose Prometheus/Grafana publicly

### 5. Performance

- Adjust Prometheus scrape interval (default: 10s)
- Use recording rules for expensive queries
- Set appropriate retention periods
- Monitor Prometheus resource usage

## References

- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [OpenTelemetry](https://opentelemetry.io/)
- [The RED Method](https://grafana.com/blog/2018/08/02/the-red-method-how-to-instrument-your-services/)
- [The USE Method](http://www.brendangregg.com/usemethod.html)
