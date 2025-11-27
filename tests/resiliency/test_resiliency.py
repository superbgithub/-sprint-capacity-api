"""
Resiliency tests for error handling and edge cases.
Tests system behavior under stress and with invalid inputs.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from concurrent.futures import ThreadPoolExecutor, as_completed
import time


@pytest.fixture
def client():
    """Create TestClient for each test"""
    return TestClient(app)


class TestBoundaryConditions:
    """Test boundary values and edge cases"""
    
    def test_zero_duration_sprint(self, client):
        """Test sprint with 0 duration"""
        sprint_data = {
            "sprintName": "Zero Duration",
            "sprintDuration": 0,
            "startDate": "2025-12-01",
            "endDate": "2025-12-01",
            "teamMembers": []
        }
        
        response = client.post("/v1/sprints", json=sprint_data)
        
        # Should accept but capacity should be 0
        if response.status_code == 201:
            sprint_id = response.json()["id"]
            capacity = client.get(f"/v1/sprints/{sprint_id}/capacity").json()
            assert capacity["totalWorkingDays"] == 0
    
    def test_very_long_sprint(self, client):
        """Test sprint with very long duration (365 days)"""
        sprint_data = {
            "sprintName": "Year Long Sprint",
            "sprintDuration": 365,
            "startDate": "2025-01-01",
            "endDate": "2025-12-31",
            "teamMembers": [
                {
                    "name": "Test Member",
                    "role": "Developer",
                    "confidencePercentage": 100.0
                }
            ]
        }
        
        response = client.post("/v1/sprints", json=sprint_data)
        
        assert response.status_code == 201
        sprint_id = response.json()["id"]
        
        # Capacity calculation should handle large date range
        capacity_response = client.get(f"/v1/sprints/{sprint_id}/capacity")
        assert capacity_response.status_code == 200
        capacity = capacity_response.json()
        assert capacity["totalWorkingDays"] > 200  # Approximately 260 working days in a year
    
    def test_large_team_size(self, client):
        """Test sprint with 100 team members"""
        team_members = [
            {
                "name": f"Member {i}",
                "role": "Developer",
                "confidencePercentage": 80.0 + (i % 20)
            }
            for i in range(100)
        ]
        
        sprint_data = {
            "sprintName": "Large Team Sprint",
            "sprintDuration": 10,
            "startDate": "2025-12-01",
            "endDate": "2025-12-10",
            "teamMembers": team_members
        }
        
        response = client.post("/v1/sprints", json=sprint_data)
        
        assert response.status_code == 201
        sprint_id = response.json()["id"]
        
        # Capacity calculation should handle large team
        capacity_response = client.get(f"/v1/sprints/{sprint_id}/capacity")
        assert capacity_response.status_code == 200
        capacity = capacity_response.json()
        assert capacity["teamSize"] == 100
        assert len(capacity["memberCapacity"]) == 100
    
    def test_many_holidays(self, client):
        """Test sprint with many holidays (all working days)"""
        holidays = [
            {
                "holidayDate": f"2025-12-{str(i).zfill(2)}",
                "name": f"Holiday {i}"
            }
            for i in range(1, 11)  # 10 days
        ]
        
        sprint_data = {
            "sprintName": "All Holidays Sprint",
            "sprintDuration": 10,
            "startDate": "2025-12-01",
            "endDate": "2025-12-10",
            "teamMembers": [
                {
                    "name": "Test Member",
                    "role": "Developer",
                    "confidencePercentage": 100.0
                }
            ],
            "holidays": holidays
        }
        
        response = client.post("/v1/sprints", json=sprint_data)
        
        assert response.status_code == 201
        sprint_id = response.json()["id"]
        
        capacity = client.get(f"/v1/sprints/{sprint_id}/capacity").json()
        # Should have minimal capacity due to holidays
        assert capacity["holidaysCount"] == 10
    
    def test_overlapping_vacations(self, client):
        """Test member with overlapping vacation periods"""
        sprint_data = {
            "sprintName": "Overlapping Vacations",
            "sprintDuration": 14,
            "startDate": "2025-12-01",
            "endDate": "2025-12-14",
            "teamMembers": [
                {
                    "name": "Test Member",
                    "role": "Developer",
                    "confidencePercentage": 100.0,
                    "vacations": [
                        {
                            "startDate": "2025-12-05",
                            "endDate": "2025-12-08"
                        },
                        {
                            "startDate": "2025-12-07",
                            "endDate": "2025-12-10"
                        }
                    ]
                }
            ]
        }
        
        response = client.post("/v1/sprints", json=sprint_data)
        
        assert response.status_code == 201
        sprint_id = response.json()["id"]
        
        # Should handle overlapping vacations gracefully
        capacity_response = client.get(f"/v1/sprints/{sprint_id}/capacity")
        assert capacity_response.status_code == 200
    
    def test_confidence_at_boundaries(self, client):
        """Test confidence percentage at 0% and 100%"""
        sprint_data = {
            "sprintName": "Boundary Confidence",
            "sprintDuration": 10,
            "startDate": "2025-12-01",
            "endDate": "2025-12-10",
            "teamMembers": [
                {
                    "name": "Zero Confidence",
                    "role": "Developer",
                    "confidencePercentage": 0.0
                },
                {
                    "name": "Full Confidence",
                    "role": "Developer",
                    "confidencePercentage": 100.0
                }
            ]
        }
        
        response = client.post("/v1/sprints", json=sprint_data)
        
        assert response.status_code == 201
        sprint_id = response.json()["id"]
        
        capacity = client.get(f"/v1/sprints/{sprint_id}/capacity").json()
        members = {m["memberName"]: m for m in capacity["memberCapacity"]}
        
        assert members["Zero Confidence"]["adjustedCapacity"] == 0.0
        assert members["Full Confidence"]["adjustedCapacity"] > 0


class TestConcurrentOperations:
    """Test concurrent requests and race conditions"""
    
    def test_concurrent_sprint_creation(self, client):
        """Test creating multiple sprints concurrently"""
        def create_sprint(index):
            sprint_data = {
                "sprintName": f"Concurrent Sprint {index}",
                "sprintDuration": 10,
                "startDate": "2025-12-01",
                "endDate": "2025-12-10",
                "teamMembers": []
            }
            return client.post("/v1/sprints", json=sprint_data)
        
        # Create 10 sprints concurrently
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(create_sprint, i) for i in range(10)]
            responses = [f.result() for f in as_completed(futures)]
        
        # All should succeed
        success_count = sum(1 for r in responses if r.status_code == 201)
        assert success_count == 10
        
        # All should have unique IDs
        sprint_ids = [r.json()["id"] for r in responses]
        assert len(set(sprint_ids)) == 10
    
    def test_concurrent_updates(self, client):
        """Test updating same sprint concurrently"""
        # Create a sprint first
        sprint_data = {
            "sprintName": "Update Target",
            "sprintDuration": 10,
            "startDate": "2025-12-01",
            "endDate": "2025-12-10",
            "teamMembers": []
        }
        
        create_response = client.post("/v1/sprints", json=sprint_data)
        sprint_id = create_response.json()["id"]
        
        def update_sprint(index):
            updated_data = sprint_data.copy()
            updated_data["sprintName"] = f"Updated Name {index}"
            return client.put(f"/v1/sprints/{sprint_id}", json=updated_data)
        
        # Update concurrently
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(update_sprint, i) for i in range(5)]
            responses = [f.result() for f in as_completed(futures)]
        
        # All updates should succeed (last write wins)
        success_count = sum(1 for r in responses if r.status_code == 200)
        assert success_count == 5
    
    def test_concurrent_capacity_calculations(self, client):
        """Test calculating capacity concurrently for same sprint"""
        # Create sprint with team
        sprint_data = {
            "sprintName": "Capacity Test",
            "sprintDuration": 14,
            "startDate": "2025-12-01",
            "endDate": "2025-12-14",
            "teamMembers": [
                {
                    "name": "Member 1",
                    "role": "Developer",
                    "confidencePercentage": 90.0
                },
                {
                    "name": "Member 2",
                    "role": "Tester",
                    "confidencePercentage": 85.0
                }
            ]
        }
        
        create_response = client.post("/v1/sprints", json=sprint_data)
        sprint_id = create_response.json()["id"]
        
        def get_capacity():
            return client.get(f"/v1/sprints/{sprint_id}/capacity")
        
        # Calculate capacity concurrently
        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(get_capacity) for _ in range(20)]
            responses = [f.result() for f in as_completed(futures)]
        
        # All should succeed with same result
        assert all(r.status_code == 200 for r in responses)
        
        # All should return consistent capacity
        capacities = [r.json()["adjustedTotalCapacity"] for r in responses]
        assert len(set(capacities)) == 1  # All same value


class TestInvalidInputs:
    """Test handling of various invalid inputs"""
    
    def test_invalid_date_formats(self, client):
        """Test various invalid date formats"""
        invalid_dates = [
            "12/01/2025",  # Wrong format
            "2025-13-01",  # Invalid month
            "2025-12-32",  # Invalid day
            "not-a-date",  # Complete nonsense
            "2025-02-30",  # Invalid date (Feb 30)
        ]
        
        for invalid_date in invalid_dates:
            sprint_data = {
                "sprintName": "Invalid Date Test",
                "sprintDuration": 10,
                "startDate": invalid_date,
                "endDate": "2025-12-10",
                "teamMembers": []
            }
            
            response = client.post("/v1/sprints", json=sprint_data)
            assert response.status_code == 422
    
    def test_end_date_before_start_date(self, client):
        """Test sprint with end date before start date"""
        sprint_data = {
            "sprintName": "Backwards Sprint",
            "sprintDuration": 10,
            "startDate": "2025-12-10",
            "endDate": "2025-12-01",  # Before start date
            "teamMembers": []
        }
        
        response = client.post("/v1/sprints", json=sprint_data)
        
        # Should reject with 400 (bad request), 422 (validation), or handle gracefully (201)
        assert response.status_code in [201, 400, 422]
    
    def test_negative_confidence(self, client):
        """Test negative confidence percentage"""
        sprint_data = {
            "sprintName": "Negative Confidence",
            "sprintDuration": 10,
            "startDate": "2025-12-01",
            "endDate": "2025-12-10",
            "teamMembers": [
                {
                    "name": "Test",
                    "role": "Developer",
                    "confidencePercentage": -50.0  # Negative
                }
            ]
        }
        
        response = client.post("/v1/sprints", json=sprint_data)
        assert response.status_code == 422
    
    def test_very_long_strings(self, client):
        """Test extremely long string inputs"""
        sprint_data = {
            "sprintName": "A" * 10000,  # Very long name
            "sprintDuration": 10,
            "startDate": "2025-12-01",
            "endDate": "2025-12-10",
            "teamMembers": [
                {
                    "name": "B" * 10000,  # Very long member name
                    "role": "Developer",
                    "confidencePercentage": 80.0
                }
            ]
        }
        
        response = client.post("/v1/sprints", json=sprint_data)
        
        # Should handle gracefully (accept or reject with proper error)
        assert response.status_code in [201, 422, 413]
    
    def test_special_characters_in_names(self, client):
        """Test special characters and unicode in names"""
        special_names = [
            "Sprint with émojis 🚀",
            "Name with <script>alert('xss')</script>",
            "Name with\nnewlines\nand\ttabs",
            "Name with 中文字符",
            "Name with Ñoño",
        ]
        
        for name in special_names:
            sprint_data = {
                "sprintName": name,
                "sprintDuration": 10,
                "startDate": "2025-12-01",
                "endDate": "2025-12-10",
                "teamMembers": []
            }
            
            response = client.post("/v1/sprints", json=sprint_data)
            
            # Should accept valid unicode, reject malicious input
            assert response.status_code in [201, 422]


class TestErrorPropagation:
    """Test error handling and error message quality"""
    
    def test_error_response_format(self, client):
        """Test that error responses follow consistent format"""
        # Trigger a validation error
        response = client.post("/v1/sprints", json={"invalid": "data"})
        
        assert response.status_code == 422
        data = response.json()
        
        # Pydantic validation errors have 'detail' field
        assert "detail" in data
    
    def test_not_found_error_details(self, client):
        """Test that 404 errors include helpful details"""
        response = client.get("/v1/sprints/non-existent-id")
        
        assert response.status_code == 404
        data = response.json()
        
        assert "detail" in data
        assert "code" in data["detail"]
        assert "message" in data["detail"]
        assert data["detail"]["code"] == "NOT_FOUND"
    
    def test_multiple_validation_errors(self, client):
        """Test handling of multiple validation errors at once"""
        sprint_data = {
            "sprintName": "",  # Empty name (might be invalid)
            "sprintDuration": -5,  # Negative duration
            "startDate": "invalid-date",
            "endDate": "also-invalid",
            "teamMembers": [
                {
                    "name": "",
                    "role": "InvalidRole",
                    "confidencePercentage": 150.0
                }
            ]
        }
        
        response = client.post("/v1/sprints", json=sprint_data)
        
        assert response.status_code == 422
        data = response.json()
        
        # Should report multiple errors
        assert "detail" in data
