# Team Capacity Management API

A REST API for managing team capacity planning across sprints, built with Python FastAPI.

## Project Structure

```
workspace/
├── app/
│   ├── __init__.py
│   ├── main.py                    # Main FastAPI application
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py             # Data models (Sprint, TeamMember, etc.)
│   ├── routes/
│   │   ├── __init__.py
│   │   └── sprints.py             # API endpoints
│   └── services/
│       ├── __init__.py
│       ├── capacity_service.py    # Capacity calculation logic
│       └── database.py            # In-memory data storage
├── openapi.yaml                   # OpenAPI specification
└── requirements.txt               # Python dependencies
```

## Setup Instructions

### 1. Install Python Dependencies

```powershell
pip install -r requirements.txt
```

### 2. Run the Server

```powershell
python -m app.main
```

Or using uvicorn directly:

```powershell
uvicorn app.main:app --reload
```

The server will start on: **http://localhost:8000**

### 3. Access the API Documentation

FastAPI automatically generates interactive API documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## API Endpoints

### Sprints

- `GET /v1/sprints` - Get all sprints (with optional date filters)
- `POST /v1/sprints` - Create a new sprint
- `GET /v1/sprints/{sprintId}` - Get a specific sprint
- `PUT /v1/sprints/{sprintId}` - Update a sprint
- `DELETE /v1/sprints/{sprintId}` - Delete a sprint

### Capacity

- `GET /v1/sprints/{sprintId}/capacity` - Get capacity calculation for a sprint

## Example Usage

### Create a Sprint

```bash
curl -X POST "http://localhost:8000/v1/sprints" \
  -H "Content-Type: application/json" \
  -d '{
    "sprintName": "Sprint 2025-01",
    "sprintDuration": 14,
    "startDate": "2025-01-06",
    "endDate": "2025-01-19",
    "teamMembers": [
      {
        "name": "John Doe",
        "role": "Developer",
        "email": "john.doe@example.com",
        "confidencePercentage": 85.0,
        "vacations": [
          {
            "startDate": "2025-01-10",
            "endDate": "2025-01-12",
            "reason": "Personal leave"
          }
        ]
      }
    ],
    "holidays": [
      {
        "date": "2025-01-01",
        "name": "New Year Day"
      }
    ]
  }'
```

### Get Capacity Summary

```bash
curl -X GET "http://localhost:8000/v1/sprints/{sprintId}/capacity"
```

## Capacity Calculation

The capacity is calculated using the following logic:

1. **Working Days**: Count weekdays between sprint start and end dates, excluding weekends (Sat/Sun) and holidays
2. **Available Days**: For each team member, subtract their vacation days from total working days
3. **Adjusted Capacity**: Apply confidence percentage: `availableDays * (confidencePercentage / 100)`
4. **Total Capacity**: Sum all team members' adjusted capacity

### Formula Location

The capacity calculation formula is in: `app/services/capacity_service.py`

To modify the formula, edit the `calculate_capacity()` function in that file.

## Data Storage

This POC uses **in-memory storage** (Python dictionary) for simplicity. Data will be lost when the server restarts.

For production, replace `app/services/database.py` with a real database:
- PostgreSQL (with SQLAlchemy)
- MongoDB (with Motor)
- SQLite (for local development)

## Testing

This project includes comprehensive automated testing:

### Quick Start

```powershell
# Run all tests
pytest tests/ -v

# Run specific test suite
pytest tests/unit/ -v          # Unit tests
pytest tests/contract/ -v      # Contract tests
pytest tests/component/ -v     # Component tests
pytest tests/functional/ -v    # Functional tests
pytest tests/resiliency/ -v    # Resiliency tests

# Run performance tests (requires server running)
python run_tests.py performance
```

### Test Coverage

