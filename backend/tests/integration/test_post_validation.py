"""
POST Request Validation Tests
------------------------------
Tests for POST endpoint input validation, sanitization, and business rules.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app


class TestPostValidation:
    """Test POST request validation and error handling"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app, raise_server_exceptions=False)
    
    def test_missing_required_fields(self, client):
        """Test POST request with missing required fields is rejected"""
        invalid_payloads = [
            {},  # Empty payload
            {"sprintNumber": "25-test"},  # Missing other required fields
            {"startDate": "2025-12-01"},  # Missing sprint number
            {"sprintNumber": "25-test", "startDate": "2025-12-01"},  # Missing end date
        ]
        
        for payload in invalid_payloads:
            response = client.post("/v1/sprints", json=payload)
            assert response.status_code == 422, \
                f"Missing required fields should return 422, got {response.status_code}"
            assert "detail" in response.json()
    
    def test_empty_string_values(self, client):
        """Test empty strings in required fields are rejected"""
        response = client.post("/v1/sprints", json={
            "sprintNumber": "",  # Empty string
            "sprintName": "",
            "startDate": "2025-12-01",
            "endDate": "2025-12-14",
            "teamMembers": []
        })
        assert response.status_code == 422
    
    def test_null_values_in_required_fields(self, client):
        """Test null values in required fields are rejected"""
        response = client.post("/v1/sprints", json={
            "sprintNumber": None,
            "sprintName": "Test",
            "startDate": "2025-12-01",
            "endDate": "2025-12-14",
            "teamMembers": []
        })
        assert response.status_code == 422
    
    def test_invalid_data_types(self, client):
        """Test invalid data types are rejected"""
        invalid_payloads = [
            {
                "sprintNumber": 12345,  # Should be string
                "startDate": "2025-12-01",
                "endDate": "2025-12-14",
                "teamMembers": []
            },
            {
                "sprintNumber": "25-test",
                "startDate": "2025-12-01",
                "endDate": "2025-12-14",
                "teamMembers": "not-an-array"  # Should be array
            },
            {
                "sprintNumber": "25-test",
                "startDate": 20251201,  # Should be string
                "endDate": "2025-12-14",
                "teamMembers": []
            },
        ]
        
        for payload in invalid_payloads:
            response = client.post("/v1/sprints", json=payload)
            assert response.status_code == 422, \
                f"Invalid data type should return 422, got {response.status_code}"
    
    def test_extra_fields_handling(self, client):
        """Test extra/unknown fields are handled properly"""
        response = client.post("/v1/sprints", json={
            "sprintNumber": "25-extra",
            "sprintName": "Test Sprint",
            "startDate": "2025-12-01",
            "endDate": "2025-12-14",
            "teamMembers": [],
            "extraField": "should be ignored or rejected",
            "anotherExtra": 12345
        })
        # Should either accept (ignoring extras) or reject with 422
        assert response.status_code in [201, 422]
    
    def test_date_range_validation(self, client):
        """Test end date must be after start date"""
        response = client.post("/v1/sprints", json={
            "sprintNumber": "25-invalid-range",
            "sprintName": "Invalid Range",
            "startDate": "2025-12-14",
            "endDate": "2025-12-01",  # Before start date
            "teamMembers": []
        })
        assert response.status_code == 422
    
    def test_same_start_and_end_date(self, client):
        """Test start and end date cannot be the same"""
        response = client.post("/v1/sprints", json={
            "sprintNumber": "25-same-date",
            "sprintName": "Same Date",
            "startDate": "2025-12-01",
            "endDate": "2025-12-01",  # Same as start
            "teamMembers": []
        })
        # Should be rejected (sprint must have duration)
        assert response.status_code == 422
    
    def test_future_dates_validation(self, client):
        """Test dates in the past are handled appropriately"""
        response = client.post("/v1/sprints", json={
            "sprintNumber": "25-past",
            "sprintName": "Past Sprint",
            "startDate": "2020-01-01",  # Past date
            "endDate": "2020-01-14",
            "teamMembers": []
        })
        # Should accept or reject based on business rules
        # Currently no past date restriction, so should accept
        assert response.status_code in [201, 422]
    
    def test_string_length_limits(self, client):
        """Test extremely long strings are rejected"""
        response = client.post("/v1/sprints", json={
            "sprintNumber": "25-" + "x" * 10000,  # Very long string
            "sprintName": "y" * 10000,
            "startDate": "2025-12-01",
            "endDate": "2025-12-14",
            "teamMembers": []
        })
        assert response.status_code in [422, 413]  # Validation error or payload too large
    
    def test_duplicate_sprint_number(self, client):
        """Test creating sprint with duplicate sprint number"""
        sprint_data = {
            "sprintNumber": "25-duplicate-test",
            "sprintName": "Duplicate Test",
            "startDate": "2025-12-01",
            "endDate": "2025-12-14",
            "teamMembers": []
        }
        
        # Create first sprint
        response1 = client.post("/v1/sprints", json=sprint_data)
        
        if response1.status_code == 201:
            # Try to create duplicate
            response2 = client.post("/v1/sprints", json=sprint_data)
            # Should reject duplicate
            assert response2.status_code in [400, 409, 422]
    
    def test_confidence_percentage_range(self, client):
        """Test confidence percentage must be between 0 and 100"""
        invalid_values = [-1, 101, 150, -50]
        
        for value in invalid_values:
            response = client.post("/v1/sprints", json={
                "sprintNumber": f"25-confidence-{value}",
                "sprintName": "Confidence Test",
                "startDate": "2025-12-01",
                "endDate": "2025-12-14",
                "confidencePercentage": value,
                "teamMembers": []
            })
            assert response.status_code == 422, \
                f"Confidence {value} should be rejected with 422"
    
    def test_valid_confidence_percentage(self, client):
        """Test valid confidence percentage values are accepted"""
        valid_values = [0, 50, 100, 75.5, 99.9]
        
        for value in valid_values:
            response = client.post("/v1/sprints", json={
                "sprintNumber": f"25-valid-conf-{value}",
                "sprintName": "Valid Confidence",
                "startDate": "2025-12-01",
                "endDate": "2025-12-14",
                "confidencePercentage": value,
                "teamMembers": []
            })
            assert response.status_code == 201, \
                f"Valid confidence {value} should be accepted"


