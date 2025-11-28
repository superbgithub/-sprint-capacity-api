# Acceptance Tests

This directory contains BDD (Behavior-Driven Development) acceptance tests written in Gherkin format using pytest-bdd.

## Overview

Acceptance tests validate that the Sprint Capacity API meets the business requirements and acceptance criteria. These tests are written in a natural language format that can be understood by both technical and non-technical stakeholders.

## Structure

```
tests/acceptance/
├── features/               # Gherkin feature files (.feature)
│   ├── sprint_management.feature
│   ├── capacity_calculation.feature
│   └── validation_and_errors.feature
├── steps/                  # Step definition implementations
│   ├── test_sprint_management_steps.py
│   ├── test_capacity_calculation_steps.py
│   └── test_validation_and_errors_steps.py
├── conftest.py            # Pytest fixtures and configuration
└── README.md              # This file
```

## Feature Files

### 1. Sprint Management (`sprint_management.feature`)

Tests core sprint CRUD operations:
- **Create Sprint**: Validate sprint creation with valid data
- **Retrieve Sprints**: Get all sprints or specific sprint by ID
- **Update Sprint**: Modify existing sprint information
- **Delete Sprint**: Remove sprints from the system
- **Validation**: Ensure duplicate sprint numbers are rejected
- **Error Handling**: Verify proper 404 responses for non-existent sprints

**Scenarios**: 10 scenarios covering the full lifecycle of sprint management

### 2. Capacity Calculation (`capacity_calculation.feature`)

Tests the capacity calculation engine:
- **Basic Capacity**: Calculate working days excluding weekends
- **Vacations**: Account for team member vacation days
- **Holidays**: Subtract company holidays from capacity
- **Complex Scenarios**: Handle overlapping vacations, multi-day holidays
- **Edge Cases**: Full sprint vacations, zero capacity scenarios
- **Confidence**: Include confidence percentage in calculations

**Scenarios**: 10 scenarios covering various capacity calculation scenarios

### 3. Validation and Error Handling (`validation_and_errors.feature`)

Tests data validation and error responses:
- **Required Fields**: Validate that mandatory fields are enforced
- **Data Types**: Ensure correct data types and formats
- **Range Validation**: Check confidence percentage bounds (0-100)
- **String Lengths**: Validate sprint number and field length limits
- **Date Validation**: Ensure logical date ranges
- **Error Messages**: Verify descriptive error responses

**Scenarios**: 15+ scenarios using scenario outlines for comprehensive validation testing

## Running Acceptance Tests

### Locally

```bash
# Run all acceptance tests
pytest tests/acceptance/ -v

# Run specific feature
pytest tests/acceptance/steps/test_sprint_management_steps.py -v

# Run with Gherkin terminal reporter
pytest tests/acceptance/ -v --gherkin-terminal-reporter

# Generate HTML report
pytest tests/acceptance/ --html=acceptance-report.html --self-contained-html
```

### In CI/CD Pipeline

Acceptance tests run automatically as **Stage 7** in the CI/CD pipeline after:
- Unit Tests
- Contract Tests
- Component Tests
- Functional Tests
- Resiliency Tests

They run before:
- Performance Tests
- Docker Build
- Deployment

## Writing New Scenarios

### 1. Add Feature File

Create or update a `.feature` file in `features/` directory:

```gherkin
Feature: New Feature
  As a [role]
  I want to [action]
  So that [benefit]

  Background:
    Given the API is running
    And the database is clean

  Scenario: Descriptive scenario name
    Given [precondition]
    When [action]
    Then [expected outcome]
    And [additional verification]
```

### 2. Implement Step Definitions

Add corresponding step implementations in `steps/` directory:

```python
from pytest_bdd import scenarios, given, when, then, parsers

scenarios('../features/your_feature.feature')

@given(parsers.parse('I have {item}'))
def setup_item(context, item):
    context['item'] = item

@when('I perform action')
def perform_action(context, test_client):
    response = test_client.post("/endpoint", json=context['item'])
    context['response'] = response

@then(parsers.parse('the result should be {expected}'))
def verify_result(context, expected):
    assert context['response'].status_code == 200
```

## Best Practices

1. **Use Clear Language**: Write scenarios that business stakeholders can understand
2. **One Scenario Per Concept**: Keep scenarios focused on a single behavior
3. **Reusable Steps**: Create generic step definitions that can be reused across scenarios
4. **Arrange-Act-Assert**: Follow the Given-When-Then pattern consistently
5. **Independent Scenarios**: Each scenario should be runnable independently
6. **Clean State**: Use fixtures to ensure clean database state for each test
7. **Descriptive Names**: Use meaningful scenario and step names

## Gherkin Keywords

- **Feature**: High-level description of a software feature
- **Background**: Steps that run before each scenario in the feature
- **Scenario**: Concrete example of business rule implementation
- **Scenario Outline**: Template scenario with multiple examples
- **Given**: Preconditions or setup steps
- **When**: The action or event that triggers the behavior
- **Then**: Expected outcome or result
- **And/But**: Additional steps of the same type

## Example Scenarios

### Simple CRUD Test
```gherkin
Scenario: Create a new sprint
  Given I have valid sprint data with sprint number "25-101"
  When I create a new sprint
  Then the sprint should be created successfully
  And the sprint number should be "25-101"
```

### Parameterized Testing
```gherkin
Scenario Outline: Invalid confidence values
  When I create a sprint with confidence percentage <value>
  Then the request should fail with status code 422

  Examples:
    | value  |
    | -1.0   |
    | 101.0  |
    | 150.0  |
```

### Complex Business Logic
```gherkin
Scenario: Calculate capacity with vacations and holidays
  Given a sprint exists from "2025-12-01" to "2025-12-14"
  And the sprint has 3 team members
  And "Member 1" has vacation from "2025-12-05" to "2025-12-06"
  And the sprint has a holiday on "2025-12-10"
  When I request the capacity calculation
  Then Member 1's capacity should be reduced
  And the total capacity should account for both vacation and holiday
```

## Benefits of Acceptance Tests

1. **Living Documentation**: Feature files serve as up-to-date documentation
2. **Stakeholder Communication**: Non-technical stakeholders can read and validate scenarios
3. **Regression Protection**: Ensure business requirements continue to be met
4. **Test Coverage**: Complement unit tests with end-to-end business scenarios
5. **Traceability**: Link tests directly to acceptance criteria

## Reports and Artifacts

Acceptance tests generate the following artifacts in CI/CD:

- **Console Output**: Scenario execution results with pass/fail status
- **HTML Report**: Detailed test report with timing and error information
- **Gherkin Report**: Human-readable format showing feature execution

Access reports in GitHub Actions artifacts for each build.

## Troubleshooting

### Test Failures

1. Check the step definition implementation
2. Verify database fixtures are working correctly
3. Ensure API endpoints match expected behavior
4. Review error messages in test output

### Adding pytest-bdd

If not installed:
```bash
pip install pytest-bdd
```

### Database Issues

Tests use SQLite in-memory database by default. For PostgreSQL testing:
- Ensure `DATABASE_URL` environment variable is set
- Run `python scripts/init_test_db.py` to initialize schema

## Future Enhancements

- [ ] Add API versioning scenarios
- [ ] Test pagination and filtering
- [ ] Add authentication/authorization scenarios
- [ ] Test webhook notifications
- [ ] Add performance acceptance criteria
- [ ] Implement data-driven testing with external data sources
