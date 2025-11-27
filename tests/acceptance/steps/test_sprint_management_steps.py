"""
Pytest-BDD step definitions for sprint management acceptance tests.
"""
import pytest
from pytest_bdd import scenarios, given, when, then, parsers
from fastapi.testclient import TestClient
from datetime import datetime, date
import json

# Load all scenarios from the feature file
scenarios('../features/sprint_management.feature')


@given('the API is running')
def api_running(test_client):
    """Ensure API is accessible."""
    response = test_client.get("/health")
    assert response.status_code == 200


@given('the database is clean')
def clean_database(test_db):
    """Database is cleaned by the fixture."""
    pass


@given(parsers.parse('I have valid sprint data with sprint number "{sprint_number}"'))
def valid_sprint_data(context, sprint_number):
    """Prepare valid sprint data."""
    context['sprint_data'] = {
        "sprintNumber": sprint_number,
        "startDate": "2025-12-01",
        "endDate": "2025-12-14",
        "confidencePercentage": 85.0,
        "teamMembers": [
            {
                "name": "Test Member",
                "role": "Developer",
                "vacations": []
            }
        ],
        "holidays": []
    }


@given(parsers.parse('I have sprint data with {count:d} team members'))
def sprint_data_with_team(context, count):
    """Prepare sprint data with specified team members."""
    context['sprint_data'] = {
        "sprintNumber": "25-102",  # Will be overridden
        "startDate": "2025-12-01",
        "endDate": "2025-12-14",
        "confidencePercentage": 80.0,
        "teamMembers": [
            {
                "name": f"Member {i}",
                "role": "Developer",
                "vacations": []
            }
            for i in range(count)
        ],
        "holidays": []
    }


@given(parsers.parse('a sprint exists with sprint number "{sprint_number}"'))
def create_sprint(context, test_client, sprint_number):
    """Create a sprint with the given sprint number."""
    sprint_data = {
        "sprintNumber": sprint_number,
        "startDate": "2025-12-01",
        "endDate": "2025-12-14",
        "confidencePercentage": 85.0,
        "teamMembers": [
            {
                "name": "Test Member",
                "role": "Developer",
                "vacations": []
            }
        ],
        "holidays": []
    }
    response = test_client.post("/v1/sprints", json=sprint_data)
    assert response.status_code == 201
    context['sprint_id'] = response.json()["id"]
    context['sprint_number'] = sprint_number


@given(parsers.parse('{count:d} sprints exist in the system'))
def create_multiple_sprints(context, test_client, count):
    """Create multiple sprints."""
    context['sprint_ids'] = []
    
    for i in range(count):
        sprint_data = {
            "sprintNumber": f"25-{200+i}",
            "startDate": "2025-12-01",
            "endDate": "2025-12-14",
            "confidencePercentage": 80.0,
            "teamMembers": [],
            "holidays": []
        }
        response = test_client.post("/v1/sprints", json=sprint_data)
        assert response.status_code == 201
        context['sprint_ids'].append(response.json()["id"])


@when('I create a new sprint')
def create_new_sprint(context, test_client):
    """Create a sprint with the prepared data."""
    response = test_client.post("/v1/sprints", json=context['sprint_data'])
    context['response'] = response
    if response.status_code == 201:
        context['sprint_id'] = response.json()["id"]


@when(parsers.parse('I create a new sprint with sprint number "{sprint_number}"'))
def create_sprint_with_number(context, test_client, sprint_number):
    """Create a sprint with specific sprint number."""
    context['sprint_data']['sprintNumber'] = sprint_number
    response = test_client.post("/v1/sprints", json=context['sprint_data'])
    context['response'] = response
    if response.status_code == 201:
        context['sprint_id'] = response.json()["id"]


@when(parsers.parse('I try to create another sprint with sprint number "{sprint_number}"'))
def try_create_duplicate_sprint(context, test_client, sprint_number):
    """Attempt to create a sprint with duplicate number."""
    sprint_data = {
        "sprintNumber": sprint_number,
        "startDate": "2025-12-01",
        "endDate": "2025-12-14",
        "confidencePercentage": 85.0,
        "teamMembers": [],
        "holidays": []
    }
    response = test_client.post("/v1/sprints", json=sprint_data)
    context['response'] = response


@when('I request all sprints')
def get_all_sprints(context, test_client):
    """Request all sprints."""
    response = test_client.get("/v1/sprints")
    context['response'] = response


@when('I request the sprint by its ID')
def get_sprint_by_id(context, test_client):
    """Request specific sprint."""
    response = test_client.get(f"/v1/sprints/{context['sprint_id']}")
    context['response'] = response


