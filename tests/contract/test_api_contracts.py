"""
Contract tests for API endpoints.
Validates API request/response schemas match the OpenAPI specification.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from datetime import date


client = TestClient(app)


class TestSprintAPIContract:
    """Test API contracts match OpenAPI spec"""
    
    def test_create_sprint_request_schema(self):
        """Test POST /sprints accepts valid request schema"""
        valid_request = {
            "sprintNumber": "25-01",
            "startDate": "2025-11-26",
            "endDate": "2025-12-09",
            "confidencePercentage": 85.0,
            "teamMembers": [
                {
                    "name": "John Doe",
                    "role": "Developer",
                    "vacations": []
                }
            ],
            "holidays": [
                {
                    "holidayDate": "2025-11-27",
                    "name": "Thanksgiving"
                }
            ]
        }
        
        response = client.post("/v1/sprints", json=valid_request)
        
        assert response.status_code == 201
        data = response.json()
        
        # Validate response schema
        assert "id" in data
        assert "sprintNumber" in data
        assert "sprintName" in data
        assert "sprintDuration" in data
        assert "confidencePercentage" in data
        assert "startDate" in data
        assert "endDate" in data
        assert "teamMembers" in data
        assert "holidays" in data
        assert "createdAt" in data
        assert "updatedAt" in data
    
    def test_create_sprint_missing_required_field(self):
        """Test POST /sprints rejects missing required fields"""
        invalid_request = {
            # Missing sprintNumber
            "startDate": "2025-11-26",
            "endDate": "2025-12-09",
            "teamMembers": [],
            "holidays": []
        }
        
        response = client.post("/v1/sprints", json=invalid_request)
        
        assert response.status_code == 422  # Validation error
    
    def test_create_sprint_invalid_date_format(self):
        """Test POST /sprints rejects invalid date format"""
        invalid_request = {
            "sprintNumber": "25-02",
            "startDate": "26-11-2025",  # Wrong format
            "endDate": "2025-12-09",
            "teamMembers": [
                {
                    "name": "John Doe",
                    "role": "Developer",
                    "vacations": []
                }
            ],
            "holidays": []
        }
        
        response = client.post("/v1/sprints", json=invalid_request)
        
        assert response.status_code == 422
    
    def test_create_sprint_invalid_role(self):
        """Test POST /sprints rejects invalid role"""
        invalid_request = {
            "sprintNumber": "25-03",
            "startDate": "2025-11-26",
            "endDate": "2025-12-09",
            "teamMembers": [
                {
                    "name": "John Doe",
                    "role": "InvalidRole",  # Not in enum
                    "vacations": []
                }
            ],
            "holidays": []
        }
        
        response = client.post("/v1/sprints", json=invalid_request)
        
        assert response.status_code == 422
    
    def test_create_sprint_confidence_out_of_range(self):
        """Test POST /sprints rejects confidence % outside 0-100"""
        invalid_request = {
            "sprintNumber": "25-04",
            "startDate": "2025-11-26",
            "endDate": "2025-12-09",
            "confidencePercentage": 150.0,  # > 100
            "teamMembers": [
                {
                    "name": "John Doe",
                    "role": "Developer",
                    "vacations": []
                }
            ],
            "holidays": []
        }
        
        response = client.post("/v1/sprints", json=invalid_request)
        
        assert response.status_code == 422
    
    def test_get_all_sprints_response_schema(self):
        """Test GET /sprints returns array of sprints"""
        response = client.get("/v1/sprints")
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
    
    def test_get_sprint_by_id_response_schema(self):
        """Test GET /sprints/{id} returns sprint object"""
        # First create a sprint
        create_response = client.post("/v1/sprints", json={
            "sprintNumber": "25-05",
            "startDate": "2025-11-26",
            "endDate": "2025-12-09",
            "confidencePercentage": 85.0,
            "teamMembers": [{"name": "John", "role": "Developer", "vacations": []}],
            "holidays": []
        })
        sprint_id = create_response.json()["id"]
        
        # Get the sprint
        response = client.get(f"/v1/sprints/{sprint_id}")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["id"] == sprint_id
        assert "sprintName" in data
        assert "teamMembers" in data
    
    def test_get_sprint_not_found(self):
        """Test GET /sprints/{id} returns 404 for non-existent sprint"""
        response = client.get("/v1/sprints/non-existent-id")
        
        assert response.status_code == 404
        data = response.json()
        
        assert "detail" in data
        assert "code" in data["detail"]
        assert "message" in data["detail"]
    
    def test_get_capacity_response_schema(self):
        """Test GET /sprints/{id}/capacity returns capacity summary"""
        # Create a sprint
        create_response = client.post("/v1/sprints", json={
            "sprintNumber": "25-12",
            "startDate": "2025-11-26",
            "endDate": "2025-12-09",
            "confidencePercentage": 85.0,
            "teamMembers": [
                {
                    "name": "John Doe",
                    "role": "Developer",
                    "vacations": []
                }
            ],
            "holidays": []
        })
        sprint_id = create_response.json()["id"]
        
        # Get capacity
        response = client.get(f"/v1/sprints/{sprint_id}/capacity")
        
        assert response.status_code == 200
        data = response.json()
        
        # Validate capacity schema
        assert "sprintId" in data
        assert "totalWorkingDays" in data
        assert "totalCapacityDays" in data
        assert "adjustedTotalCapacity" in data
        assert "teamSize" in data
        assert "holidaysCount" in data
        assert "vacationDaysCount" in data
        assert "capacityFormula" in data
        assert "memberCapacity" in data
        assert isinstance(data["memberCapacity"], list)
    
    def test_update_sprint_response_schema(self):
        """Test PUT /sprints/{id} returns updated sprint"""
        # Create a sprint
        create_response = client.post("/v1/sprints", json={
            "sprintNumber": "25-13",
            "startDate": "2025-11-26",
            "endDate": "2025-12-09",
            "confidencePercentage": 100.0,
            "teamMembers": [{"name": "John", "role": "Developer", "vacations": []}],
            "holidays": []
        })
        sprint_id = create_response.json()["id"]
        
        # Update it
        update_response = client.put(f"/v1/sprints/{sprint_id}", json={
            "sprintNumber": "25-14",
            "startDate": "2025-12-01",
            "endDate": "2025-12-10",
            "confidencePercentage": 95.0,
            "teamMembers": [{"name": "Jane", "role": "Tester", "vacations": []}],
            "holidays": []
        })
        
        assert update_response.status_code == 200
        data = update_response.json()
        
        assert data["id"] == sprint_id
        assert data["sprintNumber"] == "25-14"
        assert data["sprintName"] == "Sprint 25-14"
    
    def test_delete_sprint_response(self):
        """Test DELETE /sprints/{id} returns 204"""
        # Create a sprint
        create_response = client.post("/v1/sprints", json={
            "sprintNumber": "25-15",
            "startDate": "2025-11-26",
            "endDate": "2025-12-09",
            "confidencePercentage": 100.0,
            "teamMembers": [{"name": "John", "role": "Developer", "vacations": []}],
            "holidays": []
        })
        sprint_id = create_response.json()["id"]
        
        # Delete it
        response = client.delete(f"/v1/sprints/{sprint_id}")
        
        assert response.status_code == 204
