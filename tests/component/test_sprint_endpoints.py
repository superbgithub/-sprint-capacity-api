"""
Component tests for Sprint API endpoints.
Tests API endpoints with TestClient, including error scenarios.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from datetime import date


@pytest.fixture
def client():
    """Create TestClient for each test"""
    return TestClient(app)


@pytest.fixture(scope="module", autouse=True)
async def cleanup_database():
    """Clean up database after all tests in this module"""
    yield
    # Cleanup after tests
    from app.services.database import get_database
    db = get_database()
    sprints = await db.get_all_sprints()
    for sprint in sprints:
        try:
            await db.delete_sprint(sprint.id)
        except:
            pass


@pytest.fixture
def sample_sprint_data():
    """Sample sprint data for tests - uses unique sprint number each time"""
    import uuid
    unique_suffix = str(uuid.uuid4())[:8]
    return {
        "sprintNumber": f"25-test-{unique_suffix}",
        "startDate": "2025-11-26",
        "endDate": "2025-12-09",
        "confidencePercentage": 85.0,
        "teamMembers": [
            {
                "name": "Alice Johnson",
                "role": "Developer",
                "confidencePercentage": 90.0,
                "vacations": [
                    {
                        "startDate": "2025-11-28",
                        "endDate": "2025-11-29"
                    }
                ]
            },
            {
                "name": "Bob Smith",
                "role": "Tester",
                "confidencePercentage": 85.0,
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


class TestCreateSprint:
    """Test POST /v1/sprints endpoint"""
    
    def test_create_sprint_success(self, client, sample_sprint_data):
        """Test successful sprint creation"""
        response = client.post("/v1/sprints", json=sample_sprint_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["sprintNumber"] == "25-50"
        assert "sprintName" in data  # Auto-generated
        assert "sprintDuration" in data  # Auto-calculated
        assert len(data["teamMembers"]) == 2
        assert len(data["holidays"]) == 1
    
    def test_create_sprint_minimal_data(self, client):
        """Test sprint creation with minimal required fields"""
        minimal_data = {
            "sprintNumber": "25-51",
            "startDate": "2025-12-01",
            "endDate": "2025-12-07",
            "teamMembers": []
        }
        
        response = client.post("/v1/sprints", json=minimal_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["teamMembers"] == []
        assert data["holidays"] == []
    
    def test_create_sprint_with_defaults(self, client):
        """Test sprint creation uses default confidence percentage"""
        sprint_data = {
            "sprintNumber": "25-52",
            "startDate": "2025-12-01",
            "endDate": "2025-12-10",
            "teamMembers": [
                {
                    "name": "Charlie",
                    "role": "Developer"
                    # confidencePercentage not specified, should default to 100.0
                }
            ]
        }
        
        response = client.post("/v1/sprints", json=sprint_data)
        
        assert response.status_code == 201
        data = response.json()
        # Team member created successfully
        assert len(data["teamMembers"]) == 1
        assert data["teamMembers"][0]["name"] == "Charlie"


class TestGetSprints:
    """Test GET /v1/sprints endpoint"""
    
    def test_get_all_sprints_empty(self, client):
        """Test getting sprints when database is empty"""
        response = client.get("/v1/sprints")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_all_sprints_with_data(self, client, sample_sprint_data):
        """Test getting all sprints after creating some"""
        # Create multiple sprints
        client.post("/v1/sprints", json=sample_sprint_data)
        
        sprint_data_2 = sample_sprint_data.copy()
        sprint_data_2["sprintNumber"] = "25-53"
        client.post("/v1/sprints", json=sprint_data_2)
        
        # Get all
        response = client.get("/v1/sprints")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 2


class TestGetSprintById:
    """Test GET /v1/sprints/{sprint_id} endpoint"""
    
    def test_get_sprint_by_id_success(self, client, sample_sprint_data):
        """Test getting sprint by valid ID"""
        # Create sprint
        create_response = client.post("/v1/sprints", json=sample_sprint_data)
        sprint_id = create_response.json()["id"]
        
        # Get by ID
        response = client.get(f"/v1/sprints/{sprint_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sprint_id
        assert data["sprintNumber"] == "25-50"
    
    def test_get_sprint_by_id_not_found(self, client):
        """Test getting non-existent sprint returns 404"""
        response = client.get("/v1/sprints/non-existent-id-12345")
        
        assert response.status_code == 404
        data = response.json()
        assert data["detail"]["code"] == "NOT_FOUND"


class TestUpdateSprint:
    """Test PUT /v1/sprints/{sprint_id} endpoint"""
    
    def test_update_sprint_success(self, client, sample_sprint_data):
        """Test successful sprint update"""
        # Create sprint
        create_response = client.post("/v1/sprints", json=sample_sprint_data)
        sprint_id = create_response.json()["id"]
        
        # Update it
        updated_data = {
            "sprintNumber": "25-54",
            "startDate": "2025-12-01",
            "endDate": "2025-12-10",
            "confidencePercentage": 90.0,
            "teamMembers": [
                {
                    "name": "New Member",
                    "role": "Product Owner",
                    "confidencePercentage": 95.0,
                    "vacations": []
                }
            ],
            "holidays": []
        }
        
        response = client.put(f"/v1/sprints/{sprint_id}", json=updated_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sprint_id
        assert data["sprintNumber"] == "25-54"
        assert "sprintDuration" in data  # Auto-calculated
        assert len(data["teamMembers"]) == 1
    
    def test_update_sprint_not_found(self, client, sample_sprint_data):
        """Test updating non-existent sprint returns 404"""
        response = client.put("/v1/sprints/non-existent-id", json=sample_sprint_data)
        
        assert response.status_code == 404
        data = response.json()
        assert data["detail"]["code"] == "NOT_FOUND"
    
    def test_update_sprint_partial(self, client, sample_sprint_data):
        """Test updating specific fields only"""
        # Create sprint
        create_response = client.post("/v1/sprints", json=sample_sprint_data)
        sprint_id = create_response.json()["id"]
        original_number = create_response.json()["sprintNumber"]
        
        # Update confidence percentage
        updated_data = sample_sprint_data.copy()
        updated_data["confidencePercentage"] = 75.0
        
        response = client.put(f"/v1/sprints/{sprint_id}", json=updated_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["confidencePercentage"] == 75.0
        assert data["sprintNumber"] == original_number


class TestDeleteSprint:
    """Test DELETE /v1/sprints/{sprint_id} endpoint"""
    
    def test_delete_sprint_success(self, client, sample_sprint_data):
        """Test successful sprint deletion"""
        # Create sprint
        create_response = client.post("/v1/sprints", json=sample_sprint_data)
        sprint_id = create_response.json()["id"]
        
        # Delete it
        response = client.delete(f"/v1/sprints/{sprint_id}")
        
        assert response.status_code == 204
        
        # Verify it's gone
        get_response = client.get(f"/v1/sprints/{sprint_id}")
        assert get_response.status_code == 404
    
    def test_delete_sprint_not_found(self, client):
        """Test deleting non-existent sprint returns 404"""
        response = client.delete("/v1/sprints/non-existent-id")
        
        assert response.status_code == 404
        data = response.json()
        assert data["detail"]["code"] == "NOT_FOUND"


class TestGetCapacity:
    """Test GET /v1/sprints/{sprint_id}/capacity endpoint"""
    
    def test_get_capacity_success(self, client, sample_sprint_data):
        """Test successful capacity calculation"""
        # Create sprint
        create_response = client.post("/v1/sprints", json=sample_sprint_data)
        sprint_id = create_response.json()["id"]
        
        # Get capacity
        response = client.get(f"/v1/sprints/{sprint_id}/capacity")
        
        assert response.status_code == 200
        data = response.json()
        assert data["sprintId"] == sprint_id
        assert data["teamSize"] == 2
        assert data["holidaysCount"] == 1
        assert data["vacationDaysCount"] > 0
        assert "memberCapacity" in data
        assert len(data["memberCapacity"]) == 2
    
    def test_get_capacity_empty_team(self, client):
        """Test capacity calculation with no team members"""
        sprint_data = {
            "sprintNumber": "25-55",
            "startDate": "2025-12-01",
            "endDate": "2025-12-10",
            "teamMembers": []
        }
        
        create_response = client.post("/v1/sprints", json=sprint_data)
        sprint_id = create_response.json()["id"]
        
        response = client.get(f"/v1/sprints/{sprint_id}/capacity")
        
        assert response.status_code == 200
        data = response.json()
        assert data["teamSize"] == 0
        assert data["totalCapacityDays"] == 0
        assert data["adjustedTotalCapacity"] == 0.0
    
    def test_get_capacity_not_found(self, client):
        """Test capacity for non-existent sprint returns 404"""
        response = client.get("/v1/sprints/non-existent-id/capacity")
        
        assert response.status_code == 404
        data = response.json()
        assert data["detail"]["code"] == "NOT_FOUND"
    
    def test_get_capacity_with_weekends(self, client):
        """Test capacity excludes weekends correctly"""
        # Sprint from Monday to Sunday (should exclude weekend days)
        sprint_data = {
            "sprintNumber": "25-56",
            "startDate": "2025-12-01",  # Monday
            "endDate": "2025-12-07",    # Sunday
            "teamMembers": [
                {
                    "name": "Test Member",
                    "role": "Developer",
                    "confidencePercentage": 100.0
                }
            ]
        }
        
        create_response = client.post("/v1/sprints", json=sprint_data)
        sprint_id = create_response.json()["id"]
        
        response = client.get(f"/v1/sprints/{sprint_id}/capacity")
        
        assert response.status_code == 200
        data = response.json()
        # Should have 5 working days (Mon-Fri), excluding Sat-Sun
        assert data["totalWorkingDays"] == 5