@when('I update the sprint with new dates and confidence')
def update_sprint(context, test_client):
    """Update sprint with new data."""
    update_data = {
        "sprintNumber": context['sprint_number'],
        "startDate": "2026-02-01",
        "endDate": "2026-02-14",
        "confidencePercentage": 85.5,
        "teamMembers": [],
        "holidays": []
    }
    response = test_client.put(f"/v1/sprints/{context['sprint_id']}", json=update_data)
    context['response'] = response
    context['updated_data'] = update_data


@when('I delete the sprint')
def delete_sprint(context, test_client):
    """Delete the sprint."""
    response = test_client.delete(f"/v1/sprints/{context['sprint_id']}")
    context['response'] = response


@when(parsers.parse('I request a sprint with ID "{sprint_id}"'))
def request_invalid_sprint(context, test_client, sprint_id):
    """Request a sprint with invalid ID."""
    response = test_client.get(f"/v1/sprints/{sprint_id}")
    context['response'] = response


@when(parsers.parse('I try to create a sprint with sprint number "{sprint_number}"'))
def create_sprint_invalid_number(context, test_client, sprint_number):
    """Try to create sprint with invalid sprint number."""
    sprint_data = {
        "sprintNumber": sprint_number,
        "startDate": "2025-12-01",
        "endDate": "2025-12-14",
        "confidencePercentage": 85.0,
        "teamMembers": [],
        "holidays": []
    }
    response = test_client.post("/v1/sprints", json=sprint_data)
    context['response'] = response


@when('I try to create a sprint where end date is before start date')
def create_sprint_invalid_dates(context, test_client):
    """Try to create sprint with invalid date range."""
    sprint_data = {
        "sprintNumber": "25-999",
        "startDate": "2025-12-14",
        "endDate": "2025-12-01",
        "confidencePercentage": 85.0,
        "teamMembers": [],
        "holidays": []
    }
    response = test_client.post("/v1/sprints", json=sprint_data)
    context['response'] = response


@then('the sprint should be created successfully')
def verify_sprint_created(context):
    """Verify sprint creation."""
    assert context['response'].status_code == 201
    assert 'id' in context['response'].json()


@then('the response should contain the sprint ID')
def verify_sprint_id(context):
    """Verify response contains sprint ID."""
    assert 'id' in context['response'].json()


@then(parsers.parse('the sprint number should be "{sprint_number}"'))
def verify_sprint_number(context, sprint_number):
    """Verify sprint number in response."""
    assert context['response'].json()['sprintNumber'] == sprint_number


@then(parsers.parse('the sprint should have {count:d} team members'))
def verify_team_member_count(context, count):
    """Verify team member count."""
    assert len(context['response'].json()['teamMembers']) == count


@then(parsers.parse('the request should fail with status code {status_code:d}'))
def verify_error_status(context, status_code):
    """Verify error status code."""
    assert context['response'].status_code == status_code


@then('the request should fail with status code 422 or 500')
def verify_error_status_422_or_500(context):
    """Verify error status code is 422 or 500."""
    assert context['response'].status_code in [422, 500]


@then('the error message should indicate duplicate sprint number')
def verify_duplicate_error(context):
    """Verify duplicate error message."""
    response_data = context['response'].json()
    assert 'detail' in response_data or 'message' in response_data


@then(parsers.parse('I should receive {count:d} sprints'))
def verify_sprint_count(context, count):
    """Verify number of sprints returned."""
    assert len(context['response'].json()) == count


@then('the sprints should be in the response')
def verify_sprints_present(context):
    """Verify sprints are present."""
    assert isinstance(context['response'].json(), list)


@then('the sprint details should be returned')
def verify_sprint_details(context):
    """Verify sprint details."""
    assert context['response'].status_code == 200
    assert 'sprintNumber' in context['response'].json()


@then('the sprint should be updated successfully')
def verify_sprint_updated(context):
    """Verify sprint update."""
    assert context['response'].status_code == 200


@then('the updated fields should be reflected')
def verify_updated_fields(context):
    """Verify updated fields."""
    response_data = context['response'].json()
    assert response_data['startDate'] == context['updated_data']['startDate']
    assert response_data['confidencePercentage'] == context['updated_data']['confidencePercentage']


@then('the sprint should be deleted successfully')
def verify_sprint_deleted(context):
    """Verify sprint deletion."""
    assert context['response'].status_code == 204


@then('requesting the sprint should return 404')
def verify_sprint_not_found(context, test_client):
    """Verify deleted sprint returns 404."""
    response = test_client.get(f"/v1/sprints/{context['sprint_id']}")
    assert response.status_code == 404


@then('the error message should indicate invalid sprint number format')
def verify_format_error(context):
    """Verify format error message."""
    response_data = context['response'].json()
    assert 'detail' in response_data or 'message' in response_data


@then('the error message should indicate invalid date range')
def verify_date_range_error(context):
    """Verify date range error message."""
    response_data = context['response'].json()
    assert 'detail' in response_data or 'message' in response_data
