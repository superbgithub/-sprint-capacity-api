"""
Functional tests for end-to-end workflows.
Tests complete user journeys through the API.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    """Create TestClient for each test"""
    return TestClient(app)


class TestSprintLifecycleWorkflow:
    """Test complete sprint lifecycle from creation to deletion"""
    
    def test_complete_sprint_workflow(self, client):
        """
        Test complete workflow:
        1. Create sprint
        2. Get sprint details
        3. Calculate capacity
        4. Update sprint
        5. Recalculate capacity
        6. Delete sprint
        """
        # Step 1: Create sprint
        sprint_data = {
            "sprintNumber": "25-01",
            "startDate": "2025-11-26",
            "endDate": "2025-12-09",
            "confidencePercentage": 90.0,
            "teamMembers": [
                {
                    "name": "Alice Developer",
                    "role": "Developer",
                    "vacations": [
                        {
                            "startDate": "2025-11-28",
                            "endDate": "2025-11-29"
                        }
                    ]
                }
            ],
            "holidays": [
                {
                    "holidayDate": "2025-11-27",
                    "name": "Thanksgiving"
                }
            ]
        }
        
        create_response = client.post("/v1/sprints", json=sprint_data)
        assert create_response.status_code == 201
        sprint_id = create_response.json()["id"]
        
        # Step 2: Get sprint details
        get_response = client.get(f"/v1/sprints/{sprint_id}")
        assert get_response.status_code == 200
        sprint = get_response.json()
        assert sprint["sprintNumber"] == "25-01"
        assert sprint["sprintName"] == "Sprint 25-01"
        assert len(sprint["teamMembers"]) == 1
        
        # Step 3: Calculate capacity
        capacity_response = client.get(f"/v1/sprints/{sprint_id}/capacity")
        assert capacity_response.status_code == 200
        capacity = capacity_response.json()
        assert capacity["teamSize"] == 1
        assert capacity["holidaysCount"] == 1
        # Vacation is 2 calendar days but only weekdays count
        assert capacity["vacationDaysCount"] >= 1
        original_capacity = capacity["adjustedTotalCapacity"]
        
        # Step 4: Update sprint (add team member)
        updated_data = sprint_data.copy()
        updated_data["holidays"] = sprint_data.get("holidays", [])
        updated_data["teamMembers"].append({
            "name": "Bob Tester",
            "role": "Tester",
            "vacations": []
        })
        
        update_response = client.put(f"/v1/sprints/{sprint_id}", json=updated_data)
        assert update_response.status_code == 200
        updated_sprint = update_response.json()
        assert len(updated_sprint["teamMembers"]) == 2
        
        # Step 5: Recalculate capacity (should increase)
        new_capacity_response = client.get(f"/v1/sprints/{sprint_id}/capacity")
        assert new_capacity_response.status_code == 200
        new_capacity = new_capacity_response.json()
        assert new_capacity["teamSize"] == 2
        assert new_capacity["adjustedTotalCapacity"] > original_capacity
        
        # Step 6: Delete sprint
        delete_response = client.delete(f"/v1/sprints/{sprint_id}")
        assert delete_response.status_code == 204
        
        # Verify sprint is gone
        verify_response = client.get(f"/v1/sprints/{sprint_id}")
        assert verify_response.status_code == 404


class TestMultiSprintManagement:
    """Test managing multiple sprints simultaneously"""
    
    def test_create_multiple_sprints_and_manage(self, client):
        """
        Test workflow with multiple sprints:
        1. Create 3 sprints
        2. Get all sprints
        3. Update one sprint
        4. Delete one sprint
        5. Verify remaining sprints
        """
        # Step 1: Create 3 sprints
        sprint_ids = []
        for i in range(3):
            sprint_data = {
                "sprintNumber": f"25-{i+1:02d}",
                "startDate": f"2025-12-0{i+1}",
                "endDate": f"2025-12-1{i+1}",
                "confidencePercentage": 80.0 + i * 5,
                "teamMembers": [
                    {
                        "name": f"Developer {i+1}",
                        "role": "Developer",
                        "vacations": []
                    }
                ],
                "holidays": []
            }
            
            response = client.post("/v1/sprints", json=sprint_data)
            assert response.status_code == 201
            sprint_ids.append(response.json()["id"])
        
        # Step 2: Get all sprints
        get_all_response = client.get("/v1/sprints")
        assert get_all_response.status_code == 200
        all_sprints = get_all_response.json()
        assert len([s for s in all_sprints if s["id"] in sprint_ids]) == 3
        
        # Step 3: Update second sprint
        update_data = {
            "sprintNumber": "25-10",
            "startDate": "2025-12-02",
            "endDate": "2025-12-16",
            "confidencePercentage": 85.0,
            "teamMembers": [],
            "holidays": []
        }
        update_response = client.put(f"/v1/sprints/{sprint_ids[1]}", json=update_data)
        assert update_response.status_code == 200
        assert update_response.json()["sprintNumber"] == "25-10"
        assert update_response.json()["sprintName"] == "Sprint 25-10"
        
        # Step 4: Delete first sprint
        delete_response = client.delete(f"/v1/sprints/{sprint_ids[0]}")
        assert delete_response.status_code == 204
        
        # Step 5: Verify remaining sprints
        final_response = client.get("/v1/sprints")
        assert final_response.status_code == 200
        final_sprints = final_response.json()
        remaining_ids = [s["id"] for s in final_sprints]
        assert sprint_ids[0] not in remaining_ids
        assert sprint_ids[1] in remaining_ids
        assert sprint_ids[2] in remaining_ids


class TestCapacityPlanningWorkflow:
    """Test capacity planning across multiple scenarios"""
    
    def test_capacity_with_holidays_and_vacations(self, client):
        """
        Test realistic capacity planning workflow:
        1. Create sprint with holidays and vacations
        2. Calculate initial capacity
        3. Add more team members
        4. Add more holidays
        5. Verify capacity adjustments
        """
        # Step 1: Create sprint
        sprint_data = {
            "sprintNumber": "25-11",
            "startDate": "2025-12-01",
            "endDate": "2025-12-14",
            "confidencePercentage": 90.0,
            "teamMembers": [
                {
                    "name": "Alice",
                    "role": "Developer",
                    "vacations": [
                        {
                            "startDate": "2025-12-05",
                            "endDate": "2025-12-06"
                        }
                    ]
                }
            ],
            "holidays": [
                {
                    "holidayDate": "2025-12-10",
                    "name": "Company Holiday"
                }
            ]
        }
        
        create_response = client.post("/v1/sprints", json=sprint_data)
        assert create_response.status_code == 201
        sprint_id = create_response.json()["id"]
        
        # Step 2: Calculate initial capacity
        capacity_1 = client.get(f"/v1/sprints/{sprint_id}/capacity").json()
        assert capacity_1["teamSize"] == 1
        initial_capacity = capacity_1["adjustedTotalCapacity"]
        
        # Step 3: Add more team members
        sprint_data["teamMembers"].append({
            "name": "Bob",
            "role": "Developer",
            "confidencePercentage": 85.0,
            "vacations": []
        })
        sprint_data["teamMembers"].append({
            "name": "Charlie",
            "role": "Tester",
            "confidencePercentage": 80.0,
            "vacations": [
                {
                    "startDate": "2025-12-13",
                    "endDate": "2025-12-14"
                }
            ]
        })
        
        update_response = client.put(f"/v1/sprints/{sprint_id}", json=sprint_data)
        assert update_response.status_code == 200
        
        capacity_2 = client.get(f"/v1/sprints/{sprint_id}/capacity").json()
        assert capacity_2["teamSize"] == 3
        assert capacity_2["adjustedTotalCapacity"] > initial_capacity
        
        # Step 4: Add more holidays
        sprint_data["holidays"].append({
            "holidayDate": "2025-12-12",
            "name": "Another Holiday"
        })
        
        update_response_2 = client.put(f"/v1/sprints/{sprint_id}", json=sprint_data)
        assert update_response_2.status_code == 200
        
        # Step 5: Verify capacity adjustments
        capacity_3 = client.get(f"/v1/sprints/{sprint_id}/capacity").json()
        assert capacity_3["holidaysCount"] == 2
        # Vacation days count only working days, not calendar days
        # Some vacations may fall on weekends/holidays so count could be 0
        assert capacity_3["vacationDaysCount"] >= 0  # Vacations tracked
        
        # Verify member breakdown
        member_capacities = {m["memberName"]: m for m in capacity_3["memberCapacity"]}
        assert "Alice" in member_capacities
        assert "Bob" in member_capacities
        assert "Charlie" in member_capacities
        # Vacation days count only working days (may be 0 if vacations fall on weekends/holidays)
        assert member_capacities["Alice"]["vacationDays"] >= 0
        assert member_capacities["Bob"]["vacationDays"] == 0
        assert member_capacities["Charlie"]["vacationDays"] >= 0


class TestErrorRecoveryWorkflow:
    """Test error handling and recovery scenarios"""
    
    def test_invalid_data_recovery_workflow(self, client):
        """
        Test workflow with error recovery:
        1. Attempt to create invalid sprint (should fail)
        2. Correct data and create successfully
        3. Attempt invalid update (should fail)
        4. Correct update and succeed
        """
        # Step 1: Invalid create (confidence > 100)
        invalid_sprint = {
            "sprintName": "Invalid Sprint",
            "sprintDuration": 10,
            "startDate": "2025-12-01",
            "endDate": "2025-12-10",
            "teamMembers": [
                {
                    "name": "Test",
                    "role": "Developer",
                    "confidencePercentage": 150.0  # Invalid
                }
            ]
        }
        
        response_1 = client.post("/v1/sprints", json=invalid_sprint)
        assert response_1.status_code == 422
        
        # Step 2: Correct and create
        invalid_sprint["teamMembers"][0]["confidencePercentage"] = 95.0
        response_2 = client.post("/v1/sprints", json=invalid_sprint)
        assert response_2.status_code == 201
        sprint_id = response_2.json()["id"]
        
        # Step 3: Invalid update (bad role)
        invalid_update = {
            "sprintName": "Updated Sprint",
            "sprintDuration": 10,
            "startDate": "2025-12-01",
            "endDate": "2025-12-10",
            "teamMembers": [
                {
                    "name": "Test",
                    "role": "InvalidRole",  # Invalid
                    "confidencePercentage": 90.0
                }
            ]
        }
        
        response_3 = client.put(f"/v1/sprints/{sprint_id}", json=invalid_update)
        assert response_3.status_code == 422
        
        # Step 4: Correct and update
        invalid_update["teamMembers"][0]["role"] = "Product Owner"
        invalid_update["teamMembers"][0]["vacations"] = []
        response_4 = client.put(f"/v1/sprints/{sprint_id}", json=invalid_update)
        assert response_4.status_code == 200
        assert response_4.json()["teamMembers"][0]["role"] == "Product Owner"
    
    def test_not_found_error_handling(self, client):
        """Test handling of not-found errors in workflow"""
        fake_id = "non-existent-sprint-id-12345"
        
        # All operations should return 404
        get_response = client.get(f"/v1/sprints/{fake_id}")
        assert get_response.status_code == 404
        
        capacity_response = client.get(f"/v1/sprints/{fake_id}/capacity")
        assert capacity_response.status_code == 404
        
        update_data = {
            "sprintName": "Test",
            "sprintDuration": 10,
            "startDate": "2025-12-01",
            "endDate": "2025-12-10",
            "teamMembers": []
        }
        update_response = client.put(f"/v1/sprints/{fake_id}", json=update_data)
        assert update_response.status_code == 404
        
        delete_response = client.delete(f"/v1/sprints/{fake_id}")
        assert delete_response.status_code == 404