- **Unit Tests**: 28 tests - Capacity calculations, database operations
- **Contract Tests**: 12 tests - API schema validation
- **Component Tests**: 22 tests - Endpoint testing with various scenarios
- **Functional Tests**: 12 tests - End-to-end workflows
- **Resiliency Tests**: 20+ tests - Error handling, edge cases, concurrent operations
- **Performance Tests**: Load testing with Locust

**Total: 94+ automated tests**

See [TESTING.md](TESTING.md) for detailed testing guide.

## CI/CD Pipeline

GitHub Actions workflow automatically runs on every push and PR:

1. **Lint** - Code quality checks
2. **Unit Tests** - Fast isolated tests
3. **Contract Tests** - API contract validation
4. **Component Tests** - Endpoint testing
5. **Functional Tests** - E2E workflows
6. **Resiliency Tests** - Error scenarios
7. **Performance Tests** - Load testing (main branch)
8. **Build** - Docker image creation
9. **Deploy** - Ready for deployment

## Monitoring and Observability

The API includes comprehensive monitoring with structured logging and Prometheus metrics.

### Features

- **Structured JSON Logging**: All logs in JSON format with correlation IDs
- **Request Tracing**: Automatic X-Request-ID generation and propagation
- **Prometheus Metrics**: HTTP requests, business operations, errors
- **Health Checks**: Multiple endpoints for different use cases
- **Grafana Dashboards**: Pre-built visualization dashboards

### Health Check Endpoints

- `GET /health` - Basic health status
- `GET /health/detailed` - Detailed system metrics (CPU, memory, disk)
- `GET /health/ready` - Readiness check (for Kubernetes)
- `GET /health/live` - Liveness check (for Kubernetes)
- `GET /metrics` - Prometheus metrics endpoint

### Metrics Collected

**HTTP Metrics:**
- `http_requests_total` - Total HTTP requests by method, endpoint, status
- `http_request_duration_seconds` - Request duration histogram
- `http_requests_in_progress` - Currently processing requests

**Business Metrics:**
- `sprints_created_total` - Total sprints created
- `sprints_updated_total` - Total sprints updated
- `sprints_deleted_total` - Total sprints deleted
- `sprint_capacity_calculations_total` - Total capacity calculations

**Error Metrics:**
- `errors_total` - Total errors by type and endpoint
- `validation_errors_total` - Validation errors by field

**System Metrics:**
- `active_sprints` - Number of active sprints
- `database_connections` - Active database connections

### Running with Docker Compose

Start the full monitoring stack (API + Prometheus + Grafana):

```powershell
docker-compose up -d
```

Access the services:
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Metrics**: http://localhost:8000/metrics
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000 (admin/admin)

### Grafana Setup

1. Login to Grafana at http://localhost:3000
2. Default credentials: `admin` / `admin`
3. Dashboard is auto-provisioned: "Sprint Capacity API - Overview"
4. Prometheus datasource is pre-configured

### Viewing Logs

The application outputs structured JSON logs:

```json
{
  "timestamp": "2025-01-09T10:30:45.123Z",
  "level": "INFO",
  "logger": "app.routes.sprints",
  "message": "Request completed: POST /v1/sprints",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "method": "POST",
  "endpoint": "/v1/sprints",
  "status_code": 201,
  "duration_ms": 45.23
}
```

Filter logs by request ID to trace a request through the system.

## Docker Support

### Build Docker Image

```powershell
docker build -t sprint-capacity-api .
```

### Run Docker Container

```powershell
docker run -d -p 8000:8000 --name sprint-api sprint-capacity-api
```

### Test Docker Container

```powershell
curl http://localhost:8000/health
```

## Project Status

1. ✅ API specification created (OpenAPI 3.0)
2. ✅ Server code implemented (FastAPI + Python)
3. ✅ Frontend application (React)
4. ✅ Comprehensive test suite (94+ tests)
5. ✅ CI/CD pipeline (GitHub Actions)
6. ✅ Docker containerization
7. ✅ Monitoring and observability (Prometheus + Grafana)
8. ⏳ Production deployment (pending)
9. ⏳ Blue/green deployment (paused)
