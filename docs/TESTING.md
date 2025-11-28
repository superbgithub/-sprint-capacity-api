# Sprint Capacity Management API - Testing Guide

## Test Suite Overview

This project includes comprehensive testing across multiple levels:

### Test Types

1. **Unit Tests** (`tests/unit/`)
   - Tests individual functions and classes in isolation
   - Fast execution, no external dependencies
   - Coverage: capacity calculations, database operations

2. **Contract Tests** (`tests/contract/`)
   - Validates API request/response schemas match OpenAPI spec
   - Ensures API contract consistency
   - Coverage: all endpoint schemas, validation rules

3. **Component Tests** (`tests/component/`)
   - Tests API endpoints with TestClient
   - Verifies HTTP status codes and response structure
   - Coverage: all CRUD operations, error scenarios

4. **Functional Tests** (`tests/functional/`)
   - End-to-end workflow testing
   - Tests complete user journeys through the API
   - Coverage: sprint lifecycle, multi-sprint management, capacity planning

5. **Resiliency Tests** (`tests/resiliency/`)
   - Error handling and edge cases
   - Boundary conditions and invalid inputs
   - Coverage: concurrent operations, invalid data, stress conditions

6. **Performance Tests** (`tests/performance/`)
   - Load testing with Locust
   - Measures API performance under various load conditions
   - Coverage: throughput, response times, concurrent users

## Running Tests

### Install Test Dependencies

```powershell
pip install -r requirements.txt
```

### Run All Tests

```powershell
# Using pytest directly
pytest tests/ -v

# Using test runner script
python run_tests.py all
```

### Run Specific Test Suites

```powershell
# Unit tests
pytest tests/unit/ -v -m unit
# or
python run_tests.py unit

# Contract tests
pytest tests/contract/ -v -m contract
# or
python run_tests.py contract

# Component tests
pytest tests/component/ -v -m component
# or
python run_tests.py component

# Functional tests
pytest tests/functional/ -v -m functional
# or
python run_tests.py functional

# Resiliency tests
pytest tests/resiliency/ -v -m resiliency
# or
python run_tests.py resiliency
```

### Run Performance Tests

**Prerequisites:** FastAPI server must be running on http://127.0.0.1:8000

```powershell
# Terminal 1: Start the server
uvicorn app.main:app --reload

# Terminal 2: Run performance tests
python run_tests.py performance
# or
locust -f tests/performance/locustfile.py --host=http://127.0.0.1:8000
```

Then open http://localhost:8089 to configure and start the load test.

### Performance Test Scenarios

The Locust file includes two user types:

1. **SprintAPIUser**: Simulates normal API usage
   - Creates, reads, updates, deletes sprints
   - Calculates capacity
   - Weight distribution favors read operations

2. **CapacityHeavyUser**: Simulates capacity-focused workload
   - Creates sprints with large teams (20 members)
   - Repeatedly calculates complex capacity scenarios
   - Stress tests the calculation engine

### Recommended Load Test Configuration

- **Users**: 50-100
- **Spawn Rate**: 10 users/second
- **Duration**: 2-5 minutes

## CI/CD Pipeline

The GitHub Actions workflow (`.github/workflows/ci-cd.yml`) runs all tests automatically:

### Pipeline Stages

1. **Lint**: Code quality checks (Black, isort, Flake8)
2. **Unit Tests**: Fast, isolated tests
3. **Contract Tests**: API schema validation
4. **Component Tests**: Endpoint testing
5. **Functional Tests**: E2E workflows
6. **Resiliency Tests**: Error handling
7. **Performance Tests**: Load testing (main branch only)
8. **Build**: Docker image creation
9. **Deploy**: Deployment placeholder

### Triggering CI/CD

```powershell
# Push to main or develop branch
git push origin main

# Create pull request
gh pr create --base main --head feature-branch
```

## Test Markers

Tests are marked for easy filtering:

```powershell
# Run only unit tests
pytest -m unit

# Run all except slow tests
pytest -m "not slow"

# Run unit and contract tests
pytest -m "unit or contract"
```

## Test Coverage

To generate coverage report:

```powershell
# Install coverage tool
pip install pytest-cov

# Run with coverage
pytest --cov=app --cov-report=html --cov-report=term-missing

# View HTML report
start htmlcov/index.html
```

## Test Data

All tests use in-memory data:
- No database setup required
- Each test starts with clean state
- Data is generated randomly or from fixtures

## Troubleshooting

### Tests Failing with "Connection refused"

Ensure the FastAPI server is NOT running when executing pytest tests. Component/functional/resiliency tests use TestClient which doesn't require a running server.

### Performance Tests Can't Connect

Ensure the FastAPI server IS running:

```powershell
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

### Import Errors

Ensure you're in the project root directory and virtual environment is activated:

```powershell
cd c:\Users\peter\workspace
.\.venv\Scripts\Activate.ps1
```

### Pytest Not Found

Install test dependencies:

```powershell
pip install pytest httpx
```

## Best Practices

1. **Run tests frequently** during development
2. **Use markers** to run relevant test subsets
3. **Check coverage** to identify untested code
4. **Run performance tests** before major releases
5. **Review CI/CD results** on every PR

## Test Metrics

Current test count:
- Unit Tests: 28 tests
- Contract Tests: 12 tests
- Component Tests: 22 tests
- Functional Tests: 12 tests
- Resiliency Tests: 20+ tests
- **Total: 94+ automated tests**

## Future Enhancements

- [ ] Add integration tests with real database
- [ ] Add security tests (OWASP Top 10)
- [ ] Add mutation testing
- [ ] Add visual regression tests for frontend
- [ ] Add chaos engineering tests