class TestTeamMemberValidation:
    """Test team member validation in POST requests"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app, raise_server_exceptions=False)
    
    def test_empty_team_members_array(self, client):
        """Test empty team members array is accepted"""
        response = client.post("/v1/sprints", json={
            "sprintNumber": "25-empty-team",
            "sprintName": "Empty Team",
            "startDate": "2025-12-01",
            "endDate": "2025-12-14",
            "teamMembers": []
        })
        assert response.status_code == 201
    
    def test_team_member_missing_required_fields(self, client):
        """Test team member with missing required fields is rejected"""
        response = client.post("/v1/sprints", json={
            "sprintNumber": "25-invalid-member",
            "sprintName": "Invalid Member",
            "startDate": "2025-12-01",
            "endDate": "2025-12-14",
            "teamMembers": [
                {
                    "name": "John"
                    # Missing role and vacations
                }
            ]
        })
        assert response.status_code == 422
    
    def test_team_member_invalid_role(self, client):
        """Test team member with invalid role is rejected"""
        response = client.post("/v1/sprints", json={
            "sprintNumber": "25-invalid-role",
            "sprintName": "Invalid Role",
            "startDate": "2025-12-01",
            "endDate": "2025-12-14",
            "teamMembers": [
                {
                    "name": "John",
                    "role": "InvalidRole",  # Not in enum
                    "vacations": []
                }
            ]
        })
        assert response.status_code == 422
    
    def test_team_member_valid_roles(self, client):
        """Test all valid team member roles are accepted"""
        valid_roles = ["Developer", "Tester", "Manager", "Designer", "DevOps"]
        
        for role in valid_roles:
            response = client.post("/v1/sprints", json={
                "sprintNumber": f"25-role-{role.lower()}",
                "sprintName": f"Test {role}",
                "startDate": "2025-12-01",
                "endDate": "2025-12-14",
                "teamMembers": [
                    {
                        "name": "Team Member",
                        "role": role,
                        "vacations": []
                    }
                ]
            })
            assert response.status_code == 201, \
                f"Valid role {role} should be accepted"
    
    def test_vacation_date_validation(self, client):
        """Test vacation dates are validated"""
        response = client.post("/v1/sprints", json={
            "sprintNumber": "25-invalid-vacation",
            "sprintName": "Invalid Vacation",
            "startDate": "2025-12-01",
            "endDate": "2025-12-14",
            "teamMembers": [
                {
                    "name": "John",
                    "role": "Developer",
                    "vacations": [
                        {
                            "startDate": "2025-12-10",
                            "endDate": "2025-12-05"  # End before start
                        }
                    ]
                }
            ]
        })
        assert response.status_code == 422
    
    def test_vacation_outside_sprint_dates(self, client):
        """Test vacations outside sprint dates are handled"""
        response = client.post("/v1/sprints", json={
            "sprintNumber": "25-vacation-outside",
            "sprintName": "Vacation Outside",
            "startDate": "2025-12-01",
            "endDate": "2025-12-14",
            "teamMembers": [
                {
                    "name": "John",
                    "role": "Developer",
                    "vacations": [
                        {
                            "startDate": "2025-11-01",  # Before sprint
                            "endDate": "2025-11-05"
                        }
                    ]
                }
            ]
        })
        # Should accept (vacation doesn't overlap) or warn
        assert response.status_code in [201, 422]
    
    def test_multiple_team_members(self, client):
        """Test multiple valid team members are accepted"""
        response = client.post("/v1/sprints", json={
            "sprintNumber": "25-multi-team",
            "sprintName": "Multi Team",
            "startDate": "2025-12-01",
            "endDate": "2025-12-14",
            "teamMembers": [
                {
                    "name": "Alice",
                    "role": "Developer",
                    "vacations": []
                },
                {
                    "name": "Bob",
                    "role": "Tester",
                    "vacations": [
                        {
                            "startDate": "2025-12-05",
                            "endDate": "2025-12-06"
                        }
                    ]
                },
                {
                    "name": "Charlie",
                    "role": "Manager",
                    "vacations": []
                }
            ]
        })
        assert response.status_code == 201


class TestHolidayValidation:
    """Test holiday validation in POST requests"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app, raise_server_exceptions=False)
    
    def test_empty_holidays_array(self, client):
        """Test empty holidays array is accepted"""
        response = client.post("/v1/sprints", json={
            "sprintNumber": "25-no-holidays",
            "sprintName": "No Holidays",
            "startDate": "2025-12-01",
            "endDate": "2025-12-14",
            "teamMembers": [],
            "holidays": []
        })
        assert response.status_code == 201
    
    def test_holiday_missing_fields(self, client):
        """Test holiday with missing required fields is rejected"""
        response = client.post("/v1/sprints", json={
            "sprintNumber": "25-invalid-holiday",
            "sprintName": "Invalid Holiday",
            "startDate": "2025-12-01",
            "endDate": "2025-12-14",
            "teamMembers": [],
            "holidays": [
                {
                    "holidayDate": "2025-12-25"
                    # Missing name
                }
            ]
        })
        assert response.status_code == 422
    
    def test_holiday_invalid_date(self, client):
        """Test holiday with invalid date is rejected"""
        response = client.post("/v1/sprints", json={
            "sprintNumber": "25-bad-holiday-date",
            "sprintName": "Bad Holiday Date",
            "startDate": "2025-12-01",
            "endDate": "2025-12-14",
            "teamMembers": [],
            "holidays": [
                {
                    "holidayDate": "not-a-date",
                    "name": "Invalid Holiday"
                }
            ]
        })
        assert response.status_code == 422
    
    def test_multiple_holidays(self, client):
        """Test multiple holidays are accepted"""
        response = client.post("/v1/sprints", json={
            "sprintNumber": "25-multi-holidays",
            "sprintName": "Multi Holidays",
            "startDate": "2025-12-01",
            "endDate": "2025-12-31",
            "teamMembers": [],
            "holidays": [
                {
                    "holidayDate": "2025-12-25",
                    "name": "Christmas"
                },
                {
                    "holidayDate": "2025-12-31",
                    "name": "New Year's Eve"
                }
            ]
        })
        assert response.status_code == 201
    
    def test_duplicate_holiday_dates(self, client):
        """Test duplicate holiday dates are handled"""
        response = client.post("/v1/sprints", json={
            "sprintNumber": "25-dup-holidays",
            "sprintName": "Duplicate Holidays",
            "startDate": "2025-12-01",
            "endDate": "2025-12-31",
            "teamMembers": [],
            "holidays": [
                {
                    "holidayDate": "2025-12-25",
                    "name": "Christmas"
                },
                {
                    "holidayDate": "2025-12-25",
                    "name": "Christmas Day"
                }
            ]
        })
        # Should accept or reject based on business logic
        assert response.status_code in [201, 422]


class TestContentTypeValidation:
    """Test Content-Type and request format validation"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app, raise_server_exceptions=False)
    
    def test_missing_content_type(self, client):
        """Test POST without Content-Type header"""
        response = client.post(
            "/v1/sprints",
            content='{"sprintNumber": "25-test"}',
            headers={}
        )
        # Should handle gracefully
        assert response.status_code in [422, 415]
    
    def test_wrong_content_type(self, client):
        """Test POST with wrong Content-Type"""
        response = client.post(
            "/v1/sprints",
            content='{"sprintNumber": "25-test"}',
            headers={"Content-Type": "text/plain"}
        )
        # Should reject or handle
        assert response.status_code in [422, 415]
    
    def test_malformed_json(self, client):
        """Test POST with malformed JSON"""
        response = client.post(
            "/v1/sprints",
            content='{"sprintNumber": "25-test", invalid json}',
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422
    
    def test_array_instead_of_object(self, client):
        """Test POST with array instead of object"""
        response = client.post(
            "/v1/sprints",
            json=[
                {
                    "sprintNumber": "25-test",
                    "startDate": "2025-12-01",
                    "endDate": "2025-12-14"
                }
            ]
        )
        assert response.status_code == 422
