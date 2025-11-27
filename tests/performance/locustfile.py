"""
Performance tests using Locust for load testing.
Tests API performance under various load conditions.

To run these tests:
    locust -f tests/performance/locustfile.py --host=http://127.0.0.1:8000
    
Then open http://localhost:8089 to configure and start the load test.
"""
from locust import HttpUser, task, between, events
import json
import random


class SprintAPIUser(HttpUser):
    """Simulates a user interacting with the Sprint API"""
    
    # Wait between 1-3 seconds between tasks
    wait_time = between(1, 3)
    
    def on_start(self):
        """Initialize user session"""
        self.sprint_ids = []
        self.create_initial_sprints()
    
    def create_initial_sprints(self):
        """Create some initial sprints for testing"""
        for i in range(3):
            sprint_data = self._generate_sprint_data(f"Initial Sprint {i}")
            response = self.client.post("/v1/sprints", json=sprint_data)
            if response.status_code == 201:
                self.sprint_ids.append(response.json()["id"])
    
    def _generate_sprint_data(self, name_prefix="Sprint"):
        """Generate random sprint data"""
        team_size = random.randint(3, 10)
        team_members = [
            {
                "name": f"Member {i}",
                "role": random.choice(["Developer", "Tester", "Manager"]),
                "vacations": []
            }
            for i in range(team_size)
        ]
        
        # Randomly add vacations to some members
        for member in random.sample(team_members, k=min(3, len(team_members))):
            member["vacations"] = [
                {
                    "startDate": "2025-12-05",
                    "endDate": "2025-12-06"
                }
            ]
        
        holidays = [
            {
                "holidayDate": "2025-12-25",
                "name": "Christmas"
            }
        ]
        
        return {
            "sprintNumber": f"25-{random.randint(400, 999)}",
            "startDate": "2025-12-01",
            "endDate": "2025-12-20",
            "confidencePercentage": random.uniform(70.0, 100.0),
            "teamMembers": team_members,
            "holidays": holidays
        }
    
    @task(5)
    def get_all_sprints(self):
        """Get all sprints (high frequency task)"""
        with self.client.get("/v1/sprints", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Failed with status {response.status_code}")
    
    @task(3)
    def create_sprint(self):
        """Create a new sprint (medium frequency)"""
        sprint_data = self._generate_sprint_data("Load Test Sprint")
        
        with self.client.post("/v1/sprints", json=sprint_data, catch_response=True) as response:
            if response.status_code == 201:
                sprint_id = response.json()["id"]
                self.sprint_ids.append(sprint_id)
                response.success()
            else:
                response.failure(f"Failed to create sprint: {response.status_code}")
    
    @task(4)
    def get_sprint_by_id(self):
        """Get a specific sprint by ID (high frequency)"""
        if not self.sprint_ids:
            return
        
        sprint_id = random.choice(self.sprint_ids)
        
        with self.client.get(f"/v1/sprints/{sprint_id}", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 404:
                # Sprint was deleted, remove from list
                self.sprint_ids.remove(sprint_id)
                response.success()
            else:
                response.failure(f"Failed with status {response.status_code}")
    
    @task(6)
    def get_capacity(self):
        """Calculate sprint capacity (highest frequency - most resource intensive)"""
        if not self.sprint_ids:
            return
        
        sprint_id = random.choice(self.sprint_ids)
        
        with self.client.get(f"/v1/sprints/{sprint_id}/capacity", catch_response=True) as response:
            if response.status_code == 200:
                # Validate response structure
                data = response.json()
                if all(key in data for key in ["sprintId", "totalCapacityDays", "memberCapacity"]):
                    response.success()
                else:
                    response.failure("Invalid capacity response structure")
            elif response.status_code == 404:
                self.sprint_ids.remove(sprint_id)
                response.success()
            else:
                response.failure(f"Failed with status {response.status_code}")
    
    @task(2)
    def update_sprint(self):
        """Update an existing sprint (medium frequency)"""
        if not self.sprint_ids:
            return
        
        sprint_id = random.choice(self.sprint_ids)
        updated_data = self._generate_sprint_data("Updated Sprint")
        
        with self.client.put(f"/v1/sprints/{sprint_id}", json=updated_data, catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 404:
                self.sprint_ids.remove(sprint_id)
                response.success()
            else:
                response.failure(f"Failed to update sprint: {response.status_code}")
    
    @task(1)
    def delete_sprint(self):
        """Delete a sprint (low frequency)"""
        if not self.sprint_ids or len(self.sprint_ids) < 5:
            # Keep at least some sprints around
            return
        
        sprint_id = random.choice(self.sprint_ids)
        
        with self.client.delete(f"/v1/sprints/{sprint_id}", catch_response=True) as response:
            if response.status_code == 204:
                self.sprint_ids.remove(sprint_id)
                response.success()
            elif response.status_code == 404:
                self.sprint_ids.remove(sprint_id)
                response.success()
            else:
                response.failure(f"Failed to delete sprint: {response.status_code}")


class CapacityHeavyUser(HttpUser):
    """Simulates a user focused on capacity calculations"""
    
    wait_time = between(0.5, 2)
    
    def on_start(self):
        """Create sprints with complex capacity scenarios"""
        self.sprint_ids = []
        
        for i in range(5):
            # Create sprints with many team members for complex calculations
            sprint_data = {
                "sprintNumber": f"25-{500+i}",
                "startDate": "2025-12-01",
                "endDate": "2025-12-14",
                "confidencePercentage": random.uniform(75.0, 95.0),
                "teamMembers": [
                    {
                        "name": f"Member {j}",
                        "role": random.choice(["Developer", "Tester", "Manager"]),
                        "vacations": [
                            {
                                "startDate": "2025-12-05",
                                "endDate": "2025-12-06"
                            }
                        ] if j % 2 == 0 else []
                    }
                    for j in range(20)  # 20 team members for complex calculation
                ],
                "holidays": [
                    {"holidayDate": "2025-12-10", "name": "Holiday 1"},
                    {"holidayDate": "2025-12-11", "name": "Holiday 2"}
                ]
            }
            
            response = self.client.post("/v1/sprints", json=sprint_data)
            if response.status_code == 201:
                self.sprint_ids.append(response.json()["id"])
    
    @task(10)
    def calculate_capacity_repeatedly(self):
        """Repeatedly calculate capacity for stress testing"""
        if not self.sprint_ids:
            return
        
        sprint_id = random.choice(self.sprint_ids)
        
        with self.client.get(f"/v1/sprints/{sprint_id}/capacity", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Failed with status {response.status_code}")


# Performance metrics tracking
@events.request.add_listener
def on_request(request_type, name, response_time, response_length, exception, **kwargs):
    """Track request metrics"""
    if exception:
        print(f"Request failed: {name} - {exception}")


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Initialize test metrics"""
    print("Performance test starting...")
    print(f"Host: {environment.host}")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Print final statistics"""
    print("\nPerformance test completed!")
    print(f"Total requests: {environment.stats.total.num_requests}")
    print(f"Total failures: {environment.stats.total.num_failures}")
    print(f"Average response time: {environment.stats.total.avg_response_time:.2f}ms")
    print(f"Max response time: {environment.stats.total.max_response_time:.2f}ms")
    print(f"Requests per second: {environment.stats.total.total_rps:.2f}")
